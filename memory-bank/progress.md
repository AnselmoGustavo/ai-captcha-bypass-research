# Progress Tracker: AI CAPTCHA Bypass
*Version: 1.0*
*Created: 2026-06-07*
*Last Updated: 2026-06-07*

## Project Status

Overall Completion: ~45%

## What Works

- **Text CAPTCHA:** funcional — 2captcha demo, Gemini/OpenAI
- **Complicated Text CAPTCHA:** funcional — até 3 tentativas
- **reCAPTCHA v2:** funcional — seleção de tiles com ThreadPool
- **Puzzle (slider):** funcional — GeeTest com correção iterativa
- **Audio CAPTCHA:** funcional — transcrição via IA
- **Logging:** funcional — `logs/solve_log.json` + `get_summary()`
- **GIFs de sucesso:** funcional — salvos em `successful_solves/`

## What's In Progress

- **Baseline de métricas:** 0% — rodar bateria completa e documentar taxas
- **Servidor Flask local:** 0% — planejado no README, não implementado

## What's Left To Build

- **captcha_server.py:** ALTA — CAPTCHAs customizados com parâmetros variáveis
- **Interface procedural:** ALTA — alteração dinâmica de layout entre requisições
- **Testes automatizados (pytest):** MÉDIA — nice-to-have confirmado
- **Comparação estático vs. procedural:** ALTA — depende do servidor Flask
- **CI (GitHub Actions):** BAIXA — opcional

## Known Issues

- **Python 3.14+:** BAIXA — requirements com versões fixas podem falhar; workaround no README
- **Custo OpenAI:** INFO — provider secundário; Gemini é o padrão
- **Timeline acadêmica:** INFO — prazo não definido ainda

## Milestones

- **Baseline 2captcha (5 tipos):** em andamento — PARCIAL
- **Servidor Flask local:** a definir — NÃO INICIADO
- **Experimento procedural:** a definir — NÃO INICIADO
- **Entrega acadêmica:** a confirmar — PENDENTE

---

*This document tracks what works, what's in progress, and what's left to build.*
