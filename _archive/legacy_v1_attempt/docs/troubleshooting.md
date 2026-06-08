# Troubleshooting — COPILOTO

## Docker / PostgreSQL

**Symptom:** `connection refused` on port 5432

1. Ensure Docker Desktop is running
2. Run `docker compose ps` — both `copiloto_postgres` and `copiloto_redis` should be healthy
3. Run `docker compose up -d` from project root

**Symptom:** pgvector extension missing

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## Redis

**Symptom:** Redis connection error on port 6379

1. Check container: `docker compose logs redis`
2. Verify `REDIS_URL=redis://localhost:6379/0` in `.env`

## Ollama

**Symptom:** `/api/v1/health` shows `ollama: false`

1. Start Ollama: `ollama serve`
2. Pull models:
   ```bash
   ollama pull llama3.2:3b
   ollama pull mistral:7b-instruct
   ollama pull nomic-embed-text
   ```
3. Verify: `ollama list`
4. Check `OLLAMA_BASE_URL=http://localhost:11434`

**Symptom:** Out of memory / slow responses

- Set `OLLAMA_MAX_LOADED_MODELS=1`
- Prefer `llama3.2:3b` for quick tasks
- Reduce RAG chunks via `RAG_TOP_K=3`

## Telegram

**Symptom:** Bot not responding

1. Set `TELEGRAM_ENABLED=true`
2. Set `TELEGRAM_BOT_TOKEN` from @BotFather
3. Set `TELEGRAM_ALLOWED_USER_ID` to your Telegram user ID
4. Restart backend

## Migrations

```bash
cd backend
alembic upgrade head
python scripts/seed_user.py
```

Or without Alembic:

```bash
cd backend
python scripts/init_db.py
```

## Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Default Login (after seed)

- Email: `admin@copiloto.local`
- Password: `copiloto123`

Change immediately in production.

## Tests

```bash
cd backend
pytest
```
