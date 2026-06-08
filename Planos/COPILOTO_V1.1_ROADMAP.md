# COPILOTO V1.1 — ROADMAP ESTRATÉGICO

## Estado Atual da V1

A versão V1 está concluída e funcional.

### Infraestrutura

* FastAPI
* PostgreSQL + pgvector
* Redis
* Ollama
* Docker
* Alembic
* JWT
* WebSocket
* Scheduler
* Telegram Bot

### IA

* Chat
* Streaming
* RAG
* Memória Evolutiva
* Daily Journal
* Classificador de mensagens
* Router de modelos
* Ollama local

### Módulos

* Tasks
* Habits
* Notes
* Finance
* Study
* Workout
* Reports
* Analytics
* Reminders

### Interface

* Dashboard
* Sidebar
* Dark Mode
* Responsivo
* Lazy Loading
* Cache

---

# Fase 25 — Hardening

Antes da V1.1 o sistema deve passar por uso real.

Objetivo:

Transformar uma aplicação funcional em uma aplicação confiável.

---

## Dogfooding

Usar o sistema por 15 a 30 dias.

Utilizar diariamente:

* Telegram
* Dashboard
* Finanças
* Estudos
* Treino
* Notas
* Tarefas
* Hábitos

Registrar:

* Bugs
* Lentidões
* Fluxos ruins
* Campos faltando
* Funcionalidades pouco utilizadas

---

## Testes de Estabilidade

Validar:

### Concorrência

* múltiplas abas
* múltiplos chats
* websocket simultâneo

### Banco

* backups
* restore
* migrations

### Ollama

* queda do serviço
* troca de modelos
* falta de memória

### Telegram

* reinício automático
* perda de conexão
* mensagens duplicadas

---

# Evolução da Arquitetura da IA

Arquitetura atual:

Usuário
↓
Chat
↓
Memory
↓
RAG
↓
LLM

---

Arquitetura desejada:

Usuário
↓
Classifier
↓
Router
↓
Tools
↓
Memory
↓
RAG
↓
LLM

---

## Benefícios

Menos tokens.

Menos custo computacional.

Respostas mais rápidas.

Maior automação.

Menor dependência da LLM.

---

# Agente Executivo

Objetivo:

Transformar o Copiloto de registrador para mentor ativo.

---

## Rotina Diária

Todo dia:

07:00

O sistema analisa:

* tarefas
* hábitos
* estudos
* treino
* finanças
* metas

E envia:

"Plano do Dia"

via Telegram.

---

## Exemplo

Bom dia.

Prioridades:

1. Revisar Física
2. Resolver 20 questões de Biologia
3. Treino A
4. Registrar gastos do dia

Meta principal:
Passar em Medicina.

---

# Check-ins Inteligentes

Hoje:

Como está seu dia?

---

V1.1:

Você disse ontem que estudaria Física.

Conseguiu cumprir?

---

Você registrou treino há 4 dias.

Pretende treinar hoje?

---

Você está próximo da meta semanal de estudos.

Faltam apenas 45 minutos.

---

# Sistema de Objetivos Globais

Criar entidade:

Goal

Campos:

* título
* descrição
* prioridade
* prazo
* progresso
* status

---

Exemplos

* Passar em Medicina
* Ganhar Massa Muscular
* Melhorar Inglês
* Construir Negócio

---

# Sistema de Prioridade Global

Toda ação do usuário recebe score.

Pergunta:

Isto contribui para qual objetivo?

---

Exemplo

Estudar Física

→ Passar em Medicina

Treino

→ Ganhar Massa Muscular

Curso de Inglês

→ Melhorar Inglês

---

Resultado:

A IA passa a entender:

* importância
* urgência
* alinhamento

de cada ação.

---

# Projetos

Nova entidade:

Project

Campos:

* nome
* descrição
* objetivo relacionado
* progresso
* status
* prioridade
* data início
* data conclusão

---

Exemplos

Projeto ENEM 2026

Projeto Shape 80kg

Projeto Inglês Fluente

Projeto SaaS

---

# Sistema de Decisões

Nova entidade:

Decision

Campos:

* problema
* opções
* prós
* contras
* decisão tomada
* resultado posterior

---

Exemplos

Comprar notebook.

Trocar emprego.

Fazer curso.

Escolher faculdade.

---

Objetivo:

Criar histórico de decisões.

A IA aprende:

* padrões
* erros
* acertos

do usuário.

---

# Memória Estratégica

Separar memória em camadas.

## Curto Prazo

Contexto dos últimos dias.

---

## Médio Prazo

Hábitos.

Rotina.

Estudos.

Treinos.

---

## Longo Prazo

Objetivos.

Projetos.

Decisões.

Preferências.

Valores.

---

# Futuro — V2

## Aplicativo Desktop

Tauri 2.0

---

## Aplicativo Mobile

Flutter ou Tauri Mobile

---

## Voz

Whisper

TTS local

Conversação por voz.

---

## OCR

Extração de PDFs.

Livros.

Anotações.

---

## Visão Computacional

Captura de tela.

Análise automática.

Monitoramento de produtividade.

---

# Meta Final

Transformar o Copiloto em:

* Segundo cérebro
* Sistema operacional pessoal
* Mentor digital
* Central de produtividade
* Assistente executivo pessoal

Executando localmente.

Sem depender de APIs externas.

Com total controle dos dados.

---

# Métrica de Sucesso

O sistema deixa de ser apenas um dashboard.

Passa a:

* Organizar
* Acompanhar
* Cobrar
* Orientar
* Priorizar
* Evoluir junto com o usuário
