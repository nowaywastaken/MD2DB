//! Database layer for persisting questions
//!
//! This module provides repository abstraction for different database backends.

use crate::models::Question;
use async_trait::async_trait;
use uuid::Uuid;

/// Trait for question repository operations
#[async_trait]
pub trait QuestionRepository: Send + Sync {
    /// Save a batch of questions to the database
    async fn save_batch(&self, questions: &[Question]) -> anyhow::Result<Vec<Uuid>>;

    /// Find a question by its ID
    async fn find_by_id(&self, id: Uuid) -> anyhow::Result<Option<Question>>;

    /// Find all questions of a specific type
    async fn find_by_type(&self, qtype: &crate::models::QuestionType) -> anyhow::Result<Vec<Question>>;
}

/// PostgreSQL implementation using SQLx
#[cfg(feature = "postgres")]
pub mod postgres {
    use super::*;
    use sqlx::{PgPool, Row};

    pub struct PostgresRepository {
        pool: PgPool,
    }

    impl PostgresRepository {
        /// Create a new PostgreSQL repository
        pub async fn new(database_url: &str) -> anyhow::Result<Self> {
            let pool = PgPool::connect(database_url).await?;
            Ok(Self { pool })
        }

        /// Create repository from existing connection pool
        pub fn with_pool(pool: PgPool) -> Self {
            Self { pool }
        }
    }

    #[async_trait]
    impl QuestionRepository for PostgresRepository {
        async fn save_batch(&self, questions: &[Question]) -> anyhow::Result<Vec<Uuid>> {
            let mut tx = self.pool.begin().await?;

            for q in questions {
                let qtype_str = serde_json::to_string(&q.qtype)?;
                let options_json = serde_json::to_string(&q.options)?;
                let latex_json = serde_json::to_string(&q.latex)?;

                sqlx::query(
                    r#"
                    INSERT INTO questions (id, type, stem, answer, analysis, options, latex, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (id) DO UPDATE SET
                        stem = EXCLUDED.stem,
                        answer = EXCLUDED.answer,
                        analysis = EXCLUDED.analysis,
                        options = EXCLUDED.options
                    "#
                )
                .bind(q.id)
                .bind(&qtype_str)
                .bind(&q.stem)
                .bind(&q.answer)
                .bind(&q.analysis)
                .bind(&options_json)
                .bind(&latex_json)
                .bind(q.created_at)
                .execute(&mut *tx)
                .await?;
            }

            tx.commit().await?;

            Ok(questions.iter().map(|q| q.id).collect())
        }

        async fn find_by_id(&self, id: Uuid) -> anyhow::Result<Option<Question>> {
            let row = sqlx::query("SELECT id, type, stem, answer, analysis, options, latex, created_at FROM questions WHERE id = $1")
                .bind(id)
                .fetch_optional(&self.pool)
                .await?;

            match row {
                Some(row) => {
                    let qtype: crate::models::QuestionType = serde_json::from_str(row.try_get("type")?)?;
                    let options: Vec<crate::models::QuestionOption> = serde_json::from_str(row.try_get("options")?)?;
                    let latex: Vec<String> = serde_json::from_str(row.try_get("latex")?)?;

                    Ok(Some(Question {
                        id: row.try_get("id")?,
                        qtype,
                        stem: row.try_get("stem")?,
                        options,
                        answer: row.try_get("answer")?,
                        analysis: row.try_get("analysis")?,
                        latex,
                        images: Vec::new(), // TODO: Handle image references
                        created_at: row.try_get("created_at")?,
                    }))
                }
                None => Ok(None),
            }
        }

        async fn find_by_type(
            &self,
            qtype: &crate::models::QuestionType,
        ) -> anyhow::Result<Vec<Question>> {
            let qtype_str = serde_json::to_string(qtype)?;
            let rows = sqlx::query("SELECT id, type, stem, answer, analysis, options, latex, created_at FROM questions WHERE type = $1")
                .bind(&qtype_str)
                .fetch_all(&self.pool)
                .await?;

            rows.into_iter()
                .map(|row| {
                    let qtype: crate::models::QuestionType = serde_json::from_str(row.try_get("type")?)?;
                    let options: Vec<crate::models::QuestionOption> = serde_json::from_str(row.try_get("options")?)?;
                    let latex: Vec<String> = serde_json::from_str(row.try_get("latex")?)?;

                    Ok(Question {
                        id: row.try_get("id")?,
                        qtype,
                        stem: row.try_get("stem")?,
                        options,
                        answer: row.try_get("answer")?,
                        analysis: row.try_get("analysis")?,
                        latex,
                        images: Vec::new(),
                        created_at: row.try_get("created_at")?,
                    })
                })
                .collect()
        }
    }
}

/// Mock repository for testing
pub struct MockRepository {
    questions: std::sync::Arc<tokio::sync::RwLock<Vec<Question>>>,
}

impl MockRepository {
    pub fn new() -> Self {
        Self {
            questions: std::sync::Arc::new(tokio::sync::RwLock::new(Vec::new())),
        }
    }
}

impl Default for MockRepository {
    fn default() -> Self {
        Self::new()
    }
}

#[async_trait]
impl QuestionRepository for MockRepository {
    async fn save_batch(&self, questions: &[Question]) -> anyhow::Result<Vec<Uuid>> {
        let mut store = self.questions.write().await;
        for q in questions {
            store.push(q.clone());
        }
        Ok(questions.iter().map(|q| q.id).collect())
    }

    async fn find_by_id(&self, id: Uuid) -> anyhow::Result<Option<Question>> {
        let store = self.questions.read().await;
        Ok(store.iter().find(|q| q.id == id).cloned())
    }

    async fn find_by_type(
        &self,
        qtype: &crate::models::QuestionType,
    ) -> anyhow::Result<Vec<Question>> {
        let store = self.questions.read().await;
        Ok(store.iter().filter(|q| &q.qtype == qtype).cloned().collect())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_mock_repository() {
        let repo = MockRepository::new();
        let question = Question::default();

        let ids = repo.save_batch(&[question.clone()]).await.unwrap();
        assert_eq!(ids.len(), 1);

        let found = repo.find_by_id(ids[0]).await.unwrap();
        assert!(found.is_some());

        let all = repo.find_by_type(&question.qtype).await.unwrap();
        assert_eq!(all.len(), 1);
    }
}
