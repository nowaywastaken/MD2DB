# MD2DB Rust 重写架构设计

**日期**: 2026-02-05
**状态**: 设计阶段
**目标**: 将现有 Python MD2DB 渐进式迁移到 Rust

## 1. 项目背景与目标

### 1.1 核心目标

MD2DB Rust 重写项目旨在将现有的 Python 实现迁移到 Rust 生态系统，利用 Rust 的零成本抽象、内存安全保证和原生 ARM64 支持，在 Apple Silicon 和跨平台环境中获得显著的性能提升。

**核心目标**：
- 建立独立的 Rust 项目，与现有 Python 版本并行开发
- 完整迁移所有功能模块（解析、多媒体处理、API、数据库）
- 最终通过 Docker 部署，提供单一可执行容器的生产级服务
- 确保跨平台一致性（Windows NTFS/macOS APFS）

**渐进策略**：不采用 PyO3 或微服务混合架构，而是建立独立的 Rust 实现，便于独立测试和验证。

### 1.2 部署场景

- **使用规模**: 单客户机 + 单用户
- **文件大小**: 中型文件（10-100MB）
- **部署要求**: 越简单越好，单一 Docker 容器

## 2. 核心架构设计

MD2DB Rust 版本采用分层架构，从上到下分为 API 层、业务逻辑层、解析引擎层和存储抽象层。

### 2.1 架构分层

**API 层**: 使用 Axum 0.7+ 框架，提供 REST 端点接收 Markdown 文件或 ZIP 包。Axum 基于 Tokio 异步运行时，能够高效处理并发请求。

**业务逻辑层**: 包含题目模型定义和业务规则。`Question` 结构体使用 `serde` 进行序列化，支持选择题、判断题、填空题、主观题四种类型。

**解析引擎层**: 核心组件，使用 `pulldown-cmark` 0.11+ 解析器将 Markdown 转换为事件流。基于 AST 事件流处理，能更准确地处理嵌套结构和边缘情况。

**存储抽象层**: 使用 `sqlx` 0.7+ 提供编译时 SQL 检查，支持 PostgreSQL（主）和 MongoDB（可选）。

### 2.2 单机多核架构

针对单客户机部署场景，采用单机多核并行架构：

```rust
pub struct SingleMachineProcessor {
    repo: Arc<dyn QuestionRepository>,
    workers: usize, // 根据 CPU 核心数自动设置
}
```

**优势**：
- 去掉分布式组件的复杂性
- 充分利用单机多核 CPU
- 优化内存使用（处理 100MB 文件不爆内存）
- 部署简单：单一 Docker 容器

## 3. 数据模型设计

### 3.1 核心数据结构

```rust
pub enum QuestionType {
    Choice,           // 单选题
    MultipleChoice,   // 多选题
    TrueFalse,        // 判断题
    FillInTheBlank,   // 填空题
    Subjective,       // 主观题
}

pub struct Question {
    pub id: Uuid,
    pub qtype: QuestionType,
    pub stem: String,
    pub options: Vec<QuestionOption>,
    pub answer: Option<String>,
    pub analysis: Option<String>,
    pub images: Vec<ImageRef>,
    pub latex: Vec<String>,
    pub created_at: DateTime<Utc>,
}

pub struct QuestionOption {
    pub content: String,
    pub sort_order: i32,
    pub is_correct: bool,
}

pub enum ImageRef {
    Remote(Url),
    Local { hash: String, original_path: String },
}
```

### 3.2 设计考量

- `answer` 和 `analysis` 使用 `Option<String>`，因为某些题型可能没有标准答案
- `QuestionType` 使用 enum 确保类型安全
- `ImageRef` 使用 enum 区分在线图片和本地图片
- 所有时间戳使用 `chrono::DateTime<Utc>` 确保跨平台时区一致性

## 4. Markdown 解析引擎设计

### 4.1 多层级题型分类架构

解析引擎采用四层分类策略，从快速模式匹配到深度语义分析，逐层提升准确性。

**第1层：结构模式匹配（快速通道）**
- 显式标记检测：`[单选]`、`[多选]` 等
- 判断题特征：选项恰好2个且为二值对
- 多选题特征：检测关键词

**第2层：上下文语义规则（中等复杂度）**
- 填空 vs 判断的区分：`()` + 二值选项 = 判断题
- 关键词语义检测：`"全部"`、`"都"` 暗示多选

**第3层：结构化 NLP 分析（深度分类）**
- 使用 `rust-bert` 或 `candle` 集成轻量级文本分类模型
- 特征提取：题干长度、选项数量、关键词标记、标点模式

**第4层：人工确认（可选兜底）**
- API 返回置信度分数
- 低置信度题目标记为需人工复核

### 4.2 决策流程

```
开始 → 结构模式匹配 → 成功？→ 是 → 返回结果
              ↓ 否
        语义规则匹配 → 成功？→ 是 → 返回结果
              ↓ 否
        NLP 分类 → 返回结果 + 置信度
```

### 4.3 AST 事件流处理

使用 `pulldown-cmark` 的事件驱动架构：

1. **题目边界检测**：`Start(Tag::Heading(1..=3))` 触发新题目
2. **题干收集**：`Event::Text` 和 `Event::Paragraph` 内容追加
3. **选项识别**：`Start(Tag::List)` 和 `Event::Item` 触发选项收集
4. **LaTeX 处理**：`Event::Code` 检测 `$...$` 或 `$$...$$` 定界符
5. **图片提取**：`Event::Start(Tag::Image)` 触发图片 URL 提取

## 5. 多媒体处理流水线

### 5.1 异步 ZIP 解压

```rust
pub async fn extract_zip(zip_path: &Path) -> Result<Vec<ParsedQuestion>> {
    let reader = File::open(zip_path).await?;
    let zip = async_zip::base::read::seek::ZipFileReader::new(reader).await?;

    // 并行任务：发现 .md 文件 + 提取 images/
    let (md_files, images) = tokio::join!(
        find_markdown_files(&zip),
        extract_images(&zip)
    );

    // 流式处理每个 Markdown 文件
    let results = stream::iter(md_files)
        .map(|file| parse_markdown_file(file))
        .buffer_unordered(4) // 并发处理 4 个文件
        .collect::<Vec<_>>()
        .await;

    Ok(results)
}
```

### 5.2 内容定址存储（CAS）

本地图片使用 SHA-256 哈希重命名，实现去重和不可变引用：

```rust
pub async fn process_image(img_data: &[u8]) -> ImageRef {
    let hash = sha256(img_data);
    let ext = detect_extension(img_data);
    let filename = format!("{}.{}", hash, ext);

    // 检查是否已存在（去重）
    if !file_exists(&filename).await {
        save_cas_image(&filename, img_data).await;
    }

    ImageRef::Local { hash, original_path: filename }
}
```

### 5.3 跨平台路径处理

使用 `std::path::Path` 抹平 Windows/macOS 差异：

```rust
pub fn normalize_path(path: &Path) -> PathBuf {
    // 统一使用 / 分隔符，处理 Windows UNC 路径
    let components: Vec<_> = path.components()
        .filter(|c| *c != Component::CurDir)
        .collect();
    PathBuf::from(components.iter().join("/"))
}
```

### 5.4 临时文件管理

使用 `tempfile` 库确保跨平台安全清理：

```rust
pub struct TempZipGuard {
    path: PathBuf,
}

impl Drop for TempZipGuard {
    fn drop(&mut self) {
        // 显式释放文件句柄后再删除
        let _ = std::fs::remove_file(&self.path);
    }
}
```

## 6. 数据库持久化层

### 6.1 数据库选型

**方案 B（已选择）**: PostgreSQL 为核心，MongoDB 作为可选性能优化

- **PostgreSQL（核心）**: 通用关系型数据库，支持 JSONB 处理动态选项
- **MongoDB（可选）**: 大规模导入场景的高性能后端
- **统一接口**: 通过 `QuestionRepository` trait 保持接口一致

### 6.2 Trait 抽象

```rust
#[async_trait]
pub trait QuestionRepository: Send + Sync {
    async fn save_batch(&self, questions: &[Question]) -> Result<Vec<Uuid>>;
    async fn find_by_id(&self, id: Uuid) -> Result<Option<Question>>;
    async fn find_by_type(&self, qtype: QuestionType) -> Result<Vec<Question>>;
}
```

### 6.3 PostgreSQL 实现（SQLx）

使用编译时检查的查询，结合 JSONB 处理动态选项：

```rust
pub struct PostgresRepository {
    pool: PgPool,
}

impl PostgresRepository {
    pub async fn save_batch(&self, questions: &[Question]) -> Result<Vec<Uuid>> {
        // 开启事务，批量插入
        let mut tx = self.pool.begin().await?;

        for q in questions {
            let id = sqlx::query!(
                r#"
                INSERT INTO questions (id, type, stem, answer, analysis, options, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (id) DO UPDATE SET
                    stem = EXCLUDED.stem,
                    options = EXCLUDED.options
                "#,
                q.id, q.qtype, q.stem, q.answer, q.analysis,
                Json(&q.options) as _, q.created_at
            )
            .execute(&mut *tx)
            .await?;
        }

        tx.commit().await?;
        Ok(questions.iter().map(|q| q.id).collect())
    }
}
```

### 6.4 MongoDB 实现（可选）

使用 `mongodb` 2.x+ 驱动，利用文档模型存储嵌套选项。

### 6.5 聚合写入优化

```rust
pub struct BatchWriter {
    buffer: Vec<Question>,
    threshold: usize, // 触发批量写入的阈值
}

impl BatchWriter {
    pub async fn push(&mut self, q: Question) -> Result<()> {
        self.buffer.push(q);
        if self.buffer.len() >= self.threshold {
            self.flush().await?;
        }
        Ok(())
    }

    pub async fn flush(&mut self) -> Result<()> {
        if !self.buffer.is_empty() {
            self.repo.save_batch(&self.buffer).await?;
            self.buffer.clear();
        }
        Ok(())
    }
}
```

## 7. API 层设计

### 7.1 核心端点

```rust
pub fn create_router() -> Router {
    Router::new()
        .route("/parse", post(parse_markdown))
        .route("/parse-zip", post(parse_zip))
        .route("/health", get(health_check))
        .route("/metrics", get(metrics))
        .layer(TraceLayer::new_for_http())
        .layer(CompressionLayer::new())
}
```

### 7.2 单文件解析端点

```rust
pub async fn parse_markdown(
    Json(req): Json<ParseRequest>,
    State(repo): State<Arc<dyn QuestionRepository>>,
) -> Result<Json<ParseResponse>, ApiError> {
    let questions = Parser::new().parse(&req.markdown)?;
    let ids = repo.save_batch(&questions).await?;

    Ok(Json(ParseResponse {
        count: ids.len(),
        question_ids: ids,
        questions,
    }))
}
```

### 7.3 错误处理

使用 `thiserror` 定义结构化错误：

```rust
#[derive(Error, Debug)]
pub enum ApiError {
    #[error("Parse error: {0}")]
    ParseError(String),

    #[error("Database error: {0}")]
    DatabaseError(#[from] sqlx::Error),

    #[error("Invalid file format")]
    InvalidFormat,
}
```

## 8. 单机多核并行处理

### 8.1 核心处理器

```rust
impl SingleMachineProcessor {
    pub fn new(repo: Arc<dyn QuestionRepository>) -> Self {
        // 自动检测 CPU 核心数
        let workers = std::thread::available_parallelism()
            .map(|n| n.get())
            .unwrap_or(4);

        Self { repo, workers }
    }

    pub async fn process_zip(&self, zip_data: Vec<u8>) -> Result<ProcessResult> {
        // 1. 流式解压（不占用大量内存）
        let entries = extract_zip_stream(&zip_data[..])?;

        // 2. 按文件分割任务
        let tasks: Vec<_> = entries.into_iter()
            .map(|entry| (self.repo.clone(), entry))
            .collect();

        // 3. 并行处理（利用多核）
        let questions = stream::iter(tasks)
            .map(|(repo, entry)| async move {
                parse_single_file(repo, entry).await
            })
            .buffer_unordered(self.workers) // 并发数 = CPU 核心数
            .collect::<Vec<_>>()
            .await;

        // 4. 批量写入数据库
        let all_questions: Vec<_> = questions.into_iter()
            .filter_map(|r| r.ok())
            .flatten()
            .collect();

        self.repo.save_batch(&all_questions).await?;

        Ok(ProcessResult {
            count: all_questions.len(),
        })
    }
}
```

### 8.2 内存优化策略

```rust
// 使用流式处理，避免一次性加载整个 ZIP
pub fn extract_zip_stream(zip_data: &[u8]) -> impl Stream<Item = ZipEntry> {
    async_stream::stream! {
        let cursor = std::io::Cursor::new(zip_data);
        let mut zip = zip::ZipArchive::new(cursor)?;

        for i in 0..zip.len() {
            let mut file = zip.by_index(i)?;
            let mut buffer = Vec::new();
            file.read_to_end(&mut buffer)?;
            yield ZipEntry::from_reader(&mut file, buffer);
        }
    }
}
```

## 9. 跨平台兼容性

### 9.1 路径处理

```rust
// ✅ 正确：使用 PathBuf，自动处理分隔符
pub fn join_images_dir(base: &Path, filename: &str) -> PathBuf {
    base.join("images").join(filename)  // macOS 用 /，Windows 用 \
}
```

### 9.2 文件编码

```rust
use encoding_rs::UTF_8;

pub fn read_markdown_with_fallback(path: &Path) -> Result<String> {
    let content = std::fs::read(path)?;

    // 尝试 UTF-8
    if let Ok(text) = std::str::from_utf8(&content) {
        return Ok(text.to_string());
    }

    // 回退到 GBK（Windows 中文常见）
    let (text, _, _) = encoding_rs::GBK.decode(&content);
    Ok(text.to_string())
}
```

### 9.3 条件编译

```rust
#[cfg(target_os = "windows")]
pub fn temp_dir() -> PathBuf {
    std::env::temp_dir()
}

#[cfg(target_os = "macos")]
pub fn temp_dir() -> PathBuf {
    PathBuf::from("/tmp")
}
```

## 10. 测试策略

### 10.1 单元测试

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_choice_detection() {
        let markdown = "题目\nA. 选项1\nB. 选项2";
        let q = Parser::new().parse(markdown).unwrap();
        assert_eq!(q.qtype, QuestionType::Choice);
    }
}
```

### 10.2 集成测试

```rust
// tests/integration_test.rs
#[tokio::test]
async fn test_full_pipeline() {
    let repo = create_test_repo().await;
    let processor = SingleMachineProcessor::new(repo);

    let zip = create_test_zip();
    let result = processor.process_zip(zip).await.unwrap();

    assert!(result.count > 0);
}
```

### 10.3 性能基准测试

```rust
use criterion::{black_box, criterion_group, criterion_main, Criterion};

fn bench_parsing(c: &mut Criterion) {
    c.bench_function("parse_100_questions", |b| {
        b.iter(|| Parser::new().parse(black_box(LARGE_MARKDOWN)))
    });
}
```

## 11. Docker 部署

```dockerfile
FROM rust:1.83 as builder
WORKDIR /app
COPY . .
RUN cargo build --release

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y ca-certificates
COPY --from=builder /app/target/release/md2db /usr/local/bin/
EXPOSE 8080
CMD ["md2db", "--config", "/config/config.toml"]
```

## 12. 核心依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| axum | 0.7+ | Web 框架 |
| tokio | 1.35+ | 异步运行时 |
| sqlx | 0.7+ | 数据库（PostgreSQL） |
| mongodb | 2.x+ | 数据库（MongoDB 可选） |
| pulldown-cmark | 0.11+ | Markdown 解析 |
| serde | 1.0+ | 序列化 |
| chrono | 0.4+ | 时间处理 |
| thiserror | 1.0+ | 错误处理 |
| rayon | 1.8+ | 并行处理 |
| tempfile | 3.8+ | 临时文件 |
| encoding_rs | 0.8+ | 编码检测 |

## 13. 实施计划

1. **阶段 1**: 项目脚手架 + 核心数据模型
2. **阶段 2**: Markdown 解析引擎（多层级分类）
3. **阶段 3**: 多媒体处理流水线
4. **阶段 4**: 数据库持久化层（PostgreSQL）
5. **阶段 5**: API 层
6. **阶段 6**: 单机多核优化
7. **阶段 7**: 跨平台适配
8. **阶段 8**: 测试和 Docker 部署

## 14. 成功标准

- ✅ 功能对等：与 Python 版本功能一致
- ✅ 性能提升：解析速度提升 1.5-2x
- ✅ 内存优化：处理 100MB 文件不爆内存
- ✅ 跨平台：Windows/macOS 无差异运行
- ✅ 部署简单：单一 Docker 容器
