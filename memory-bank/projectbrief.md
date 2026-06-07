# Project Brief: AI CAPTCHA Bypass — Autenticação Procedural
*Version: 1.0*
*Created: 2026-06-07*
*Last Updated: 2026-06-07*

## Project Overview

Repositório acadêmico (PUC Minas) para medir como bots baseados em IA contornam diferentes tipos de CAPTCHA. O trabalho embasa a pesquisa **"Autenticação Procedural: Defesas dinâmicas para resistência a bots em autenticações"**, analisando padrões de automação e preparando comparações entre interfaces estáticas e procedurais.

Fork/adaptação do projeto [ai-captcha-bypass](https://github.com/aydinnyunus/ai-captcha-bypass) (Aydin, 2025) para fins exclusivamente acadêmicos.

## Core Requirements

- Medir taxa de sucesso do bot de IA ao resolver os 5 tipos de CAPTCHA atuais (text, complicated_text, recaptcha_v2, puzzle, audio)
- Registrar cada tentativa com logs estruturados (prompt, resposta, sucesso/falha)
- Implementar servidor local de CAPTCHA customizado (Flask) para testes controlados
- Manter experimentos restritos a demos locais e 2captcha.com/demo (sem sistemas reais)
- Usar Gemini Flash como provider principal (custo zero no momento)

## Success Criteria

- Os 5 tipos de CAPTCHA rodam no Windows com taxa de sucesso mensurável via `solve_logger`
- Servidor Flask local serve CAPTCHAs customizados com parâmetros ajustáveis
- Dados experimentais suficientes para comparar comportamento do bot em cenários controlados
- Documentação clara de setup, execução e análise de resultados

## Scope

### In Scope

- Bot Selenium + IA (Gemini Flash) resolvendo CAPTCHAs em 2captcha demo
- Logging detalhado de tentativas (`logs/solve_log.json`)
- Servidor Flask local com CAPTCHAs customizados
- Ambiente de desenvolvimento Windows
- Testes automatizados (nice-to-have, prioridade média)

### Out of Scope

- Ataques a sistemas de produção ou CAPTCHAs reais fora de demos
- Suporte multiplataforma (Linux/macOS)
- Providers pagos como padrão (OpenAI permanece opcional)
- Dashboard web de visualização de logs

## Timeline

- Milestone 1 — Baseline 2captcha: em andamento (5 tipos funcionais)
- Milestone 2 — Servidor Flask local: a definir
- Milestone 3 — Interface procedural + comparação de métricas: a definir
- Entrega do trabalho acadêmico: a confirmar com orientadora

## Stakeholders

- Ana Beatriz Costa Viana — Autora
- Gustavo Anselmo Santos Silva — Autor
- Prof. Ana Paula — Orientadora

---

*This document serves as the foundation for the project and informs all other memory files.*
