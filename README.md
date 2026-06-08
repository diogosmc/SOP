# COPILOTO

**Sistema Operacional Pessoal Inteligente** — V1

Assistente pessoal local-first: tarefas, hábitos, notas, finanças, estudos, treino, chat com IA (Ollama), RAG, memória evolutiva, Telegram, relatórios e dashboard web.

Plano detalhado das fases: [`Planos/`](Planos/).

---

## Visão geral

O COPILOTO centraliza sua vida digital em um único sistema:

- **Backend** FastAPI + PostgreSQL (pgvector) + Redis
- **Frontend** SPA Vite (dashboard + módulos)
- **IA local** via Ollama (sem dependência de cloud)
- **Telegram** como canal mobile (modo instructor)
- **Auth JWT** opcional (cookies HttpOnly)
- **Single-user** por padrão em desenvolvimento

Módulos V1: tarefas, hábitos, notas, finanças, estudos, treino, chat, memória, lembretes, relatórios, analytics, scheduler.

**Fora do V1:** projetos/decisões (V1.1), Tauri/voz/OCR (V2).

---

## Stack

| Camada | Tecnologia |
|--------|------------|
| API | Python 3.10+, FastAPI, SQLAlchemy async, Alembic |
| Banco | PostgreSQL 16 + pgvector |
| Cache / rate limit | Redis 7 |
| IA | Ollama (HTTP local) |
| Frontend | Vite 6, JavaScript vanilla, Chart.js |
| Bot | python-telegram-bot (polling) |
| Infra | Docker Compose |

---

## Requisitos

| Ferramenta | Versão mínima | Obrigatório |
|------------|---------------|-------------|
| Docker + Compose | recente | Sim (Postgres + Redis) |
| Python | 3.10+ | Sim |
| Node.js | 18+ | Sim (frontend) |
| Ollama | latest | Sim (IA) |
| Git Bash / WSL | — | Scripts `.sh` no Windows |
| [Tailscale](https://tailscale.com) | — | Opcional (acesso remoto) |

Hardware recomendado: **GTX 1660 (6 GB)** ou similar — veja [docs/ollama.md](docs/ollama.md).

---

## Instalação do zero

### 1. Clone e configure

```bash
git clone <repo-url> copiloto
cd copiloto
cp .env.example .env
# Edite .env: senhas, JWT_SECRET_KEY (produção)
```

### 2. Infraestrutura (PostgreSQL + Redis)

```bash
docker compose config
docker compose up -d
docker compose ps
```

Ou use o script:

```bash
chmod +x scripts/*.sh
./scripts/start_dev.sh
```

Containers: `copiloto_postgres`, `copiloto_redis`.

### 3. Backend

```bash
cd backend
pip install -r requirements.txt
python -m alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Modelos Ollama

Em outro terminal:

```bash
ollama serve
ollama pull llama3.2:3b
ollama pull mistral:7b-instruct
ollama pull nomic-embed-text
ollama list
```

### 5. Frontend

```bash
cd frontend
npm install
npm run dev
```

Abra: **http://localhost:5173**

### 6. Verificação

```bash
./scripts/check_health.sh
```

Ou manualmente:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/ai/health
```

---

## Configuração `.env`

Copie `.env.example` → `.env`. Variáveis principais:

| Variável | Descrição |
|----------|-----------|
| `DATABASE_URL` | PostgreSQL async (`postgresql+asyncpg://...`) |
| `REDIS_URL` | Redis (`redis://localhost:6379/0`) |
| `OLLAMA_*` | URL e modelos — ver [docs/ollama.md](docs/ollama.md) |
| `AUTH_ENABLED` | `false` = single-user; `true` = login obrigatório |
| `JWT_SECRET_KEY` | **Trocar em produção** (32+ caracteres) |
| `CORS_ORIGINS` | Origens do frontend (vírgula) |
| `TELEGRAM_*` | Bot — ver [docs/telegram.md](docs/telegram.md) |
| `SCHEDULER_ENABLED` | Check-ins e resumos automáticos |
| `CACHE_ENABLED` | Cache Redis em summaries/relatórios |

---

## Checklist — instalação

- [ ] Docker Desktop rodando
- [ ] `cp .env.example .env` e senhas alteradas
- [ ] `docker compose up -d` — postgres + redis healthy
- [ ] `cd backend && pip install -r requirements.txt`
- [ ] `python -m alembic upgrade head`
- [ ] Ollama rodando + 3 modelos instalados
- [ ] Backend: `uvicorn app.main:app --reload --port 8000`
- [ ] Frontend: `cd frontend && npm install && npm run dev`
- [ ] `./scripts/check_health.sh` — tudo OK
- [ ] Dashboard abre em http://localhost:5173

---

## Checklist — produção local / Tailscale

Uso pessoal na rede Tailscale (sem expor à internet pública):

- [ ] `AUTH_ENABLED=true` + `JWT_SECRET_KEY` forte
- [ ] `POSTGRES_PASSWORD` e senhas reais (não defaults)
- [ ] `COOKIE_SECURE=true` se usar HTTPS reverso; `false` em HTTP local
- [ ] `CORS_ORIGINS` inclui IP Tailscale do frontend (ex.: `http://100.x.x.x:5173`)
- [ ] Firewall: liberar portas apenas na tailnet
- [ ] Ollama na mesma máquina ou URL Tailscale em `OLLAMA_BASE_URL`
- [ ] Backup agendado: `./scripts/backup_db.sh`
- [ ] Telegram: `TELEGRAM_ALLOWED_USER_ID` restrito ao seu ID
- [ ] `./scripts/check_health.sh` após deploy

---

## Telegram

1. Crie bot em [@BotFather](https://t.me/BotFather)
2. Obtenha seu ID em [@userinfobot](https://t.me/userinfobot)
3. Configure `.env`:
   ```env
   TELEGRAM_ENABLED=true
   TELEGRAM_BOT_TOKEN=...
   TELEGRAM_ALLOWED_USER_ID=...
   ```
4. Reinicie o backend

Detalhes: [docs/telegram.md](docs/telegram.md)

---

## Auth (JWT)

**Desenvolvimento:** `AUTH_ENABLED=false` — funciona sem login.

**Produção:**

```env
AUTH_ENABLED=true
JWT_SECRET_KEY=seu_segredo_longo_e_unico_aqui
COOKIE_SECURE=false
```

1. Acesse http://localhost:5173/#/login
2. **Bootstrap admin** (primeira vez, se não houver usuário com senha)
3. Login → cookies HttpOnly (`access_token`, `refresh_token`)

Endpoints: `/api/v1/auth/login`, `/logout`, `/refresh`, `/me`, `/bootstrap-admin`

---

## Tailscale (acesso remoto)

1. Instale Tailscale na máquina que roda o COPILOTO
2. Anote o IP `100.x.x.x` (`tailscale ip`)
3. Backend: `--host 0.0.0.0` (já padrão)
4. Frontend dev: `npm run dev -- --host 0.0.0.0`
5. Acesse de outro dispositivo: `http://100.x.x.x:5173`
6. Adicione o IP em `CORS_ORIGINS`
7. Se Ollama estiver em outra máquina: `OLLAMA_BASE_URL=http://100.x.x.x:11434`

---

## Backup e restore

### Backup

```bash
./scripts/backup_db.sh
# Gera: backups/copiloto_YYYYMMDD_HHMMSS.sql
```

Usa `docker exec copiloto_postgres pg_dump` ou `pg_dump` local. Lê variáveis do `.env`.

### Restore

```bash
./scripts/restore_db.sh backups/copiloto_20260607_120000.sql
# Digite 'yes' para confirmar — SUBSTITUI dados atuais
```

---

## Scripts utilitários

| Script | Função |
|--------|--------|
| `scripts/start_dev.sh` | Sobe Docker + instruções |
| `scripts/check_health.sh` | Docker + health endpoints |
| `scripts/backup_db.sh` | Backup PostgreSQL |
| `scripts/restore_db.sh` | Restore com confirmação |

No Windows: use **Git Bash** ou WSL. `chmod +x scripts/*.sh` no Linux/macOS.

---

## Troubleshooting

Guia completo: [docs/troubleshooting.md](docs/troubleshooting.md)

Problemas comuns: Docker, Postgres, Redis, Ollama, Telegram, Auth/CORS, migrations, pgvector, frontend offline.

---

## Documentação técnica

| Doc | Conteúdo |
|-----|----------|
| [docs/schema.md](docs/schema.md) | Tabelas e migrations |
| [docs/api.md](docs/api.md) | Endpoints REST + WS |
| [docs/ollama.md](docs/ollama.md) | Modelos e VRAM |
| [docs/telegram.md](docs/telegram.md) | Bot instructor |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Solução de problemas |
| http://localhost:8000/docs | OpenAPI interativo |

---

## Performance esperado

Referências locais (GTX 1660 + 16 GB RAM):

| Operação | Expectativa |
|----------|-------------|
| Dashboard (cache warm) | < 1s |
| API CRUD paginada | < 200ms |
| Chat streaming (3B) | 1º token 1–3s |
| Chat streaming (7B) | 1º token 3–8s |
| RAG search (HNSW) | < 500ms (base pequena) |

---

## Testes

```bash
docker compose up -d
cd backend && python -m alembic upgrade head
cd .. && python -m pytest -v
cd frontend && npm run build
```

---

## Estrutura do projeto

```txt
.
├── backend/          # API FastAPI
├── frontend/         # Dashboard Vite
├── scripts/          # backup, restore, dev, health
├── docs/             # Documentação V1
├── tests/            # Testes raiz
├── backups/          # Backups SQL (gitignored)
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Roadmap

### V1 — entregue

Fases 01–24: infra, CRUD, IA, RAG, memória, Telegram, scheduler, dashboard, módulos frontend, finanças, estudos, treino, relatórios, auth/JWT, performance/cache, documentação e scripts.

### V1.1 — próximo

- Projetos e decisões
- Melhorias incrementais

### V2 — futuro

- App desktop **Tauri**
- Voz
- OCR / captura de documentos

---

## Licença / uso

Projeto pessoal. Ajuste `.env` e credenciais antes de qualquer exposição pública.

---

## Histórico de fases (referência)

<details>
<summary>Fases 01–23 (clique para expandir)</summary>

- **01–06:** Estrutura, Docker, backend, Alembic, models, CRUD
- **07–11:** Ollama, chat, WebSocket, RAG, memória
- **12–13:** Telegram, scheduler
- **14–21:** Dashboard + módulos frontend + relatórios
- **22:** Auth / JWT
- **23:** Performance / cache / índices / lazy loading

Detalhes em [`Planos/`](Planos/).

</details>
