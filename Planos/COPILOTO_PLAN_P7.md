# COPILOTO_PLAN.md

# PARTE 7 — INSTALAÇÃO, EXECUÇÃO, TESTES, QUALIDADE, DEBUG E MODO PLAN DO CURSOR

---

# 286. OBJETIVO DA PARTE 7

Esta parte define como o Cursor deve implementar, testar, corrigir e validar o projeto.

Regra principal:

```txt
Não gerar tudo de uma vez.
```

O projeto deve ser construído por fases pequenas, com testes após cada fase.

---

# 287. COMO O CURSOR DEVE TRABALHAR

O Cursor deve:

```txt
1. Ler o COPILOTO_PLAN.md inteiro.
2. Criar um plano técnico.
3. Dividir em fases.
4. Implementar uma fase.
5. Testar.
6. Corrigir.
7. Esperar aprovação.
8. Avançar.
```

Nunca avançar sem validação.

---

# 288. PROMPT INICIAL PARA O CURSOR

Use este comando no Cursor:

```txt
Leia o arquivo COPILOTO_PLAN.md inteiro.

Você está no modo Plan.

Não implemente nada ainda.

Primeiro:
1. Entenda o produto.
2. Resuma a arquitetura.
3. Liste os módulos.
4. Aponte riscos técnicos.
5. Sugira uma ordem de implementação.
6. Crie um checklist de execução.
7. Aguarde minha aprovação.

Não escreva código nesta primeira resposta.
```

---

# 289. PROMPT PARA EXECUTAR UMA FASE

Depois que o Cursor criar o plano, use:

```txt
Execute somente a Fase 01.

Regras:
- Não avance para a Fase 02.
- Crie apenas os arquivos necessários para esta fase.
- Explique o que foi criado.
- Rode ou indique os testes.
- Liste pendências.
- Aguarde minha aprovação.
```

---

# 290. PROMPT PARA CORREÇÃO

Se der erro:

```txt
Analise o erro abaixo.

Corrija apenas o necessário.

Não reescreva arquivos inteiros sem necessidade.

Explique:
1. Causa do erro.
2. Arquivos alterados.
3. Como testar novamente.

Erro:
[cole o erro aqui]
```

---

# 291. PROMPT PARA REVISÃO DE FASE

Ao terminar uma fase:

```txt
Revise a fase atual.

Verifique:
- arquivos criados
- imports
- dependências
- testes
- possíveis bugs
- inconsistências com COPILOTO_PLAN.md

Não avance de fase.

Apenas revise e proponha correções.
```

---

# 292. ORDEM OFICIAL DE IMPLEMENTAÇÃO

Implementar nesta ordem:

```txt
Fase 01 — Estrutura do projeto
Fase 02 — Docker Compose
Fase 03 — Backend Core
Fase 04 — Banco + Alembic
Fase 05 — Models principais
Fase 06 — CRUD básico
Fase 07 — Ollama direto
Fase 08 — Chat simples
Fase 09 — WebSocket streaming
Fase 10 — RAG por chunks
Fase 11 — Memória evolutiva
Fase 12 — Telegram Instructor
Fase 13 — Scheduler
Fase 14 — Dashboard base
Fase 15 — Módulo tarefas
Fase 16 — Módulo hábitos
Fase 17 — Módulo notas
Fase 18 — Módulo finanças
Fase 19 — Módulo estudos
Fase 20 — Módulo treino
Fase 21 — Relatórios
Fase 22 — Projetos e decisões
Fase 23 — Segurança
Fase 24 — Performance
Fase 25 — README final
```

---

# 293. FASE 01 — ESTRUTURA DO PROJETO

Criar pastas:

```txt
copiloto/
backend/
frontend/
scripts/
docs/
tests/
backups/
```

Criar arquivos base:

```txt
README.md
.gitignore
.env.example
docker-compose.yml
```

Critério de aceite:

```txt
Estrutura criada corretamente.
```

---

# 294. FASE 02 — DOCKER COMPOSE

Criar serviços:

```txt
PostgreSQL + pgvector
Redis
```

Critério de aceite:

```txt
docker compose up -d
docker ps
```

Deve mostrar:

```txt
copiloto_postgres
copiloto_redis
```

---

# 295. FASE 03 — BACKEND CORE

Criar:

```txt
FastAPI
Config
Database
Redis Client
Logging
Healthcheck
```

Endpoints:

```txt
/health
/api/v1/health
```

Critério de aceite:

```txt
python main.py
curl http://localhost:8000/health
```

---

# 296. FASE 04 — BANCO + ALEMBIC

Criar:

```txt
Alembic
Base Models
Migrations
UUID
pgvector
```

Critério de aceite:

```txt
alembic upgrade head
```

Sem erros.

---

# 297. FASE 05 — MODELS PRINCIPAIS

Criar models:

```txt
users
tasks
habits
habit_logs
notes
documents
document_chunks
chat_sessions
chat_messages
ai_memories
daily_journal
```

Critério de aceite:

```txt
Tabelas criadas no PostgreSQL.
```

---

# 298. FASE 06 — CRUD BÁSICO

Criar CRUD para:

```txt
tasks
habits
notes
```

Critério de aceite:

```txt
Criar
Listar
Editar
Deletar
```

via `/docs`.

---

# 299. FASE 07 — OLLAMA DIRETO

Criar:

```txt
app/ai/ollama.py
```

Funções:

```txt
generate
chat
stream
embed
health
```

Critério de aceite:

```txt
/api/v1/ai/health
```

Deve listar modelos disponíveis.

---

# 300. FASE 08 — CHAT SIMPLES

Criar:

```txt
/api/v1/chat/message
```

Critério de aceite:

```txt
Enviar mensagem.
Receber resposta da IA.
Salvar histórico.
```

---

# 301. FASE 09 — WEBSOCKET STREAMING

Criar:

```txt
/ws/chat
```

Critério de aceite:

```txt
Resposta aparece em streaming token por token.
```

---

# 302. FASE 10 — RAG POR CHUNKS

Criar:

```txt
chunk_text
index_note
search_chunks
build_context
```

Critério de aceite:

```txt
Criar nota.
Indexar.
Perguntar sobre a nota.
IA responder usando conteúdo.
```

---

# 303. FASE 11 — MEMÓRIA EVOLUTIVA

Criar:

```txt
ai_memories
ai_notes
daily_journal
memory_extractor
```

Critério de aceite:

```txt
Conversa gera memória útil.
Memória aparece no dashboard/API.
```

---

# 304. FASE 12 — TELEGRAM INSTRUCTOR

Criar:

```txt
bot
handlers
classify_message
memory update
```

Critério de aceite:

```txt
Mandar mensagem natural pelo Telegram.
Bot entende.
Registra.
Responde.
```

---

# 305. FASE 13 — SCHEDULER

Criar:

```txt
APScheduler
check-ins
lembretes
resumo diário
```

Critério de aceite:

```txt
Job executa no horário configurado.
```

---

# 306. FASE 14 — DASHBOARD BASE

Criar:

```txt
Vite
HTML
CSS
JS Modules
Layout
Sidebar
Header
```

Critério de aceite:

```txt
Dashboard abre no navegador.
```

---

# 307. FASE 15 — MÓDULO TAREFAS

Implementar frontend + backend.

Critério de aceite:

```txt
Criar tarefa no dashboard.
Aparecer no banco.
```

---

# 308. FASE 16 — MÓDULO HÁBITOS

Implementar:

```txt
hábitos
streaks
logs
```

Critério de aceite:

```txt
Marcar hábito.
Atualizar streak.
```

---

# 309. FASE 17 — MÓDULO NOTAS

Implementar:

```txt
Markdown
Tags
RAG
Busca
```

Critério de aceite:

```txt
Criar nota.
Pesquisar semanticamente.
```

---

# 310. FASE 18 — MÓDULO FINANÇAS

Implementar:

```txt
receitas
despesas
categorias
saldo
gráficos
```

Critério de aceite:

```txt
Registrar gasto.
Aparecer no dashboard financeiro.
```

---

# 311. FASE 19 — MÓDULO ESTUDOS

Implementar:

```txt
matérias
tópicos
flashcards
plano IA
quiz
```

Critério de aceite:

```txt
Criar tópico.
Gerar plano de estudo com IA.
```

---

# 312. FASE 20 — MÓDULO TREINO

Implementar:

```txt
planos
exercícios
histórico
cargas
```

Critério de aceite:

```txt
Registrar treino.
Ver progresso.
```

---

# 313. FASE 21 — RELATÓRIOS

Implementar:

```txt
diário
semanal
mensal
IA analyst
```

Critério de aceite:

```txt
Gerar relatório semanal.
```

---

# 314. FASE 22 — PROJETOS E DECISÕES

Implementar:

```txt
projects
goals
decisions
commitments
```

Critério de aceite:

```txt
Criar projeto.
Criar milestones.
Gerar plano.
```

---

# 315. FASE 23 — SEGURANÇA

Implementar:

```txt
Auth
JWT
Rate Limit
CORS
Allowed Telegram User
```

Critério de aceite:

```txt
Usuário não autorizado não acessa.
```

---

# 316. FASE 24 — PERFORMANCE

Implementar:

```txt
Cache
Paginação
Índices
Lazy Loading
Otimização IA
```

Critério de aceite:

```txt
Dashboard rápido.
Chat com streaming.
API estável.
```

---

# 317. FASE 25 — README FINAL

Criar README com:

```txt
instalação
configuração
comandos
modelos Ollama
Telegram
Tailscale
troubleshooting
```

---

# 318. TESTES OBRIGATÓRIOS

Criar testes para:

```txt
Config
Database
Redis
Tasks
Notes
RAG
Ollama
Telegram Classifier
```

---

# 319. COMANDOS DE TESTE

Backend:

```bash
pytest
```

API:

```bash
curl http://localhost:8000/health
```

Docker:

```bash
docker compose ps
```

Ollama:

```bash
ollama list
```

---

# 320. DEBUG

Quando houver erro, verificar:

```txt
.env
Docker
PostgreSQL
Redis
Ollama
Imports
Migrations
```

---

# 321. TROUBLESHOOTING COMUM

Erro PostgreSQL:

```txt
Verificar se container está rodando.
```

Erro Redis:

```txt
Verificar porta 6379.
```

Erro Ollama:

```txt
Verificar ollama serve.
```

Erro Telegram:

```txt
Verificar token e allowed_user_id.
```

---

# 322. PADRÃO DE COMMITS

Usar:

```txt
feat:
fix:
refactor:
docs:
test:
perf:
```

---

# 323. PADRÃO DE QUALIDADE

Todo código deve ter:

```txt
typing
tratamento de erro
logs
comentários úteis
```

---

# 324. NÃO FAZER

O Cursor não deve:

```txt
implementar tudo de uma vez
ignorar testes
misturar fases
usar LangChain na Fase 1
colocar Ollama no Docker
expor API pública
```

---

# 325. FINALIZAÇÃO

Ao final de cada fase, o Cursor deve responder:

```txt
Fase concluída:
Arquivos criados:
Testes realizados:
Como validar:
Pendências:
Próxima fase sugerida:
```

---

# FIM DA PARTE 7

Documento pronto para orientar implementação faseada no Cursor.
