# COPILOTO_PLAN.md

# PARTE 4 — BACKEND COMPLETO, SEGURANÇA, PERFORMANCE, DEPLOY E ROADMAP

---

# 131. VISÃO GERAL

Esta fase fecha a arquitetura técnica.

Objetivo:

Transformar o projeto em um sistema:

```txt
Estável
Seguro
Escalável
Rápido
Fácil de manter
```

---

# 132. BACKEND CORE

Framework:

```txt
FastAPI
```

Estrutura:

```txt
backend/
│
├── app/
│
├── core/
│
├── db/
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
├── middleware/
│
├── tests/
│
└── main.py
```

---

# 133. PADRÃO DE ARQUITETURA

Utilizar:

```txt
Router
Service
Repository
Model
Schema
```

Fluxo:

```txt
Request
↓
Router
↓
Service
↓
Repository
↓
Database
```

---

# 134. RESPONSABILIDADES

## Router

Responsável por:

```txt
Receber requisição
Validar entrada
Chamar Service
```

---

## Service

Responsável por:

```txt
Regras de negócio
```

---

## Repository

Responsável por:

```txt
Consultas ao banco
```

---

## Model

Responsável por:

```txt
Estrutura do banco
```

---

## Schema

Responsável por:

```txt
Validação Pydantic
```

---

# 135. API REST

Prefixo:

```txt
/api/v1
```

---

Rotas:

```txt
/auth
/tasks
/habits
/notes
/finance
/study
/workout
/reminders
/chat
/memory
/reports
/settings
```

---

# 136. PADRÃO DE RESPOSTA

Sucesso:

```json
{
  "success": true,
  "data": {}
}
```

Erro:

```json
{
  "success": false,
  "error": {}
}
```

---

# 137. AUTENTICAÇÃO

Sistema:

```txt
JWT
```

---

Endpoints:

```txt
/login
/logout
/refresh
/me
```

---

Armazenamento:

```txt
HttpOnly Cookies
```

Preferencialmente.

---

# 138. SEGURANÇA

Obrigatório:

```txt
JWT
Hash de senha
Rate Limit
Logs
Validação
```

---

# 139. HASH

Utilizar:

```txt
bcrypt
```

---

Nunca salvar senha.

---

# 140. RATE LIMIT

Exemplos:

```txt
Login:
5/min

Chat:
60/min

Telegram:
120/min
```

---

# 141. CORS

Configurar:

```txt
origins permitidas
```

via `.env`

---

# 142. MIDDLEWARES

Criar:

```txt
Request Logger
Rate Limit
Error Handler
Auth Middleware
```

---

# 143. LOGS

Utilizar:

```txt
structlog
```

ou

```txt
logging JSON
```

---

Registrar:

```txt
Erros
Tempo resposta
Login
Telegram
IA
```

---

# 144. MONITORAMENTO

Criar endpoint:

```txt
/health
```

---

Retornar:

```json
{
  "api": true,
  "database": true,
  "redis": true,
  "ollama": true
}
```

---

# 145. HEALTH CHECKS

Verificar:

```txt
Postgres
Redis
Ollama
Telegram
```

---

# 146. WEBSOCKET

Criar:

```txt
/ws/chat
```

---

Responsável por:

```txt
Streaming IA
Notificações
Status
```

---

# 147. STREAMING IA

Obrigatório.

---

Fluxo:

```txt
Usuário
↓
WebSocket
↓
Ollama Stream
↓
Frontend
```

---

Mostrar tokens em tempo real.

---

# 148. REDIS

Utilizar para:

```txt
Cache
Sessões
Fila
Contexto curto
```

---

Não utilizar como banco principal.

---

# 149. CACHE

Dashboard:

```txt
60 segundos
```

---

Relatórios:

```txt
5 minutos
```

---

Insights IA:

```txt
15 minutos
```

---

# 150. SCHEDULER

Utilizar:

```txt
APScheduler
```

---

# 151. JOBS

Criar:

```txt
Lembretes
Check-ins
Resumo diário
Resumo semanal
Embeddings
```

---

# 152. CHECK-IN MATINAL

Horário padrão:

```txt
07:00
```

---

Mensagem:

```txt
Bom dia.

Qual é sua prioridade principal hoje?
```

---

# 153. CHECK-IN ALMOÇO

Horário:

```txt
12:00
```

---

Pergunta:

```txt
Como está sua energia?
```

---

# 154. CHECK-IN NOITE

Horário:

```txt
22:00
```

---

Pergunta:

```txt
Qual foi sua principal vitória hoje?
```

---

# 155. RESUMO DIÁRIO

Executar:

```txt
23:00
```

---

Gerar:

```txt
Study Summary
Workout Summary
Finance Summary
Mood Summary
```

---

# 156. RESUMO SEMANAL

Executar:

```txt
Domingo
20:00
```

---

Gerar:

```txt
Insights
Vitórias
Falhas
Plano próxima semana
```

---

# 157. SISTEMA DE EMBEDDINGS

Fila dedicada.

---

Fluxo:

```txt
Nova Nota
↓
Fila
↓
Embedding
↓
Banco
```

---

Não bloquear usuário.

---

# 158. PERFORMANCE IA

Objetivos:

```txt
Resposta inicial:
<2s

Resposta completa:
<8s
```

---

# 159. RAG

Limites:

```txt
3-5 chunks
```

---

Evitar contexto enorme.

---

# 160. MODEL ROUTER

Criar:

```txt
Complexidade baixa
↓
llama3.2:3b

Complexidade alta
↓
mistral:7b
```

---

# 161. OLLAMA

Configuração:

```txt
Streaming ON
Keep Alive ON
```

---

Contexto:

```txt
4096
```

---

# 162. FRONTEND PERFORMANCE

Objetivos:

```txt
Primeira carga <2s
```

---

# 163. LAZY LOADING

Aplicar em:

```txt
Analytics
Study
Finance
Reports
```

---

# 164. PAGINAÇÃO

Obrigatória.

---

Aplicar em:

```txt
Notas
Memórias
Chat
Transações
```

---

# 165. INDEXAÇÃO

Criar índices:

```txt
Datas
UserID
Status
Embeddings
```

---

# 166. BACKUP

Criar scripts:

```txt
backup_db.sh
restore_db.sh
```

---

Backup:

```txt
Diário
```

---

# 167. EXPORTAÇÃO

Permitir exportar:

```txt
Notas
Memórias
Finanças
Estudos
```

---

Formatos:

```txt
JSON
CSV
```

---

# 168. TAILSCALE

Acesso remoto principal.

---

Regra:

```txt
Não expor API pública.
```

---

Acesso:

```txt
Somente Tailscale.
```

---

# 169. HTTPS

Opcional inicialmente.

---

Quando exposto:

```txt
Traefik
Caddy
Nginx
```

---

# 170. TELEGRAM SECURITY

Obrigatório:

```txt
Allowed User ID
```

---

Ignorar qualquer outro usuário.

---

# 171. DASHBOARD SETTINGS

Adicionar:

```txt
Configurações IA
Configurações Telegram
Configurações Memória
Configurações Estudo
Configurações Treino
```

---

# 172. CONFIGURAÇÕES IA

Editar:

```txt
Modelo principal
Modelo rápido
Temperatura
Chunks
```

---

# 173. CONFIGURAÇÕES MEMÓRIA

Editar:

```txt
Auto Learning
Auto Memory
Retention
```

---

# 174. CONFIGURAÇÕES TELEGRAM

Editar:

```txt
Check-ins
Horários
Notificações
```

---

# 175. TESTES

Criar:

```txt
Unitários
Integração
API
```

---

# 176. TESTES OBRIGATÓRIOS

Validar:

```txt
Banco
Redis
Ollama
Telegram
RAG
```

---

# 177. TESTES DE CARGA

Simular:

```txt
1000 mensagens
```

---

Verificar:

```txt
Memória
CPU
Latência
```

---

# 178. ROADMAP V1

Objetivo:

Sistema funcional.

---

Inclui:

```txt
Dashboard
Telegram
IA
Memórias
Estudos
Treino
Finanças
Hábitos
```

---

# 179. ROADMAP V2

Adicionar:

```txt
Tauri
Mobile
SearXNG
Voice
OCR
Calendário
```

---

# 180. VOZ (FUTURO)

Adicionar:

```txt
Whisper
```

---

Funções:

```txt
Áudio → Texto
```

---

# 181. PESQUISA WEB (FUTURO)

Adicionar:

```txt
SearXNG
```

---

Funções:

```txt
Pesquisa local
Pesquisa web
Fontes
```

---

# 182. OCR (FUTURO)

Adicionar:

```txt
Tesseract
```

---

Funções:

```txt
PDF
Imagem
Livro
```

---

# 183. TAURI

Transformar Dashboard em:

```txt
Desktop App
```

---

Mesma base.

---

# 184. APP MOBILE (FUTURO)

Opções:

```txt
Tauri Mobile
PWA
```

---

# 185. IA ANALISTA

Criar agente especializado.

---

Responsável por:

```txt
Análises
Insights
Tendências
```

---

# 186. IA PLANNER

Criar agente especializado.

---

Responsável por:

```txt
Planejamento semanal
Planejamento diário
```

---

# 187. IA REVIEWER

Criar agente especializado.

---

Responsável por:

```txt
Revisão semanal
Revisão mensal
```

---

# 188. IA STUDY COACH

Responsável por:

```txt
ENEM
Medicina
Cronograma
Questões
```

---

# 189. IA WORKOUT COACH

Responsável por:

```txt
Hipertrofia
Progressão
Consistência
```

---

# 190. CRITÉRIOS DE ACEITE FINAIS

Projeto aprovado quando:

```txt
✓ Dashboard funcional
✓ Telegram Instructor funcional
✓ IA funcional
✓ Memória funcional
✓ RAG funcional
✓ Estudos funcionais
✓ Treino funcional
✓ Finanças funcionais
✓ Hábitos funcionais
✓ Relatórios funcionais
✓ Check-ins funcionais
✓ Backups funcionais
✓ Tailscale funcional
```

---

# 191. INSTRUÇÃO FINAL PARA O CURSOR

Leia todas as partes do COPILOTO_PLAN.md.

NÃO implemente tudo de uma vez.

Fluxo obrigatório:

1. Analisar todas as partes.
2. Criar plano técnico detalhado.
3. Identificar dependências.
4. Dividir em fases.
5. Implementar apenas uma fase por vez.
6. Testar.
7. Corrigir.
8. Solicitar aprovação.
9. Avançar para próxima fase.

Nunca pular testes.

Nunca pular validação.

Nunca implementar fases futuras antes da fase atual estar estável.

---

# FIM DA ESPECIFICAÇÃO V1

Versão atual:

```txt
COPILOTO v1
Sistema Operacional Pessoal Inteligente
```

Próxima evolução:

```txt
COPILOTO v2
Memória avançada
Voz
OCR
Pesquisa Web
Mobile
```
