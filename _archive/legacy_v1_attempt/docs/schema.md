# COPILOTO Database Schema (V1)

## Core

| Table | Description |
|-------|-------------|
| `users` | User accounts (single-user default in dev) |

## Productivity

| Table | Description |
|-------|-------------|
| `tasks` | Tasks with status, priority, due dates |
| `habits` | Positive/negative habits with streaks |
| `habit_logs` | Daily habit completion logs |
| `notes` | Markdown notes with tags |
| `reminders` | Scheduled reminders |

## RAG

| Table | Description |
|-------|-------------|
| `documents` | Indexed document sources |
| `document_chunks` | Text chunks with pgvector embeddings (768d) |

## Chat

| Table | Description |
|-------|-------------|
| `chat_sessions` | Conversation sessions |
| `chat_messages` | Messages per session |

## Memory

| Table | Description |
|-------|-------------|
| `ai_memories` | Extracted user memories with embeddings |
| `ai_notes` | AI-generated observations |
| `daily_journal` | Auto-generated daily summaries |
| `weekly_reviews` | Weekly review reports |
| `entity_relations` | Simplified knowledge graph edges |

## Finance

| Table | Description |
|-------|-------------|
| `finance_categories` | Expense/income categories |
| `finance_transactions` | Transactions |
| `finance_goals` | Financial goals |

## Study

| Table | Description |
|-------|-------------|
| `study_subjects` | ENEM subjects |
| `study_topics` | Topics with mastery status |
| `flashcards` | SM-2 spaced repetition cards |
| `study_sessions` | Study time logs |

## Workout

| Table | Description |
|-------|-------------|
| `workout_plans` | Training splits (A-E) |
| `exercises` | Exercises per plan |
| `workout_sessions` | Completed workouts |
| `workout_sets` | Sets with weight/reps |
| `physical_profiles` | User physical profile |

## Indexes

- All tables: `user_id` indexed where applicable
- Date fields: indexed for reports and analytics
- `document_chunks.embedding`: pgvector cosine index (created at runtime if needed)
