# API — COPILOTO V1

Base URL: `http://localhost:8000`

Documentação interativa: **http://localhost:8000/docs**

## Health

| Método | Path | Descrição |
|--------|------|-----------|
| GET | `/health` | Status básico |
| GET | `/api/v1/health` | API + PostgreSQL + Redis |
| GET | `/api/v1/ai/health` | Ollama + modelos |

## Auth (quando `AUTH_ENABLED=true`)

| Método | Path | Descrição |
|--------|------|-----------|
| POST | `/api/v1/auth/login` | Login (cookies HttpOnly) |
| POST | `/api/v1/auth/logout` | Logout |
| POST | `/api/v1/auth/refresh` | Renovar tokens |
| GET | `/api/v1/auth/me` | Usuário atual |
| POST | `/api/v1/auth/bootstrap-admin` | Primeiro admin (uma vez) |

## Módulos principais

Prefixo comum: `/api/v1`

| Grupo | Prefixo | Recursos |
|-------|---------|----------|
| Tarefas | `/tasks` | CRUD, paginação, filtros |
| Hábitos | `/habits` | CRUD, paginação |
| Notas | `/notes` | CRUD, busca, RAG semântico |
| Finanças | `/finance` | Transações, summary, by-category |
| Estudos | `/study` | Matérias, tópicos, flashcards, sessões |
| Treino | `/workout` | Exercícios, planos, logs, summary |
| Chat | `/chat` | Mensagens, sessões, streaming WS |
| Memória | `/memory` | Memórias IA, notas IA, diário |
| Relatórios | `/reports` | Diário, semanal, analytics, insights |
| Lembretes | `/reminders` | CRUD, due, cancel |
| IA | `/ai` | Health, modelos, route-test |

## WebSocket

| Path | Descrição |
|------|-----------|
| `/ws/chat` | Chat streaming com tokens |

## Resposta padrão

```json
{
  "success": true,
  "data": { }
}
```

Erro:

```json
{
  "success": false,
  "error": { "message": "..." }
}
```

## Paginação

Listas usam `page` e `page_size` (máx. 100):

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20,
  "pages": 1
}
```

## Autenticação

- `AUTH_ENABLED=false`: header/cookie opcional; usa `default_user_id`.
- `AUTH_ENABLED=true`: cookie `access_token` HttpOnly obrigatório (exceto rotas públicas).

Rotas públicas: `/health`, `/api/v1/health`, login, bootstrap, refresh.

## Cache (Redis)

Summaries e relatórios usam cache com TTL (60s–900s). Ver README seção Performance.

Schema: [schema.md](schema.md)
