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

O bot suporta dois modos: **2captcha** (padrão, demos online) e **local** (CAPTCHAs seus via Flask).

### Modo 2captcha (padrão — comportamento original)

Não é necessário passar `--target`. Todos os comandos abaixo continuam funcionando como antes:

```bash
# CAPTCHA de texto
python main.py text --provider gemini --model gemini-2.5-flash

# CAPTCHA de texto complicado
python main.py complicated_text --provider gemini --model gemini-2.5-flash

# reCAPTCHA v2
python main.py recaptcha_v2 --provider gemini --model gemini-2.5-flash

# Puzzle (slider)
python main.py puzzle --provider gemini --model gemini-2.5-flash

# Áudio
python main.py audio --provider gemini --model gemini-2.5-flash

# Com documentação do raciocínio da IA (opcional)
python main.py text --provider gemini --model gemini-2.5-flash --explain
```

### Modo local (CAPTCHAs customizados)

**Terminal 1** — subir o servidor:
```bash
python captcha_server.py
```

**Terminal 2** — rodar o bot contra o CAPTCHA local:
```bash
# CAPTCHA padrão (sem distorção)
python main.py text --target local --provider gemini --model gemini-2.5-flash

# CAPTCHA com parâmetros customizados (via URL)
python main.py text --target local --url "http://127.0.0.1:5000/text?noise=3&rotation=20&length=6&seed=42" --provider gemini --model gemini-2.5-flash
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

- `main.py` — Ponto de entrada principal (`--target 2captcha|local`)
- `captcha_server.py` — Servidor Flask de CAPTCHAs customizados
- `captcha_generators/text_captcha.py` — Gera imagens de CAPTCHA com parâmetros variáveis
- `templates/text_captcha.html` — Página HTML com DOM estável para o bot
- `run_experiments.py` — Roda bateria de testes automatizados
- `failure_report.py` — Relatório de taxa de falha por parâmetro
- `experiments/text_variants.json` — Matriz de variantes para experimentos
- `ai_utils.py` — Interação com APIs de IA (OpenAI e Gemini), definição de prompts
- `puzzle_solver.py` — Lógica específica para resolver CAPTCHA de slider/puzzle
- `solve_logger.py` — Logger que registra cada interação da IA (prompts, respostas, raciocínio, resultados)
- `reasoning_utils.py` — Segunda chamada à API para documentar o raciocínio da IA
- `requirements.txt` — Dependências do projeto
- `logs/solve_log.json` — Registro detalhado de todas as tentativas de resolução
- `successful_solves/` — GIFs de resoluções bem-sucedidas

## Sistema de Logging

O projeto registra automaticamente cada tentativa de resolução em `logs/solve_log.json`, incluindo:
- Timestamp da tentativa
- ID da sessão (`session_id`)
- Tipo de CAPTCHA
- Provider e modelo utilizado
- Prompt enviado à IA
- Resposta retornada pela IA
- Resultado (sucesso/falha)
- **Raciocínio da IA** (somente com `--explain`)

Com a flag `--explain`, cada passo gera uma 2ª chamada à API pedindo explicação em português, e ao final é criado `logs/reasoning_TIMESTAMP_TIPO.md`.

```bash
python main.py text --provider gemini --model gemini-2.5-flash --explain
```

> **Nota:** Com `--explain`, cada passo usa 2 chamadas à API. No reCAPTCHA v2, cada tile também gera uma explicação.

Para ver um resumo das tentativas:
```bash
python -c "from solve_logger import get_summary; import json; print(json.dumps(get_summary(), indent=2, ensure_ascii=False))"
```

## CAPTCHAs Customizados — Laboratório Local

O servidor Flask gera CAPTCHAs de texto com parâmetros controláveis, para descobrir **onde a IA mais erra** e desenhar defesas em cima disso.

### 1. Criar um CAPTCHA (via URL)

Abra no navegador ou passe a URL para o bot. Cada parâmetro na query string altera a dificuldade:

| Parâmetro | Padrão | Descrição |
|-----------|--------|-----------|
| `noise` | 0 | Ruído visual (linhas e pontos sobre o texto) |
| `rotation` | 0 | Rotação máxima por caractere (graus) |
| `overlap` | 0 | Sobreposição entre caracteres |
| `length` | 5 | Quantidade de caracteres |
| `font_size` | 36 | Tamanho da fonte |
| `char_set` | alnum | `alnum`, `mixed_case` ou `symbols` (O/0/l/1) |
| `bg_color` | #f0f0f0 | Cor de fundo |
| `fg_color` | #1a1a1a | Cor do texto |
| `wave` | 0 | Distorção ondulada vertical |
| `seed` | aleatório | Fixa a imagem para reprodutibilidade |

**Exemplos no navegador:**
```
http://127.0.0.1:5000/text
http://127.0.0.1:5000/text?noise=3&rotation=20
http://127.0.0.1:5000/text?char_set=symbols&length=6&noise=2
http://127.0.0.1:5000/text?noise=4&rotation=30&overlap=2&seed=42
```

**Bot resolver o mesmo CAPTCHA:**
```bash
python main.py text --target local --url "http://127.0.0.1:5000/text?noise=4&rotation=30&seed=42" --provider gemini --model gemini-2.5-flash
```

### 2. Rodar experimentos em lote

Com o servidor ativo, execute sweeps definidos em `experiments/text_variants.json`:

```bash
# Todos os sweeps (noise, rotation, overlap, length)
python run_experiments.py --start-server

# Apenas variação de ruído, 3 tentativas por variante
python run_experiments.py --start-server --sweep noise_sweep --trials 3
```

O flag `--start-server` sobe o Flask automaticamente. Sem ele, rode `python captcha_server.py` em outro terminal antes.

Resultados em `logs/experiments/run_TIMESTAMP.json`.

### 3. Gerar relatório de falhas

```bash
python failure_report.py --experiment logs/experiments/run_TIMESTAMP.json
```

Saída:
- `logs/reports/failure_analysis_TIMESTAMP.md` — taxa de sucesso por variante e por eixo
- `logs/reports/failure_analysis_TIMESTAMP.csv` — dados para gráficos

O relatório lista as **variantes com menor taxa de sucesso**, indicando onde a IA é mais vulnerável (ex.: `rotation=30` derruba a taxa).

### 4. Editar variantes de experimento

Edite `experiments/text_variants.json` para adicionar novos sweeps:

```json
{
  "name": "wave_sweep",
  "fixed": { "noise": 1, "rotation": 0 },
  "vary": "wave",
  "values": [0, 1, 2, 3]
}
```

### Compatibilidade

Os CAPTCHAs do **2captcha continuam funcionando** sem nenhuma alteração nos comandos. O modo local (`--target local`) é opcional e, por enquanto, suporta apenas `captcha_type=text`.

## Referências

- AYDIN, Y. **AI-powered CAPTCHA bypass: Automating CAPTCHA solving with GPT-4o and Gemini.** 2025. Disponível em: https://aydinnyunus.github.io/2025/12/08/ai-captcha-bypass/
- DINH, N. T.; HOANG, V. T. Recent advances of CAPTCHA security analysis: a short literature review. *Procedia Computer Science*, v. 218, p. 2550–2562, 2023.
- CHANDRA, J. et al. Aura-captcha: A reinforcement learning and GAN-enhanced multi-modal CAPTCHA system. 2025.

## Licença

Este repositório é um fork/adaptação do projeto original de [Yunus Aydin](https://github.com/aydinnyunus/ai-captcha-bypass) para fins exclusivamente acadêmicos e de pesquisa.
