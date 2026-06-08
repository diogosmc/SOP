# COPILOTO — Schema do banco (V1)

PostgreSQL 16 + **pgvector** + **uuid-ossp**. PKs em UUID; timestamps `created_at` / `updated_at` na maioria das tabelas.

## Diagrama lógico (resumo)

```txt
users
 ├── tasks, habits, notes, documents, chat_sessions
 ├── ai_memories, ai_notes, daily_journal, reminders
 ├── finance_transactions
 ├── study_subjects → study_topics → flashcards, study_sessions
 └── workout_profiles, exercises, workout_plans → workout_logs → exercise_set_logs

documents → document_chunks (embedding vector 768)
notes → (indexação RAG via documents)
```

## Tabelas principais

### users

Usuário local. Campos auth (migration 006): `hashed_password`, `is_active`, `is_admin`.

### Core

| Tabela | Descrição |
|--------|-----------|
| tasks | Tarefas (status, priority, due_date) |
| habits | Hábitos positivos/negativos |
| habit_logs | Registro diário por hábito |
| notes | Notas com tags, favorite, archived |
| documents | Fontes indexadas para RAG |
| document_chunks | Chunks + `embedding vector(768)` |
| chat_sessions | Sessões (origin: dashboard, telegram, api) |
| chat_messages | Mensagens + model_used, response_time_ms |
| ai_memories | Memória evolutiva + embedding |
| ai_notes | Notas geradas pela IA + embedding |
| daily_journal | Diário por data (summary, mood, módulos) |
| reminders | Lembretes (telegram/dashboard) |

### Finanças (003)

| Tabela | Descrição |
|--------|-----------|
| finance_transactions | Receitas/despesas, category, transaction_date |

### Estudos (004)

| Tabela | Descrição |
|--------|-----------|
| study_subjects | Matérias |
| study_topics | Tópicos por matéria |
| flashcards | SM-2 (next_review, interval, ease) |
| study_sessions | Sessões de estudo (duration_minutes) |

### Treino (005)

| Tabela | Descrição |
|--------|-----------|
| workout_profiles | Perfil do usuário |
| exercises | Catálogo de exercícios |
| workout_plans | Planos ativos |
| workout_plan_exercises | Exercícios no plano |
| workout_logs | Treinos por data |
| exercise_set_logs | Séries (reps, weight, rpe) |

## Embeddings

Colunas `vector(768)` em:

- `document_chunks.embedding`
- `ai_memories.embedding`
- `ai_notes.embedding`

Migration **007** adiciona índices **HNSW** (`vector_cosine_ops`) para busca RAG.

## Migrations Alembic

| Revisão | Descrição |
|---------|-----------|
| 001_initial | Extensões + users |
| 002_main_models | Core (tasks, habits, notes, chat, memory, …) |
| 003_finance | finance_transactions |
| 004_study | study_* |
| 005_workout | workout_* |
| 006_user_auth_fields | hashed_password, is_active, is_admin |
| 007_performance_indexes | Índices compostos + HNSW |

```bash
cd backend && python -m alembic upgrade head
```

## Índices (V1)

Índices simples por FK/filtro + compostos (007):

- tasks: `(user_id, status, due_date)`
- habits: `(user_id, active, type)`
- notes: `(user_id, favorite, archived)`, `(user_id, created_at)`
- finance: `(user_id, transaction_date, type, category)`
- study_sessions: `(user_id, created_at)`
- workout_logs: `(user_id, date)`
- chat_messages: `(session_id, created_at)`
- ai_memories: `(user_id, type, importance)`
- reminders: `(user_id, remind_at, status)`

Detalhes coluna a coluna das tabelas core: seções abaixo (Fase 05).

---

## users

| Coluna | Tipo | Notas |
|--------|------|-------|
| id | UUID PK | |
| name | VARCHAR(255) | |
| email | VARCHAR(255) UNIQUE | nullable |
| hashed_password | VARCHAR | nullable (auth) |
| is_active | BOOLEAN | default true |
| is_admin | BOOLEAN | default false |
| telegram_id | BIGINT UNIQUE | nullable |
| timezone | VARCHAR(64) | default `America/Sao_Paulo` |
| preferences | JSONB | default `{}` |

## tasks / habits / notes / chat / memory

Ver estrutura completa nas migrations `002_main_models.py`. Campos principais documentados na tabela acima.

## Fora do escopo V1

- **Projetos e decisões** → V1.1
- **Tauri / voz / OCR** → V2
