# MD2DB 高性能并行解析系统设计文档

**日期:** 2026-02-05
**目标:** 支持百万行 (50-200MB) Markdown 文件的高性能解析，使用 MongoDB 存储

---

## 一、需求概述

| 需求 | 具体内容 |
|------|---------|
| 文件规模 | 50-200 MB（约50万-200万行） |
| 性能目标 | 处理速度优先 |
| 输出方式 | 流式写入 MongoDB |
| 并行策略 | 多进程 (ProcessPool) |

---

## 二、MongoDB 数据结构设计

### 2.1 集合结构

```javascript
// 1. questions 集合 - 主问题数据
{
  "_id": ObjectId("..."),
  "content": "What is 2+2?",
  "question_type": "multiple_choice",  // multiple_choice, true_false, fill_in_blank, subjective
  "options": [ObjectId("...")],        // 引用 options 集合
  "answer": "B",
  "explanation": "2+2 equals 4",
  "images": [ObjectId("...")],         // 引用 images 集合
  "latex_formulas": [ObjectId("...")], // 引用 latex 集合
  "created_at": ISODate("...")
}

// 2. options 集合 - 选项数据（去重）
{
  "_id": ObjectId("..."),
  "label": "A",                       // 选项标签 A, B, C, D...
  "content": "3",                     // 选项内容
  "hash": "sha256:..."                // 内容哈希，用于去重
}

// 3. images 集合 - 图片信息
{
  "_id": ObjectId("..."),
  "url": "http://example.com/image.png",
  "alt": "diagram",
  "hash": "sha256:..."                // URL 哈希，用于去重
}

// 4. latex_formulas 集合 - LaTeX 公式
{
  "_id": ObjectId("..."),
  "formula": "\\frac{a}{b}",
  "hash": "sha256:..."                # 公式哈希，用于去重
}
```

### 2.2 索引设计

```javascript
// questions 集合
db.questions.createIndex({ "question_type": 1 })
db.questions.createIndex({ "created_at": -1 })

// options 集合
db.options.createIndex({ "hash": 1 }, { unique: true })

// images 集合
db.images.createIndex({ "hash": 1 }, { unique: true })

// latex_formulas 集合
db.latex_formulas.createIndex({ "hash": 1 }, { unique: true })
```

---

## 三、多进程并行处理架构

### 3.1 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    主进程 (Main Process)                     │
│  - 读取文件并分块                                            │
│  - 检测题目边界                                              │
│  - 分配任务给工作进程                                        │
│  - 协调 MongoDB 写入                                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  Worker 1    │      │  Worker 2    │      │  Worker N    │
│  解析块 1    │      │  解析块 2    │      │  解析块 N    │
│  → 问题对象  │      │  → 问题对象  │      │  → 问题对象  │
└──────────────┘      └──────────────┘      └──────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  MongoDB 批量写入 │
                    │  (去重 + 关联)   │
                    └──────────────────┘
```

### 3.2 核心组件

| 组件 | 职责 |
|------|------|
| FileChunker | 将大文件分割成块，确保不在题目中间分割 |
| ProcessPool | 使用 `multiprocessing.Pool` 并行解析 |
| ResultCollector | 收集解析结果并批量写入 MongoDB |
| Deduplicator | 对 options、images、latex 进行去重 |

---

## 四、流式写入与去重策略

### 4.1 双缓冲流式写入

```python
# 伪代码流程
def stream_to_mongodb(worker_results):
    buffer_a = []  # 缓冲区 A
    buffer_b = []  # 缓冲区 B
    current_buffer = buffer_a
    writing_buffer = None

    for result in worker_results:
        current_buffer.append(result)

        # 缓冲区满时，切换并异步写入
        if len(current_buffer) >= BATCH_SIZE:
            writing_buffer = current_buffer
            current_buffer = buffer_b if current_buffer == buffer_a else buffer_b
            async_write(writing_buffer)  # 非阻塞写入

    # 写入剩余数据
    async_write(current_buffer)
```

### 4.2 去重策略

使用内容哈希避免重复存储：

```python
# options 去重示例
option_hash = sha256(content).hexdigest()
existing = db.options.find_one({"hash": option_hash})
if existing:
    question.options.append(existing["_id"])  # 引用已存在的选项
else:
    new_option = {"label": "A", "content": "...", "hash": option_hash}
    option_id = db.options.insert_one(new_option).inserted_id
    question.options.append(option_id)
```

### 4.3 批量写入配置

| 配置项 | 值 |
|--------|-----|
| BATCH_SIZE | 1000 (每批1000个问题) |
| 写入方式 | `bulk_write()` / `insert_many()` |
| ordered | False (允许部分失败) |

---

## 五、问题边界处理

### 5.1 两阶段分割

```python
# 阶段1：粗略分割（按字节数）
raw_chunks = [
    (0, 10MB),
    (10MB, 20MB),
    (20MB, 30MB),
    ...
]

# 阶段2：调整边界到题目分隔符
def adjust_boundaries(file_path, raw_chunks):
    with open(file_path, 'r') as f:
        adjusted_chunks = []
        for start, end in raw_chunks:
            f.seek(end)
            # 向后搜索直到找到题目分隔符
            while True:
                line = f.readline()
                if re.match(r'^\d+\.\s+', line) or line == '':
                    end = f.tell()
                    break
            adjusted_chunks.append((start, end))
        return adjusted_chunks
```

### 5.2 题目分隔符模式

```python
QUESTION_SEPARATORS = [
    r'^\d+\.\s+',           # 1. 2. 3.
    r'^\s*---\s*$',         # ---
    r'^\s*\*\*\*\s*$',      # ***
    r'^\n\s*\n\s*\n+',      # 多个空行
]
```

---

## 六、错误恢复机制

### 6.1 进度跟踪

- 每个工作进程记录进度到 Redis/文件
- 主进程定期检查，失败的块重新分配

### 6.2 容错写入

- MongoDB 使用 `insert_many()` 的 `ordered=False`
- 部分失败不影响其他插入
- 失败的记录记录到错误日志

---

## 七、技术栈总结

| 组件 | 技术选型 |
|------|---------|
| 并行处理 | `multiprocessing.Pool` |
| 数据库 | MongoDB (4集合关联) |
| 写入策略 | 双缓冲 + 批量写入 |
| 去重 | SHA256 内容哈希 |
| 边界处理 | 两阶段分割 |

---

## 八、文件结构

```
src/md2db/
├── __init__.py
├── models.py              # 现有数据模型
├── parser.py              # 现有解析器
├── image_processor.py     # 现有图像处理
├── api.py                 # 现有 API
├── database.py            # 现有数据库导出
├── main.py                # 现有 CLI
├── parallel/              # 新增：并行处理模块
│   ├── __init__.py
│   ├── chunker.py         # 文件分块
│   ├── worker.py          # 工作进程
│   ├── coordinator.py     # 协调器
│   └── progress.py        # 进度跟踪
└── mongodb/               # 新增：MongoDB 模块
    ├── __init__.py
    ├── models.py          # MongoDB 模型
    ├── client.py          # MongoDB 客户端
    ├── deduplicator.py    # 去重器
    └── writer.py          # 批量写入器
```

---

## 九、实施步骤概要

1. **Phase 1: MongoDB 基础设施**
   - 安装 MongoDB 驱动
   - 创建 MongoDB 模型和客户端
   - 实现去重器

2. **Phase 2: 文件分块**
   - 实现 FileChunker
   - 实现两阶段边界检测

3. **Phase 3: 并行处理**
   - 实现工作进程
   - 实现协调器
   - 实现进度跟踪

4. **Phase 4: 流式写入**
   - 实现双缓冲写入器
   - 集成去重和批量写入

5. **Phase 5: 集成测试**
   - 端到端测试
   - 性能基准测试
