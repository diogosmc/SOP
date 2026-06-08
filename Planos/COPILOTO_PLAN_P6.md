# COPILOTO_PLAN.md

# PARTE 6 — PROJETOS, DECISÕES, VIDA REAL E EXECUÇÃO DE OBJETIVOS

---

# 235. VISÃO GERAL DA PARTE 6

Esta parte transforma o Copiloto em um sistema para gerenciar objetivos grandes da vida.

O sistema não deve controlar apenas:

```txt
tarefas
hábitos
notas
gastos
```

Ele deve ajudar a conduzir projetos reais como:

```txt
Passar em Medicina
Ganhar massa muscular
Melhorar vida financeira
Construir um projeto profissional
Organizar rotina
```

---

# 236. MÓDULO PROJECTS

Criar módulo:

```txt
projects
```

Objetivo:

Gerenciar objetivos grandes divididos em etapas menores.

---

# 237. TIPOS DE PROJETO

Categorias:

```txt
Acadêmico
Financeiro
Físico
Profissional
Pessoal
Saúde
Produtividade
```

---

# 238. EXEMPLO DE PROJETO

```txt
Projeto:
Passar em Medicina

Objetivo:
Aumentar desempenho no ENEM

Áreas:
Matemática
Natureza
Redação
Humanas
Linguagens

Métricas:
Questões por dia
Acertos por área
Tempo de estudo
Simulados
```

---

# 239. TABELA PROJECTS

Criar:

```txt
projects
```

Campos:

```txt
id
user_id
title
description
category
status
priority
start_date
target_date
progress
created_at
updated_at
```

---

# 240. TABELA PROJECT_MILESTONES

Criar:

```txt
project_milestones
```

Campos:

```txt
id
project_id
title
description
status
due_date
progress
created_at
updated_at
```

---

# 241. TABELA PROJECT_ACTIONS

Criar:

```txt
project_actions
```

Campos:

```txt
id
project_id
milestone_id
title
description
status
priority
due_date
linked_task_id
created_at
updated_at
```

---

# 242. SISTEMA DE DECISÕES

Criar módulo:

```txt
decisions
```

Objetivo:

Ajudar o usuário a tomar decisões melhores com base em dados, histórico e objetivos.

---

# 243. EXEMPLOS DE DECISÕES

```txt
Devo estudar agora ou treinar?
Devo comprar esse curso?
Devo mudar meu cronograma?
Devo focar mais em Física ou Matemática?
Devo economizar ou investir nesse mês?
```

---

# 244. TABELA DECISIONS

Criar:

```txt
decisions
```

Campos:

```txt
id
user_id
title
context
options
criteria
recommendation
chosen_option
outcome
created_at
updated_at
```

---

# 245. DECISION ENGINE

Criar módulo:

```txt
Decision Engine
```

Função:

Analisar decisões usando:

```txt
objetivos
dados históricos
prioridades
restrições
riscos
benefícios
```

---

# 246. FORMATO DE DECISÃO

Quando o usuário pedir ajuda para decidir, responder com:

```txt
Contexto
Opções
Critérios
Recomendação
Próximo passo
```

---

# 247. EXEMPLO

Usuário:

```txt
Devo estudar Física ou Biologia hoje?
```

Copiloto:

```txt
Contexto:
Física está com mais dificuldade e menos revisão recente.

Opções:
1. Física — maior impacto agora.
2. Biologia — manutenção.

Recomendação:
Física por 45 minutos.

Próximo passo:
Resolver 10 questões de cinemática.
```

---

# 248. SISTEMA DE METAS AVANÇADO

Criar módulo:

```txt
goals
```

A meta deve poder se conectar com:

```txt
projetos
hábitos
tarefas
estudos
treinos
finanças
```

---

# 249. TABELA GOALS

Campos:

```txt
id
user_id
title
description
category
target_value
current_value
unit
deadline
status
priority
created_at
updated_at
```

---

# 250. RELAÇÃO GOALS COM PROJECTS

Uma meta pode pertencer a um projeto.

Exemplo:

```txt
Projeto:
Passar em Medicina

Meta:
Fazer 900 questões de Natureza em 90 dias
```

---

# 251. EXECUTION ENGINE

Criar módulo:

```txt
Execution Engine
```

Objetivo:

Transformar objetivos grandes em ações pequenas.

---

# 252. FUNÇÕES DO EXECUTION ENGINE

```txt
quebrar meta em etapas
criar tarefas
criar lembretes
gerar cronograma
acompanhar progresso
recalcular plano
```

---

# 253. DAILY PLAN ENGINE

Criar módulo:

```txt
Daily Plan Engine
```

Função:

Gerar plano diário baseado em:

```txt
tarefas pendentes
energia
humor
objetivos
prazos
hábitos
treino
estudo
```

---

# 254. PLANO DIÁRIO

Formato:

```txt
Prioridade 1
Prioridade 2
Prioridade 3
Blocos de tempo
Checklist
```

---

# 255. WEEKLY PLAN ENGINE

Criar módulo:

```txt
Weekly Plan Engine
```

Função:

Gerar plano semanal baseado em:

```txt
metas
falhas da semana anterior
progresso atual
prazos
```

---

# 256. SISTEMA DE REPLANEJAMENTO

Se o usuário falhar, o Copiloto não deve apenas registrar.

Ele deve recalcular.

Exemplo:

```txt
Você não estudou ontem.
Vou redistribuir o conteúdo nos próximos 3 dias.
```

---

# 257. MÓDULO LIFE AREAS

Criar conceito:

```txt
life_areas
```

Áreas:

```txt
Estudo
Treino
Finanças
Saúde
Família
Trabalho
Projetos
Mentalidade
```

---

# 258. BALANCE SCORE

Criar pontuação de equilíbrio.

Exemplo:

```txt
Estudo: 80%
Treino: 70%
Finanças: 55%
Rotina: 60%
```

---

# 259. LIFE DASHBOARD

Criar tela:

```txt
Vida
```

Mostrar:

```txt
Projetos ativos
Metas principais
Equilíbrio por área
Prioridades da semana
Riscos atuais
```

---

# 260. RISK ENGINE

Criar módulo:

```txt
Risk Engine
```

Detectar riscos como:

```txt
muitos dias sem estudar
gastos acima do padrão
queda de treino
hábitos negativos aumentando
rotina desorganizada
```

---

# 261. ALERTAS INTELIGENTES

Exemplo:

```txt
Você está há 5 dias sem revisar Física.
Isso pode prejudicar seu progresso no ENEM.
```

---

# 262. SISTEMA DE COMPROMISSOS

Criar módulo:

```txt
commitments
```

Objetivo:

Registrar compromissos assumidos pelo usuário.

Exemplo:

```txt
Amanhã vou estudar 2h.
Vou treinar 4x essa semana.
Não vou gastar com lanche até sexta.
```

---

# 263. TABELA COMMITMENTS

Campos:

```txt
id
user_id
title
description
category
due_date
status
source
created_at
updated_at
```

---

# 264. ACCOUNTABILITY ENGINE

Criar módulo:

```txt
Accountability Engine
```

Função:

Cobrar gentilmente compromissos.

Exemplo:

```txt
Você disse que estudaria 2h hoje.
Quer começar com 25 minutos agora?
```

---

# 265. SISTEMA DE DECISÕES PASSADAS

O Copiloto deve registrar:

```txt
decisão tomada
motivo
resultado
aprendizado
```

---

# 266. DECISION REVIEW

Após alguns dias, revisar decisão.

Exemplo:

```txt
Você escolheu estudar à noite.
Funcionou melhor que de manhã?
```

---

# 267. SISTEMA DE LIÇÕES APRENDIDAS

Criar:

```txt
lessons_learned
```

Campos:

```txt
id
user_id
source_type
source_id
content
importance
created_at
```

---

# 268. EXEMPLOS DE LIÇÕES

```txt
Planejar o dia à noite melhora consistência.
Treinar antes de estudar aumenta energia.
Celular pela manhã reduz produtividade.
```

---

# 269. LIFE TIMELINE

Criar linha do tempo da vida.

Mostrar eventos importantes:

```txt
metas criadas
projetos iniciados
projetos concluídos
mudanças de rotina
marcos de treino
marcos financeiros
marcos de estudo
```

---

# 270. MÓDULO DE PROJETOS NO DASHBOARD

Criar página:

```txt
Projetos
```

Recursos:

```txt
lista de projetos
progresso
milestones
ações
timeline
relatórios
```

---

# 271. VISUALIZAÇÃO KANBAN

Para projetos:

```txt
Backlog
Em andamento
Aguardando
Concluído
```

---

# 272. IA PROJECT MANAGER

Criar agente:

```txt
Project Manager Agent
```

Funções:

```txt
quebrar projetos
criar milestones
definir próximas ações
revisar progresso
```

---

# 273. IA DECISION ADVISOR

Criar agente:

```txt
Decision Advisor Agent
```

Funções:

```txt
comparar opções
analisar custo-benefício
considerar objetivos
registrar decisão
```

---

# 274. IA LIFE STRATEGIST

Criar agente:

```txt
Life Strategist Agent
```

Função:

Ajudar o usuário a alinhar ações diárias com objetivos maiores.

---

# 275. REGRAS DE SEGURANÇA PARA DECISÕES

A IA não deve decidir pelo usuário.

Ela deve:

```txt
analisar
organizar
recomendar
explicar
```

Mas a escolha final é do usuário.

---

# 276. DECISÕES FINANCEIRAS

A IA deve evitar prometer retorno financeiro.

Responder com:

```txt
organização
análise de orçamento
risco
prioridade
```

---

# 277. DECISÕES DE SAÚDE E TREINO

A IA deve recomendar cautela.

Não prescrever tratamento.

---

# 278. DECISÕES EMOCIONAIS

A IA deve oferecer apoio básico.

Não substituir profissional.

---

# 279. TELEGRAM + PROJETOS

O usuário pode dizer:

```txt
Cria um projeto para passar em Medicina.
```

A IA deve:

```txt
criar projeto
criar milestones
criar primeiras ações
sugerir cronograma
```

---

# 280. TELEGRAM + DECISÕES

Usuário:

```txt
Estou em dúvida se estudo ou treino agora.
```

IA:

```txt
analisa energia
histórico
metas do dia
recomenda
```

---

# 281. TELEGRAM + COMPROMISSOS

Usuário:

```txt
Amanhã vou acordar 7h.
```

IA deve:

```txt
registrar compromisso
criar lembrete opcional
acompanhar amanhã
```

---

# 282. RELATÓRIO DE PROJETOS

Gerar semanalmente:

```txt
projetos ativos
progresso
bloqueios
próximas ações
```

---

# 283. RELATÓRIO DE DECISÕES

Mostrar:

```txt
decisões tomadas
resultados
lições aprendidas
```

---

# 284. PRIORIDADE SUPREMA

Toda ação do sistema deve responder:

```txt
Isso aproxima o usuário dos objetivos principais?
```

---

# 285. CRITÉRIOS DE ACEITE DA PARTE 6

Parte pronta quando:

```txt
✓ Projetos funcionam
✓ Metas avançadas funcionam
✓ Decisões são registradas
✓ Compromissos são acompanhados
✓ Plano diário é gerado
✓ Plano semanal é gerado
✓ Alertas inteligentes funcionam
✓ Dashboard de vida funciona
✓ Telegram entende projetos e decisões
```

---

# FIM DA PARTE 6

Próxima parte opcional:

```txt
PARTE 7 — INSTALAÇÃO, EXECUÇÃO, TESTES, QUALIDADE, DEBUG E MODO PLAN DO CURSOR
```
