# Troubleshooting — COPILOTO V1

Guia rápido para problemas comuns. Para instalação completa, veja o [README](../README.md).

---

## Docker não sobe

**Sintomas:** `docker compose up` falha ou containers reiniciam.

1. Verifique se o Docker Desktop (ou Docker Engine) está rodando.
2. Porta em uso:
   ```bash
   docker compose ps
   netstat -an | findstr 5432   # Windows
   ```
3. Recrie containers:
   ```bash
   docker compose down
   docker compose up -d
   docker compose logs postgres
   docker compose logs redis
   ```
4. Valide config:
   ```bash
   docker compose config
   ```

---

## PostgreSQL — erro de conexão

**Sintomas:** `connection refused`, `password authentication failed`, Alembic não conecta.

1. Container saudável:
   ```bash
   docker compose ps
   docker exec copiloto_postgres pg_isready -U copiloto -d copiloto
   ```
2. Confira `.env`:
   - `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
   - `DATABASE_URL=postgresql+asyncpg://USER:PASS@localhost:5432/copiloto`
3. Senha do `.env` deve coincidir com a usada na **primeira** subida do container. Se mudou a senha depois, recrie o volume:
   ```bash
   docker compose down -v   # APAGA DADOS
   docker compose up -d
   cd backend && python -m alembic upgrade head
   ```

---

## Redis offline

**Sintomas:** `/api/v1/health` mostra `redis: false`, rate limit ou cache desabilitados.

1. `docker compose logs redis`
2. Confira `REDIS_URL=redis://localhost:6379/0`
3. **Nota:** Com Redis offline, a API continua funcionando (cache e rate limit fazem fallback).

---

## Ollama offline

**Sintomas:** `/api/v1/ai/health` com `ollama: false`, chat sem resposta.

1. Inicie o serviço:
   ```bash
   ollama serve
   ```
2. Instale modelos (veja [ollama.md](ollama.md)):
   ```bash
   ollama pull llama3.2:3b
   ollama pull mistral:7b-instruct
   ollama pull nomic-embed-text
   ```
3. Confira `OLLAMA_BASE_URL=http://localhost:11434`
4. Teste: `curl http://localhost:11434/api/tags`

---

## Modelos não encontrados

**Sintomas:** Erro 404 ou modelo inexistente no chat.

1. `ollama list` — confira nomes exatos.
2. Ajuste `.env`:
   ```env
   OLLAMA_MODEL_FAST=llama3.2:3b
   OLLAMA_MODEL_MAIN=mistral:7b-instruct
   OLLAMA_MODEL_EMBED=nomic-embed-text
   ```
3. Reinicie o backend após alterar `.env`.

---

## Telegram não responde

**Sintomas:** Bot silencioso ou mensagem de não autorizado.

1. `.env`:
   ```env
   TELEGRAM_ENABLED=true
   TELEGRAM_BOT_TOKEN=...        # @BotFather
   TELEGRAM_ALLOWED_USER_ID=...  # seu ID numérico
   ```
2. Reinicie o backend (bot inicia no lifespan).
3. Veja [telegram.md](telegram.md).
4. Logs: procure `telegram_start_failed` no console do backend.

---

## Auth / cookies

**Sintomas:** Redirect loop para login, 401 em todas as rotas.

1. Dev: `AUTH_ENABLED=false` (modo single-user).
2. Produção local:
   ```env
   AUTH_ENABLED=true
   JWT_SECRET_KEY=...   # 32+ chars, único
   COOKIE_SECURE=false  # true apenas com HTTPS
   ```
3. Bootstrap admin (primeira vez): `POST /api/v1/auth/bootstrap-admin` ou `#/login`.
4. Frontend usa cookies HttpOnly — não desabilite `credentials: include`.
5. Limpe cookies do browser se tokens antigos causarem problemas.

---

## CORS

**Sintomas:** Browser bloqueia fetch, erro CORS no console.

1. Inclua a origem do frontend em `.env`:
   ```env
   CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000
   ```
2. Tailscale: adicione `http://100.x.x.x:5173` (IP da máquina).
3. Reinicie o backend após alterar CORS.

---

## Migrations

**Sintomas:** Tabela não existe, Alembic desatualizado.

```bash
cd backend
python -m alembic current
python -m alembic upgrade head
python -m alembic history
```

Downgrade (cuidado — pode perder dados):
```bash
python -m alembic downgrade -1
```

---

## pgvector

**Sintomas:** Erro ao criar índice HNSW ou extensão `vector` missing.

1. Use a imagem correta: `pgvector/pgvector:pg16` (já no `docker-compose.yml`).
2. Verifique extensões:
   ```bash
   docker exec copiloto_postgres psql -U copiloto -d copiloto -c "\dx"
   ```
3. Se necessário:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
4. Migration 007 cria índices HNSW — requer pgvector 0.5+.

---

## Frontend não conecta no backend

**Sintomas:** Dashboard offline, timeout, 502.

1. Backend rodando: `uvicorn app.main:app --reload --port 8000`
2. Dev Vite faz proxy de `/api` e `/health` → `localhost:8000` (veja `frontend/vite.config.js`).
3. Acesse via `http://localhost:5173` (não abra `file://`).
4. `./scripts/check_health.sh`
5. Firewall/antivirus bloqueando portas 8000/5173.

---

## Backup / restore falhou

1. Container postgres deve estar rodando.
2. Git Bash ou WSL no Windows para scripts `.sh`.
3. Restore pede confirmação `yes` — dados atuais serão substituídos.

---

## Testes falhando

```bash
docker compose up -d
cd backend && python -m alembic upgrade head
cd .. && python -m pytest -v
```

PostgreSQL de teste usa o mesmo `DATABASE_URL` do `.env`.
