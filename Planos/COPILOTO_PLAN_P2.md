# COPILOTO_PLAN.md

# PARTE 2 — IA, MEMÓRIA EVOLUTIVA, TELEGRAM INSTRUCTOR E KNOWLEDGE GRAPH

---

# 31. VISÃO GERAL DA IA

A IA do projeto não deve ser tratada como um chatbot.

Ela deve ser tratada como um sistema cognitivo composto por:

```txt
Router
Memory
RAG
Tools
Knowledge Graph
Journal
Reasoning
```

O objetivo é que a IA fique mais inteligente conforme o usuário utiliza o sistema.

---

# 32. FILOSOFIA DA MEMÓRIA

A IA deve lembrar apenas informações úteis.

Ela não deve memorizar tudo.

Ela deve construir conhecimento sobre:

```txt
Objetivos
Hábitos
Rotina
Treino
Estudos
Finanças
Comportamento
Padrões
Preferências
```

---

# 33. ARQUITETURA DA MEMÓRIA

A memória será dividida em 4 camadas.

---

## Camada 1 — Contexto Imediato

Redis

Função:

```txt
últimas mensagens
últimas ações
últimos eventos
```

Tempo:

```txt
24 horas
```

---

## Camada 2 — Histórico Estruturado

PostgreSQL

Função:

```txt
tarefas
treinos
hábitos
estudos
finanças
```

---

## Camada 3 — Memória Semântica

pgvector

Função:

```txt
recordações
preferências
padrões
contexto
```

---

## Camada 4 — Knowledge Graph

Função:

```txt
conectar fatos
```

Exemplo:

```txt
Usuário
↓
Quer Medicina
↓
Estuda ENEM
↓
Dificuldade Física
↓
Melhor horário noite
```

---

# 34. KNOWLEDGE GRAPH PESSOAL

Criar módulo:

```txt
personal_graph
```

---

Objetivo:

Criar representação estruturada do usuário.

---

Entidades:

```txt
Pessoa
Objetivo
Hábito
Rotina
Matéria
Treino
Meta Financeira
Projeto
Preferência
```

---

Relacionamentos:

```txt
quer
gosta
não_gosta
estuda
treina
possui_meta
possui_habito
possui_rotina
```

---

Exemplo:

```txt
Usuário
  └─ quer → Medicina

Usuário
  └─ estuda → Física

Usuário
  └─ prefere → Estudar à noite

Usuário
  └─ objetivo_físico → Hipertrofia
```

---

# 35. TABELA AI_MEMORIES

Criar tabela:

```txt
ai_memories
```

Campos:

```txt
id
user_id
type
content
importance
confidence
source
embedding
created_at
updated_at
expires_at
```

---

Tipos:

```txt
goal
preference
habit
pattern
study
workout
financial
emotional
routine
fact
```

---

# 36. TABELA AI_NOTES

Criar tabela:

```txt
ai_notes
```

Objetivo:

Anotações criadas pela própria IA.

---

Exemplo:

```txt
Usuário apresenta dificuldade recorrente em loops.

Usuário responde melhor quando possui tarefas pequenas.

Usuário procrastina usando celular.
```

---

Campos:

```txt
id
user_id
title
content
category
importance
embedding
created_at
```

---

# 37. DAILY JOURNAL

Criar tabela:

```txt
daily_journal
```

---

Objetivo:

Criar diário automático.

---

Campos:

```txt
id
user_id
date
summary
mood_score
energy_score
productivity_score
study_summary
workout_summary
finance_summary
habit_summary
important_events
```

---

# 38. WEEKLY REVIEW

Criar tabela:

```txt
weekly_reviews
```

---

Objetivo:

Resumo semanal.

---

Campos:

```txt
id
user_id
week_reference
summary
wins
failures
patterns
recommendations
created_at
```

---

# 39. SISTEMA DE EXTRAÇÃO DE MEMÓRIA

Toda mensagem relevante deve passar por:

```txt
Memory Extractor
```

---

Fluxo:

```txt
Mensagem
↓
Classificador
↓
Extrator
↓
Validação
↓
Memória
```

---

Exemplo:

Usuário:

```txt
Quero passar em Medicina.
```

Memória criada:

```txt
Tipo: Goal

Conteúdo:
Objetivo acadêmico é Medicina.

Importância:
10
```

---

# 40. CONSOLIDAÇÃO DE MEMÓRIAS

Evitar duplicação.

---

Errado:

```txt
Quero Medicina.
Quero Medicina.
Quero Medicina.
```

---

Correto:

```txt
Atualizar memória existente.
```

---

# 41. DETECÇÃO DE PADRÕES

A IA deve detectar:

```txt
horários
procrastinação
produtividade
rotina
humor
hábitos
```

---

Exemplo:

```txt
Usuário estuda melhor entre 19h e 22h.
```

Criar memória:

```txt
study_pattern
```

---

# 42. TELEGRAM INSTRUCTOR

O Telegram será o principal ponto de contato.

---

Ele deve funcionar como:

```txt
mentor
instrutor
diário
copiloto
```

---

Não depender de comandos.

---

# 43. MODO CONVERSA NATURAL

Exemplos:

```txt
Acordei.

Vou treinar.

Gastei 30 reais.

Hoje não consegui estudar.

Estou cansado.

Estudei Python.
```

---

A IA deve entender tudo automaticamente.

---

# 44. CLASSIFICADOR DE MENSAGENS

Criar:

```python
classify_message()
```

---

Retorno:

```json
{
  "intent": "",
  "entities": {},
  "actions": [],
  "save_memory": true
}
```

---

# 45. INTENÇÕES SUPORTADAS

```txt
general_chat
study_log
workout_log
expense_log
habit_log
goal_update
emotional_checkin
reminder_creation
task_creation
question
```

---

# 46. EXTRAÇÃO DE ENTIDADES

Exemplo:

Mensagem:

```txt
Gastei 25 reais no almoço.
```

Retorno:

```json
{
  "amount": 25,
  "category": "alimentacao"
}
```

---

# 47. APRENDIZADO AUTOMÁTICO

A IA deve aprender:

```txt
objetivos
rotina
preferências
dificuldades
```

---

Sem necessidade de comandos.

---

# 48. CHECK-INS AUTOMÁTICOS

Criar sistema de check-ins.

---

Horários padrão:

```txt
07:00
12:00
18:00
22:00
```

---

Configurável.

---

# 49. CHECK-IN MATINAL

Mensagem:

```txt
Bom dia.

Qual é a prioridade principal de hoje?
```

---

# 50. CHECK-IN NOTURNO

Mensagem:

```txt
Como foi seu dia?

Qual foi sua principal vitória?
```

---

# 51. RESUMO DIÁRIO

Gerar automaticamente.

---

Exemplo:

```txt
Você estudou 2h.

Treinou peito.

Gastou R$42.

Concluiu 80% da rotina.
```

---

# 52. RESUMO SEMANAL

Gerar automaticamente.

---

Exemplo:

```txt
Você treinou 5 vezes.

Estudou 12 horas.

Economizou R$180.

Melhorou consistência.
```

---

# 53. RAG

Toda informação relevante deve ser indexada.

---

Fontes:

```txt
Notas
Estudos
Conversas
Memórias
Documentos
```

---

# 54. CHUNKING

Utilizar:

```txt
500 a 900 caracteres
```

---

Overlap:

```txt
100 caracteres
```

---

# 55. BUSCA SEMÂNTICA

Pergunta:

```txt
O que eu estava estudando mês passado?
```

---

RAG deve recuperar:

```txt
Sessões
Notas
Memórias
```

---

# 56. CONTEXTO DA IA

Toda resposta deve considerar:

```txt
Memórias
RAG
Histórico recente
Objetivos
```

---

# 57. PERFIL DO USUÁRIO

Criar entidade:

```txt
user_profile
```

---

Campos:

```txt
objetivos
preferências
rotina
perfil_estudo
perfil_treino
perfil_financeiro
```

---

# 58. PERFIL DE ESTUDO

Exemplo:

```txt
Objetivo:
Medicina

Método:
Questões

Dificuldade:
Física

Melhor horário:
Noite
```

---

# 59. PERFIL DE TREINO

Exemplo:

```txt
Objetivo:
Hipertrofia

Peso:
65kg

Altura:
1.75m

Treina:
5x semana
```

---

# 60. PERFIL FINANCEIRO

Exemplo:

```txt
Meta:
Reserva financeira

Gasto recorrente:
Alimentação
```

---

# 61. PROMPT MESTRE DA IA

A IA deve agir como:

```txt
mentor
organizador
conselheiro
instrutor
analista
```

---

Nunca como:

```txt
médico
psicólogo
advogado
consultor financeiro profissional
```

---

Ela pode:

```txt
orientar
motivar
organizar
explicar
```

---

Ela não pode:

```txt
diagnosticar
prescrever
substituir profissionais
```

---

# 62. REGRAS DE RESPOSTA

Telegram:

```txt
curto
direto
até 3 parágrafos
```

---

Dashboard:

```txt
mais detalhado
```

---

# 63. DASHBOARD DE MEMÓRIAS

Criar página:

```txt
Memórias da IA
```

---

Mostrar:

```txt
O que a IA sabe
```

---

Permitir:

```txt
editar
apagar
exportar
```

---

# 64. CONFIGURAÇÕES

Adicionar:

```txt
Auto Learning
Auto Memory
Daily Journal
Weekly Reviews
Telegram Instructor
```

---

# 65. CRITÉRIOS DE ACEITE

A Parte 2 será considerada pronta quando:

```txt
✓ Memórias funcionarem
✓ Telegram Instructor funcionar
✓ Journal funcionar
✓ Weekly Review funcionar
✓ RAG funcionar
✓ Knowledge Graph funcionar
✓ Perfil do usuário funcionar
```

---

# PRÓXIMA PARTE

COPILOTO_PLAN.md
PARTE 3

* Dashboard Completo
* UX/UI Premium
* Finanças Inteligentes
* Estudos Inteligentes
* Treino Inteligente
* Hábitos e Vícios
* Sistema de Metas
* Analytics e Relatórios
