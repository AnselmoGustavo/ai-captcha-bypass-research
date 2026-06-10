# Autenticação Procedural: Testes com Bot de CAPTCHA

Repositório de experimentação utilizado como parte do trabalho acadêmico **"Autenticação Procedural: Defesas dinâmicas para resistência a bots em autenticações"**, desenvolvido na disciplina de Trabalho Interdisciplinar da PUC Minas.

## Sobre o Trabalho

Este estudo analisa os padrões de falha de bots baseados em IA ao resolver diferentes tipos de CAPTCHA, com foco em identificar quais variações visuais e estruturais comprometem a capacidade de automação. Os dados coletados servem para avaliar a **viabilidade** de uma autenticação procedural — que alteraria elementos da interface de forma imprevisível para resistir a bots — como proposta de defesa para trabalhos futuros.

**Autores:**
- Ana Beatriz Costa Viana — abcviana@sga.pucminas.br
- Gustavo Anselmo Santos Silva — gustavosilvasocial@gmail.com

**Instituição:** Pontifícia Universidade Católica de Minas Gerais (PUC Minas)

## Objetivo dos Testes

Este repositório contém a ferramenta [AI-powered CAPTCHA bypass](https://github.com/aydinnyunus/ai-captcha-bypass) (AYDIN, 2025), utilizada na etapa experimental do trabalho para:

1. Observar o comportamento de bots baseados em IA ao resolver diferentes tipos de CAPTCHA
2. Identificar quais parâmetros visuais (ruído, rotação, oclusão, sobreposição) causam falhas e em que proporção
3. Analisar o raciocínio da IA nas tentativas falhas para entender os pontos de ruptura
4. Produzir evidências empíricas que fundamentem a viabilidade de uma defesa procedural

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

- Python 3.12 (recomendado — 3.14+ não tem wheels para Pillow/pydantic)
- Mozilla Firefox
- API Key do Google Gemini (ou OpenAI)

> Para instalar o Python 3.12 sem baixar instalador manualmente:
> ```bash
> winget install Python.Python.3.12
> ```

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
# Texto simples (padrão, sem distorção)
python main.py text --target local --provider gemini --model gemini-2.5-flash

# Texto simples com parâmetros customizados
python main.py text --target local --url "http://127.0.0.1:5000/text?noise=3&rotation=20&length=6&seed=42" --provider gemini --model gemini-2.5-flash

# Texto distorcido (preset difícil: noise=3, rotation=25, occlusion=2, wave=2)
python main.py complicated_text --target local --provider gemini --model gemini-2.5-flash

# Texto distorcido com parâmetros customizados
python main.py complicated_text --target local --url "http://127.0.0.1:5000/complicated_text?noise=5&rotation=35&occlusion=3&seed=42" --provider gemini --model gemini-2.5-flash
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
- `captcha_server.py` — Servidor Flask de CAPTCHAs customizados (rotas: `/text`, `/complicated_text`)
- `captcha_generators/text_captcha.py` — Gera imagens de CAPTCHA com parâmetros variáveis; expõe `DEFAULT_VARIANT`, `COMPLICATED_DEFAULT_VARIANT`, `parse_variant`, `parse_variant_complicated`, `check`
- `templates/text_captcha.html` — Página HTML com DOM estável para o bot (IDs: `captcha-image`, `captcha-input`, `captcha-submit`, `captcha-result`)
- `run_tests.py` — Bateria completa por tipo de CAPTCHA (tabela de taxa de sucesso)
- `run_experiments.py` — Sweep de um parâmetro por vez (`--captcha-type text|complicated_text`, `--sweep <nome>`)
- `failure_report.py` — Relatório de taxa de falha por parâmetro
- `plot_results.py` — Gera gráficos PNG a partir dos logs (taxa de sucesso, tempo)
- `experiments/text_variants.json` — Matriz de variantes para experimentos
- `ai_utils.py` — Interação com APIs de IA (OpenAI e Gemini), definição de prompts
- `puzzle_solver.py` — Lógica específica para resolver CAPTCHA de slider/puzzle
- `solve_logger.py` — Logger que registra cada interação da IA (prompts, respostas, raciocínio, resultados)
- `reasoning_utils.py` — Segunda chamada à API para documentar o raciocínio da IA
- `requirements.txt` — Dependências do projeto
- `logs/solve_log.json` — Registro detalhado de todas as tentativas de resolução
- `successful_solves/` — GIFs de resoluções bem-sucedidas
- `failed_solves/` — GIFs de diagnósticos de tentativas que falharam

## Sistema de Logging

O projeto registra automaticamente cada tentativa de resolução em `logs/solve_log.json`, incluindo:
- Timestamp da tentativa
- ID da sessão (`session_id`)
- Tipo de CAPTCHA
- Provider e modelo utilizado
- Prompt enviado à IA
- Resposta retornada pela IA
- Raciocínio da IA (capturado em todas as execuções)
- Resultado (sucesso/falha)

### Raciocínio automático em falhas

O raciocínio da IA é capturado em **toda** execução (segunda chamada à API por passo). O relatório `logs/reasoning_TIMESTAMP_TIPO.md` é gerado **automaticamente** sempre que o CAPTCHA falha — sem precisar de flags extras.

A flag `--explain` força a geração do relatório também em casos de sucesso (útil para documentação acadêmica):

```bash
python main.py text --provider gemini --model gemini-2.5-flash --explain
```

> **Nota:** Cada passo usa 2 chamadas à API (resposta + raciocínio). No reCAPTCHA v2, cada tile também gera uma chamada de raciocínio.

O projeto também salva GIFs de diagnóstico em `failed_solves/` quando a resolução falha, além dos GIFs de sucesso em `successful_solves/`.

Para ver um resumo das tentativas:
```bash
python -c "from solve_logger import get_summary; import json; print(json.dumps(get_summary(), indent=2, ensure_ascii=False))"
```

## CAPTCHAs Customizados — Laboratório Local

O servidor Flask gera CAPTCHAs de texto com parâmetros controláveis, para descobrir **onde a IA mais erra** e desenhar defesas em cima disso.

### 1. Criar um CAPTCHA (via URL)

Abra no navegador ou passe a URL para o bot. Cada parâmetro na query string altera a dificuldade:

| Parâmetro | Padrão (`text`) | Padrão (`complicated_text`) | Descrição |
|-----------|--------|-----------|-----------|
| `noise` | 0 | 3 | Ruído visual (linhas e pontos sobre o texto) |
| `rotation` | 0 | 25 | Rotação máxima por caractere (graus) |
| `overlap` | 0 | 1 | Sobreposição entre caracteres |
| `occlusion` | 0 | 2 | Linhas horizontais cruzando o texto |
| `wave` | 0 | 2 | Distorção ondulada vertical |
| `length` | 5 | 6 | Quantidade de caracteres |
| `font_size` | 36 | 36 | Tamanho da fonte |
| `char_set` | alnum | mixed_case | `alnum`, `mixed_case` ou `symbols` (O/0/l/1) |
| `bg_color` | #f0f0f0 | #e8e8e8 | Cor de fundo |
| `fg_color` | #1a1a1a | #2a2a2a | Cor do texto |
| `seed` | aleatório | aleatório | Fixa a imagem para reprodutibilidade |

**Exemplos no navegador:**
```
# Texto simples
http://127.0.0.1:5000/text
http://127.0.0.1:5000/text?noise=3&rotation=20
http://127.0.0.1:5000/text?char_set=symbols&length=6&noise=2
http://127.0.0.1:5000/text?noise=4&rotation=30&overlap=2&seed=42

# Texto distorcido (preset difícil, parâmetros sobrescrevíveis)
http://127.0.0.1:5000/complicated_text
http://127.0.0.1:5000/complicated_text?occlusion=3&rotation=35&seed=42
```

**Bot resolver o mesmo CAPTCHA:**
```bash
python main.py text --target local --url "http://127.0.0.1:5000/text?noise=4&rotation=30&seed=42" --provider gemini --model gemini-2.5-flash

python main.py complicated_text --target local --url "http://127.0.0.1:5000/complicated_text?occlusion=3&rotation=35&seed=42" --provider gemini --model gemini-2.5-flash
```

### 2. Bateria completa de testes (`run_tests.py`)

Roda múltiplos tipos de CAPTCHA em sequência e exibe uma tabela de taxa de sucesso:

```bash
# Locais (text + complicated_text) — sobe servidor automaticamente
python run_tests.py --start-server

# Escolher tipos e número de trials
python run_tests.py --start-server --types text complicated_text --trials 5

# Contra o 2captcha (sem servidor local)
python run_tests.py --target 2captcha --types text recaptcha_v2 puzzle --trials 2
```

Resultados em `logs/tests/test_TIMESTAMP.json`.

### 3. Sweeps por parâmetro (`run_experiments.py`)

Varia um parâmetro de dificuldade por vez para medir o impacto na taxa de sucesso:

```bash
# Sweep de ruído no texto simples
python run_experiments.py --start-server --sweep noise_sweep

# Sweep de oclusão no texto distorcido (complicated_text)
python run_experiments.py --start-server --captcha-type complicated_text --sweep occlusion_sweep --trials 3

# Outros sweeps disponíveis: rotation_sweep, overlap_sweep, length_sweep
python run_experiments.py --start-server --sweep rotation_sweep --trials 3
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

### 4. Gerar gráficos (`plot_results.py`)

Gera gráficos PNG em `logs/charts/` a partir dos JSONs de teste ou experimento:

```bash
# De um test run (run_tests.py)
python plot_results.py --experiment logs/tests/test_TIMESTAMP.json

# De um sweep (run_experiments.py)
python plot_results.py --experiment logs/experiments/run_TIMESTAMP.json

# Processar todos os JSONs de uma vez
python plot_results.py --all
```

**Gráficos gerados por tipo de arquivo:**

| Arquivo | Gráficos |
|---------|---------|
| `logs/tests/*.json` | Barras: taxa de sucesso por tipo de CAPTCHA + box plot de tempo |
| `logs/experiments/*.json` | Barras por eixo de parâmetro + linha do sweep variado |

Os gráficos usam cores semânticas: verde ≥ 70%, amarelo ≥ 40%, vermelho < 40%.

### 5. Editar variantes de experimento

Sweeps disponíveis em `experiments/text_variants.json`: `noise_sweep`, `rotation_sweep`, `overlap_sweep`, `length_sweep`, `occlusion_sweep`.

Adicione novos sweeps editando o arquivo:

```json
{
  "name": "wave_sweep",
  "fixed": { "noise": 1, "rotation": 0 },
  "vary": "wave",
  "values": [0, 1, 2, 3]
}
```

### Compatibilidade

Os CAPTCHAs do **2captcha continuam funcionando** sem nenhuma alteração nos comandos. O modo local (`--target local`) suporta `text` e `complicated_text`.

## Referências

- AYDIN, Y. **AI-powered CAPTCHA bypass: Automating CAPTCHA solving with GPT-4o and Gemini.** 2025. Disponível em: https://aydinnyunus.github.io/2025/12/08/ai-captcha-bypass/
- DINH, N. T.; HOANG, V. T. Recent advances of CAPTCHA security analysis: a short literature review. *Procedia Computer Science*, v. 218, p. 2550–2562, 2023.
- CHANDRA, J. et al. Aura-captcha: A reinforcement learning and GAN-enhanced multi-modal CAPTCHA system. 2025.

## Licença

Este repositório é um fork/adaptação do projeto original de [Yunus Aydin](https://github.com/aydinnyunus/ai-captcha-bypass) para fins exclusivamente acadêmicos e de pesquisa.
