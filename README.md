# Autenticação Procedural: Testes com Bot de CAPTCHA

Repositório de experimentação utilizado como parte do trabalho acadêmico **"Autenticação Procedural: Defesas dinâmicas para resistência a bots em autenticações"**, desenvolvido na disciplina de Trabalho Interdisciplinar da PUC Minas.

## Sobre o Trabalho

Este estudo analisa o comportamento de bots que contornam mecanismos como CAPTCHA e reCAPTCHA, com foco em como eles respondem a interfaces que mudam de forma procedural. A proposta utiliza aprendizado de máquina para memorizar comportamentos padronizados dos bots e altera elementos da interface de forma imprevisível, buscando interromper interações automatizadas e aumentar a eficácia dos processos de autenticação.

**Autores:**
- Ana Beatriz Costa Viana — abcviana@sga.pucminas.br
- Gustavo Anselmo Santos Silva — gustavosilvasocial@gmail.com

**Instituição:** Pontifícia Universidade Católica de Minas Gerais (PUC Minas)

## Objetivo dos Testes

Este repositório contém a ferramenta [AI-powered CAPTCHA bypass](https://github.com/aydinnyunus/ai-captcha-bypass) (AYDIN, 2025), utilizada na etapa experimental do trabalho para:

1. Observar o comportamento de bots baseados em IA ao resolver diferentes tipos de CAPTCHA
2. Identificar quais padrões de interface são explorados durante a resolução dos desafios
3. Analisar como técnicas de visão computacional e automação de interface influenciam o desempenho do bot
4. Avaliar como alterações procedurais na interface impactam a capacidade de automação

> **Nota:** Os experimentos não exploram sistemas reais, apenas ambientes de teste (2captcha.com/demo/).

## Tipos de CAPTCHA Testados

| Tipo | Descrição |
|------|-----------|
| **Text** | Reconhecimento de texto simples |
| **Complicated Text** | Texto com distorção e ruído |
| **reCAPTCHA v2** | Checkbox "Não sou um robô" com seleção de imagens |
| **Puzzle** | Slider puzzle (arrastar peça para posição correta) |
| **Audio** | Transcrição de áudio |

## Pré-requisitos

- Python 3.7+
- Mozilla Firefox
- API Key do Google Gemini (ou OpenAI)

## Instalação e Configuração

1. **Instalar dependências:**
    ```bash
    pip install -r requirements.txt
    ```
    > Se estiver usando Python 3.14+, instale sem fixar versões:
    > ```bash
    > pip install --only-binary :all: openai google-genai Pillow pynput selenium python-dotenv pydantic requests webdriver-manager
    > ```

2. **Configurar API keys:**
    Crie um arquivo `.env` na raiz do projeto:
    ```
    OPENAI_API_KEY="sk-..."
    GOOGLE_API_KEY="..."
    ```
    Obtenha sua chave do Gemini em: https://aistudio.google.com/apikey

## Uso

```bash
# CAPTCHA de texto com Gemini
python main.py text --provider gemini --model gemini-2.5-flash

# CAPTCHA de texto complicado
python main.py complicated_text --provider gemini --model gemini-2.5-flash

# reCAPTCHA v2
python main.py recaptcha_v2 --provider gemini --model gemini-2.5-flash

# Puzzle (slider)
python main.py puzzle --provider gemini --model gemini-2.5-flash

# Áudio
python main.py audio --provider gemini --model gemini-2.5-flash
```

## Como Funciona

1. O script inicia o Firefox via Selenium
2. Navega até a página de demonstração do CAPTCHA
3. Captura screenshots do desafio
4. Envia as imagens para a IA (Gemini/OpenAI) com um prompt específico
5. A IA retorna a solução (texto, coordenadas ou seleções)
6. O script executa a ação no navegador
7. Verifica se o CAPTCHA foi resolvido com sucesso

## Estrutura do Projeto

- `main.py` — Ponto de entrada principal, processa argumentos de linha de comando
- `ai_utils.py` — Interação com APIs de IA (OpenAI e Gemini), definição de prompts
- `puzzle_solver.py` — Lógica específica para resolver CAPTCHA de slider/puzzle
- `solve_logger.py` — Logger que registra cada interação da IA (prompts, respostas, resultados)
- `requirements.txt` — Dependências do projeto
- `logs/solve_log.json` — Registro detalhado de todas as tentativas de resolução
- `successful_solves/` — GIFs de resoluções bem-sucedidas

## Sistema de Logging

O projeto registra automaticamente cada tentativa de resolução em `logs/solve_log.json`, incluindo:
- Timestamp da tentativa
- Tipo de CAPTCHA
- Provider e modelo utilizado
- Prompt enviado à IA
- Resposta retornada pela IA
- Resultado (sucesso/falha)

Para ver um resumo das tentativas:
```bash
python -c "from solve_logger import get_summary; import json; print(json.dumps(get_summary(), indent=2, ensure_ascii=False))"
```

## Criando CAPTCHAs Próprios (Próximos Passos)

É possível criar CAPTCHAs customizados para testar o bot em condições controladas. A ideia é servir um servidor web local que gera desafios com parâmetros ajustáveis.

### Como funciona

1. **Instalar Flask:**
   ```bash
   pip install flask pillow
   ```

2. **Criar um servidor local** (ex: `captcha_server.py`) que:
   - Gera imagens de CAPTCHA de texto com distorção, ruído, rotação variáveis
   - Gera puzzles de slider com posições aleatórias da peça
   - Gera grades de imagens para seleção (estilo reCAPTCHA)
   - Serve as páginas em `http://localhost:5000`

3. **Apontar o bot para o servidor local** em vez do `2captcha.com/demo`

### Variáveis que podem ser controladas

| Variável | Tipo de CAPTCHA | Descrição |
|----------|----------------|-----------|
| Nível de ruído | Texto | Quantidade de linhas/pontos sobre o texto |
| Rotação dos caracteres | Texto | Ângulo de inclinação de cada letra |
| Sobreposição | Texto | Grau de junção entre caracteres |
| Fonte/cor | Texto | Variação visual do texto |
| Posição do slot | Puzzle | Onde a peça deve ser encaixada |
| Formato da peça | Puzzle | Forma do recorte (quadrado, irregular) |
| Quantidade de tiles | Seleção de imagens | Grade 3x3, 4x4, 5x5 |
| Posição dos elementos | Todos | Mover botões, inputs, instruções de lugar |

### Para testar autenticação procedural

O servidor pode alterar dinamicamente entre requisições:
- Posição do campo de input e botão de submit
- Ordem e formato das instruções
- Layout da grade de imagens
- Estilo visual dos elementos (cores, tamanhos, espaçamentos)

Isso permite comparar a taxa de sucesso do bot entre:
- **Interface estática** (baseline) — elementos sempre no mesmo lugar
- **Interface procedural** — elementos mudam a cada carregamento

## Referências

- AYDIN, Y. **AI-powered CAPTCHA bypass: Automating CAPTCHA solving with GPT-4o and Gemini.** 2025. Disponível em: https://aydinnyunus.github.io/2025/12/08/ai-captcha-bypass/
- DINH, N. T.; HOANG, V. T. Recent advances of CAPTCHA security analysis: a short literature review. *Procedia Computer Science*, v. 218, p. 2550–2562, 2023.
- CHANDRA, J. et al. Aura-captcha: A reinforcement learning and GAN-enhanced multi-modal CAPTCHA system. 2025.

## Licença

Este repositório é um fork/adaptação do projeto original de [Yunus Aydin](https://github.com/aydinnyunus/ai-captcha-bypass) para fins exclusivamente acadêmicos e de pesquisa.
