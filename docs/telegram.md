# Telegram — COPILOTO V1

Bot **Instructor**: classifica mensagens, atualiza memória/diário e responde via Ollama.

## Configuração

### 1. Criar bot (BotFather)

1. Abra [@BotFather](https://t.me/BotFather) no Telegram.
2. `/newbot` → escolha nome e username.
3. Copie o **token** para `.env`:
   ```env
   TELEGRAM_ENABLED=true
   TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
   ```

### 2. Obter seu user ID

1. Fale com [@userinfobot](https://t.me/userinfobot) ou [@getidsbot](https://t.me/getidsbot).
2. Copie o ID numérico:
   ```env
   TELEGRAM_ALLOWED_USER_ID=123456789
   ```

Somente esse usuário pode usar o bot (segurança V1).

### 3. Reiniciar backend

O bot inicia automaticamente quando `TELEGRAM_ENABLED=true` e token válido.

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Modo Instructor

Mensagens livres são:

1. Classificadas (estudo, finanças, treino, emocional, etc.)
2. Persistidas em memória/diário quando relevante
3. Respondidas via chat Ollama (modelo fast/main)

Comandos úteis:

- `/start` — boas-vindas
- `/help` — exemplos de uso

## Polling vs webhook

V1 usa **long polling** (sem expor webhook público). Ideal para uso pessoal com Tailscale ou localhost.

## Troubleshooting

| Problema | Verificação |
|----------|-------------|
| Bot não responde | `TELEGRAM_ENABLED=true`, token correto, backend rodando |
| "Não autorizado" | `TELEGRAM_ALLOWED_USER_ID` = seu ID exato |
| IA não responde | Ollama online — veja [ollama.md](ollama.md) |
| Bot não inicia | Logs: `telegram_start_failed`; token inválido |

Ver [troubleshooting.md](troubleshooting.md).
