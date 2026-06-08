# COPILOTO_PLAN.md

# PARTE 1 — VISÃO GERAL, ARQUITETURA E FUNDAÇÃO DO PROJETO

---

# 1. VISÃO GERAL

## Nome do Projeto

**COPILOTO**

## Objetivo

Criar um Sistema Operacional Pessoal Inteligente.

O projeto não deve ser tratado como um chatbot.

O projeto deve ser tratado como um ecossistema pessoal composto por:

* IA Local
* Dashboard
* Telegram
* Banco de Dados
* Memória Inteligente
* Finanças
* Estudos
* Treino
* Hábitos
* Rotina
* Relatórios

A IA será apenas um dos módulos do sistema.

---

# 2. VISÃO DE LONGO PRAZO

O objetivo final é construir uma IA que:

* acompanhe minha evolução
* aprenda meus padrões
* conheça meus objetivos
* me ajude diariamente
* organize minha rotina
* acompanhe meus estudos
* acompanhe meu treino
* acompanhe minhas finanças
* funcione como um copiloto pessoal

O sistema deve ficar mais inteligente com o tempo.

Quanto mais eu utilizar:

* Telegram
* Dashboard
* Notas
* Estudos
* Treinos

mais contexto a IA terá.

---

# 3. HARDWARE ALVO

Desenvolver considerando:

```txt
GPU: GTX 1660 6GB
CPU: Ryzen 5 5500
RAM: 16GB DDR4
SSD: NVMe 1TB
```

O projeto deve ser otimizado para esse hardware.

---

# 4. FILOSOFIA DO PROJETO

## Regra Principal

A IA NÃO É O CENTRO.

O CENTRO É O SISTEMA.

Arquitetura mental:

```txt
Sistema
│
├── Estudos
├── Treino
├── Finanças
├── Hábitos
├── Rotina
├── Notas
├── Relatórios
│
└── IA
```

A IA consulta os módulos.

Os módulos não dependem da IA.

---

# 5. SUPERFÍCIES DE ACESSO

## Dashboard

Painel principal.

Funções:

* visualizar dados
* editar dados
* criar dados
* conversar com IA
* configurar sistema

---

## Telegram

Principal interface diária.

Funções:

* conversa natural
* registro rápido
* acompanhamento diário
* lembretes
* check-ins

---

## Tauri (Futuro)

Transformar dashboard em:

* Desktop App
* Mobile App

---

# 6. PRINCÍPIOS TÉCNICOS

## Simplicidade

Evitar frameworks desnecessários.

---

## Performance

Priorizar velocidade.

---

## Escalabilidade

Arquitetura preparada para crescer.

---

## Manutenção

Código organizado.

---

## Modularização

Cada módulo deve funcionar sozinho.

---

# 7. STACK DEFINITIVA

## Backend

```txt
Python 3.11+
FastAPI
SQLAlchemy Async
Alembic
Pydantic Settings
Redis Async
APScheduler
HTTPX
```

---

## Banco

```txt
PostgreSQL 16
pgvector
Redis
```

---

## IA

```txt
Ollama
```

Modelos:

```txt
llama3.2:3b
mistral:7b-instruct
nomic-embed-text
```

---

## Frontend

```txt
Vite
JavaScript ES Modules
HTML
CSS
Chart.js
WebSocket
```

---

## Infraestrutura

```txt
Docker Compose
Tailscale
```

---

# 8. ESTRATÉGIA DE IA

## Modelo rápido

```txt
llama3.2:3b
```

Usado para:

* comandos
* consultas rápidas
* respostas curtas

---

## Modelo principal

```txt
mistral:7b-instruct
```

Usado para:

* planejamento
* análise
* RAG
* relatórios

---

## Embeddings

```txt
nomic-embed-text
```

---

# 9. ARQUITETURA GERAL

```txt
Telegram
       │
       ▼
 FastAPI API
       │
       ▼
 Services Layer
       │
 ┌─────┼─────┐
 │     │     │
 ▼     ▼     ▼
AI   PostgreSQL Redis
 │
 ▼
Ollama
```

---

# 10. REGRAS DE ARQUITETURA

## PROIBIDO

IA acessando banco diretamente.

---

## CORRETO

```txt
IA
↓
Tool
↓
Service
↓
Database
```

---

# 11. CAMADAS DO SISTEMA

## Presentation Layer

```txt
Dashboard
Telegram
Tauri
```

---

## API Layer

```txt
FastAPI
```

---

## Service Layer

```txt
Business Rules
```

---

## Data Layer

```txt
PostgreSQL
Redis
```

---

## AI Layer

```txt
Router
RAG
Memory
Tools
Prompts
```

---

# 12. ESTRUTURA DE PASTAS

```txt
copiloto/
│
├── backend/
│
├── frontend/
│
├── docker/
│
├── docs/
│
├── scripts/
│
├── backups/
│
└── tests/
```

---

# 13. BACKEND

```txt
backend/
│
├── app/
│
├── core/
│
├── ai/
│
├── modules/
│
├── telegram/
│
├── websocket/
│
├── scheduler/
│
├── db/
│
└── tests/
```

---

# 14. MÓDULOS DE NEGÓCIO

Criar módulos independentes:

```txt
tasks
habits
notes
finance
study
workout
reminders
chat
memory
reports
```

---

# 15. MÓDULO TASKS

Responsável por:

```txt
tarefas
checklists
prioridades
```

---

# 16. MÓDULO HABITS

Responsável por:

```txt
hábitos
vícios
streaks
```

---

# 17. MÓDULO NOTES

Responsável por:

```txt
anotações
markdown
documentos
```

---

# 18. MÓDULO FINANCE

Responsável por:

```txt
receitas
despesas
metas
relatórios
```

---

# 19. MÓDULO STUDY

Responsável por:

```txt
matérias
tópicos
flashcards
revisão
```

---

# 20. MÓDULO WORKOUT

Responsável por:

```txt
treinos
cargas
exercícios
progresso
```

---

# 21. MÓDULO REMINDERS

Responsável por:

```txt
lembretes
agenda
recorrências
```

---

# 22. MÓDULO CHAT

Responsável por:

```txt
conversas
sessões
histórico
```

---

# 23. MÓDULO MEMORY

Responsável por:

```txt
memórias
aprendizado
perfil do usuário
```

---

# 24. MÓDULO REPORTS

Responsável por:

```txt
resumos
análises
relatórios
```

---

# 25. FRONTEND

Estrutura:

```txt
frontend/
│
├── pages/
├── assets/
├── components/
├── modules/
├── services/
└── state/
```

---

# 26. DASHBOARD

Páginas:

```txt
Dashboard
Tasks
Habits
Notes
Finance
Study
Workout
Reminders
Chat
Settings
```

---

# 27. DESIGN

Visual:

```txt
Dark Mode
Moderno
Minimalista
Responsivo
```

Inspirado em:

```txt
Linear
Notion
Raycast
Arc Browser
```

---

# 28. PERFORMANCE

Objetivos:

```txt
Dashboard < 1.5s
API < 200ms
Chat rápido < 4s
```

---

# 29. SEGURANÇA

Tudo configurado por:

```txt
.env
```

Nunca hardcode.

---

# 30. REGRAS PARA O CURSOR

IMPORTANTE:

NÃO IMPLEMENTAR O PROJETO INTEIRO DE UMA VEZ.

Fluxo obrigatório:

```txt
1. Ler este documento.
2. Gerar plano técnico.
3. Validar plano.
4. Implementar Fase 01.
5. Testar Fase 01.
6. Aguardar aprovação.
7. Implementar Fase 02.
8. Testar Fase 02.
9. Aguardar aprovação.
```

NUNCA avançar de fase sem aprovação.

---

# PRÓXIMA PARTE

COPILOTO_PLAN.md
PARTE 2

* Banco de Dados Completo
* Sistema de IA
* Memória Evolutiva
* Telegram Instructor
* RAG
* Knowledge Graph Pessoal
