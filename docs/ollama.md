# Ollama — COPILOTO V1

Configuração de IA local via [Ollama](https://ollama.com).

## Modelos recomendados (GTX 1660 · 6 GB VRAM)

| Papel | Modelo | Uso |
|-------|--------|-----|
| Fast | `qwen3:4b` | Chat curto, respostas rápidas |
| Main | `mistral:7b` | Análises e mensagens complexas |
| Embed | `nomic-embed-text` | RAG e busca semântica (768 dims) |

Instalação:

```bash
ollama serve
ollama pull qwen3:4b
ollama pull mistral:7b
ollama pull nomic-embed-text
ollama list
```

## Variáveis `.env`

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL_FAST=qwen3:4b
OLLAMA_MODEL_MAIN=mistral:7b
OLLAMA_MODEL_EMBED=nomic-embed-text
OLLAMA_CONTEXT_SIZE=4096
OLLAMA_KEEP_ALIVE=5m
OLLAMA_TIMEOUT_SECONDS=45
```

### keep_alive

Mantém o modelo carregado na VRAM por `5m` após o último uso. Reduz latência entre mensagens consecutivas. Em máquinas com pouca VRAM, use `2m` ou deixe o Ollama descarregar (`0`).

### num_ctx

Enviado como `options.num_ctx` (padrão 4096). Se faltar VRAM, reduza para `2048`.

## Roteamento automático

O backend escolhe **fast** ou **main** conforme tamanho e palavras-chave da mensagem (`app/ai/router.py`). Modelo main só é usado quando necessário.

## Ollama remoto (Tailscale)

Se Ollama roda em outra máquina na rede Tailscale:

```env
OLLAMA_BASE_URL=http://100.x.x.x:11434
```

Garanta que o Ollama escute em `0.0.0.0:11434` na máquina host.

## Troubleshooting

| Problema | Solução |
|----------|---------|
| Out of memory | Use só `llama3.2:3b`; reduza `OLLAMA_CONTEXT_SIZE` |
| Lento no 7B | Normal na GTX 1660; prefira fast para tarefas simples |
| Embed falha | `ollama pull nomic-embed-text` |
| Timeout | Aumente `OLLAMA_TIMEOUT_SECONDS` ou use modelo menor |
| Health false | `curl http://localhost:11434/api/tags` |

Ver também [troubleshooting.md](troubleshooting.md).
