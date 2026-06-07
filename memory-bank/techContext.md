# Technical Context: AI CAPTCHA Bypass
*Version: 1.0*
*Created: 2026-06-07*
*Last Updated: 2026-06-07*

## Technology Stack

- **Linguagem:** Python 3.7+
- **Automação de browser:** Selenium 4.x + Mozilla Firefox
- **IA (provider principal):** Google Gemini (`gemini-2.5-flash`) via `google-genai`
- **IA (opcional):** OpenAI GPT-4o via `openai`
- **Processamento de imagem:** Pillow
- **Configuração:** python-dotenv (`.env`)
- **Servidor local (planejado):** Flask + Pillow
- **Testes (planejado):** pytest
- **CI/CD:** não configurado ainda
- **SO alvo:** Windows 10/11

## Development Environment Setup

1. Instalar Python 3.7+ e Mozilla Firefox no Windows
2. Clonar o repositório e criar `.env` a partir de `.env.example`:
   ```
   GOOGLE_API_KEY="..."
   ```
3. Instalar dependências:
   ```bash
   pip install -r requirements.txt
   ```
4. Para Python 3.14+, usar instalação sem fixar versões (ver README)
5. Executar um teste:
   ```bash
   python main.py text --provider gemini --model gemini-2.5-flash
   ```

## Dependencies

- `selenium` — automação do Firefox
- `google-genai` — API Gemini (provider principal)
- `openai` — API OpenAI (opcional)
- `Pillow` — manipulação de imagens e GIFs de sucesso
- `python-dotenv` — variáveis de ambiente
- `webdriver-manager` — gerenciamento de drivers
- `pynput` — interações de input (puzzle)
- `flask` — servidor local de CAPTCHA (a adicionar)
- `pytest` — testes automatizados (a adicionar)

## Technical Constraints

- Apenas Windows como plataforma alvo
- Gemini Flash como provider padrão (gratuito no momento)
- Experimentos limitados a `2captcha.com/demo` e servidor local
- Dependência de API key do Google Gemini
- Firefox obrigatório (geckodriver via Selenium)

## Build and Deployment

- **Build:** não aplicável (script Python)
- **Execução:** `python main.py <tipo> --provider gemini --model gemini-2.5-flash`
- **Deploy:** local apenas; sem pipeline de produção
- **CI/CD:** pytest em GitHub Actions (planejado, nice-to-have)

## Testing Approach

- **Unit Testing:** pytest para `solve_logger`, utilitários em `ai_utils` (planejado)
- **Integration Testing:** smoke tests dos fluxos de CAPTCHA com mocks de IA (planejado)
- **E2E Testing:** execução manual contra 2captcha demo e servidor Flask local
- **Métricas:** `solve_logger.get_summary()` para taxa de sucesso por tipo

---

*This document describes the technologies used in the project and how they're configured.*
