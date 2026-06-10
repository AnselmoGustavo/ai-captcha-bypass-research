# Resultados dos Experimentos — Bot de Bypass de CAPTCHA

**Projeto:** Autenticação Procedural: Defesas dinâmicas para resistência a bots  
**Instituição:** PUC Minas  
**Data dos testes:** 10/06/2026  
**Modelo utilizado:** OpenAI GPT-4o-mini  
**Provedor:** OpenAI API  

---

## 1. Visão Geral

Foram realizados quatro conjuntos de experimentos:

| Experimento | Descrição | Trials |
|-------------|-----------|--------|
| Testes 2captcha | Bot contra demos reais do 2captcha.com | 2 por tipo |
| Testes locais | Bot contra servidor Flask local com CAPTCHAs gerados proceduralmente | 5 por tipo |
| Sweep de ruído (`noise_sweep`) | Variação do parâmetro `noise` em CAPTCHA de texto simples | 5 por variante |
| Sweep de oclusão (`occlusion_sweep`) | Variação do parâmetro `occlusion` em CAPTCHA de texto complicado | 5 por variante |

---

## 2. Testes no 2captcha (demos reais)

**Arquivo de log:** `logs/tests/test_20260610_163707.json`  
**Gráficos:** `logs/charts/success_by_type_20260610_163707.png`

| Tipo | Resultado | Taxa | Observação |
|------|-----------|------|------------|
| text | 2/2 | **100%** | Resolvido corretamente nas 2 tentativas |
| complicated_text | 2/2 | **100%** | Passou em 1 tentativa (trial 1) e em 2 tentativas (trial 2) |
| recaptcha_v2 | 0/2 | **0%** | Falha de infraestrutura (ver nota abaixo) |
| puzzle (GeeTest) | 0/2 | **0%** | Bloqueio por política de conteúdo (ver nota abaixo) |

### Notas sobre falhas no 2captcha

**reCAPTCHA v2 — falha de Selenium, não da IA:**  
O iframe do desafio de imagem do reCAPTCHA levou mais tempo que o timeout configurado (3s) para aparecer. O bot interpretou a ausência de detecção como "sem desafio", avançou para submissão e encontrou o botão bloqueado pelo próprio iframe. Trata-se de um problema de timing de Selenium, não de capacidade de reconhecimento visual da IA.

**Puzzle (GeeTest) — filtro de conteúdo da OpenAI:**  
O puzzle do 2captcha usa imagens de fundo que contêm rostos humanos. O GPT-4o-mini recusou processar todas as imagens com mensagens como *"I can't assist with identifying or describing people in images"*. Essa é uma limitação de política de conteúdo da OpenAI — o modelo é capaz de resolver o slider puzzle, mas recusa imagens com pessoas. Não é uma limitação de raciocínio espacial.

> **Importante para o relatório:** Os testes no 2captcha não são estatisticamente independentes — o site usa um conjunto fixo (ou muito pequeno) de imagens CAPTCHA. As 2 trials do mesmo tipo podem estar resolvendo exatamente o mesmo desafio. Os resultados devem ser interpretados qualitativamente ("o bot consegue ou não resolver esse tipo") e não como taxa de sucesso estatística.

---

## 3. Testes Locais (CAPTCHAs procedurais)

**Arquivo de log:** `logs/tests/test_20260610_164811.json`  
**Gráficos:** `logs/charts/success_by_type_20260610_164811.png`

| Tipo | Resultado | Taxa |
|------|-----------|------|
| text (simples) | 5/5 | **100%** |
| complicated_text (distorcido) | 2/5 | **40%** |
| recaptcha_v2 (local) | 5/5 | **100%** |

Os CAPTCHAs locais foram gerados com seeds aleatórios distintos em cada trial, garantindo independência entre as tentativas.

### Análise qualitativa

**text (100%):** Com o prompt corrigido (instrução explícita para responder sem espaços), o modelo acertou todas as 5 tentativas. Exemplos de respostas corretas: `51G3Q`, `GK7HC`, `1GKJU`, `V7OJX`, `E0D18`.

**complicated_text (40%):** O preset difícil (`noise=3, rotation=25, occlusion=2, wave=2`) desafia genuinamente o modelo. Nas 3 falhas, o modelo produziu respostas com contagem de caracteres incorreta (ex.: `6I1DVB` com 6 chars quando o CAPTCHA tinha 5, `82qkv0` com 6 chars). A distorção combinada de múltiplos parâmetros ao mesmo tempo parece ser o fator determinante.

**recaptcha_v2 (100%):** O bot selecionou corretamente os tiles em todas as 5 tentativas, com objetos variados (estrelas, triângulos, quadrados). O reconhecimento visual de formas geométricas simples não apresentou dificuldades para o GPT-4o-mini.

---

## 4. Sweep de Ruído — `noise_sweep` (texto simples)

**Arquivo de log:** `logs/experiments/run_20260610_165319.json`  
**Gráfico principal:** `logs/charts/axis_noise_20260610_165319.png`  
**Total:** 27/35 (77%)

| Variante | Resultado | Taxa |
|----------|-----------|------|
| baseline (noise=0, sem outros parâmetros) | 5/5 | **100%** |
| noise=0 | 3/5 | 60% |
| noise=1 | 4/5 | 80% |
| noise=2 | 5/5 | **100%** |
| noise=3 | 4/5 | 80% |
| noise=4 | 4/5 | 80% |
| noise=5 | 2/5 | **40%** |

### Observações

- A taxa de sucesso cai progressivamente a partir de `noise=5` (40%), mas não de forma linear nos valores intermediários.
- `noise=2` atingiu 100%, sugerindo que ruído moderado não prejudica o reconhecimento — possivelmente porque o modelo aprende a filtrar ruído visual de baixa intensidade.
- A queda mais acentuada ocorre em `noise=5`, onde o ruído começa a mascarar os próprios traços das letras.
- A diferença entre o `baseline` (100%) e `noise=0` no sweep (60%) pode ser explicada por variabilidade amostral (apenas 5 trials por variante), ou por diferenças sutis nos parâmetros fixos da URL.

---

## 5. Sweep de Oclusão — `occlusion_sweep` (texto complicado)

**Arquivo de log:** `logs/experiments/run_20260610_170454.json`  
**Gráfico principal:** `logs/charts/axis_occlusion_20260610_170454.png`  
**Total:** 20/30 (67%)

| Variante | Resultado | Taxa |
|----------|-----------|------|
| baseline (sem distorção) | 3/5 | 60% |
| occlusion=0 (com noise+rotation, sem oclusão) | 4/5 | 80% |
| occlusion=1 | 3/5 | 60% |
| occlusion=2 | 5/5 | **100%** |
| occlusion=3 | 4/5 | 80% |
| occlusion=4 | 1/5 | **20%** |

### Observações

- **`occlusion=4` é o ponto de ruptura** (20%): quatro linhas horizontais cruzando o texto, combinadas com ruído (`noise=2`) e rotação (`rotation=15`), reduzem drasticamente a taxa de sucesso.
- `occlusion=2` paradoxalmente atingiu 100% — oclusão moderada parece não prejudicar o modelo, talvez porque o contexto restante dos caracteres ainda seja suficiente para inferência.
- A combinação de múltiplos parâmetros de distorção (`noise + rotation + occlusion`) parece ter efeito multiplicativo, não aditivo: quando um parâmetro já estressado (rotation=15) se combina com oclusão alta (4 linhas), o modelo falha mais do que falharia com apenas um dos dois.
- O `baseline` (sem distorção alguma) obteve apenas 60%, abaixo de alguns níveis com oclusão. Isso indica variabilidade natural da geração de caracteres como fator dominante em amostras pequenas.

---

## 6. Comparação 2captcha vs. Local

| Tipo | 2captcha | Local |
|------|----------|-------|
| text | 100% | 100% |
| complicated_text | 100% | 40% |
| recaptcha_v2 | — (infra) | 100% |

A diferença no `complicated_text` revela uma assimetria importante: o preset local ("difícil") é mais desafiador do que o CAPTCHA real do 2captcha. Isso é esperado — o 2captcha usa parâmetros calibrados para humanos passarem com facilidade; o preset local foi deliberadamente configurado com distorções mais agressivas (`noise=3, rotation=25, occlusion=2, wave=2`).

---

## 7. Limitações e Considerações Metodológicas

1. **Tamanho amostral pequeno:** 5 trials por variante é suficiente para tendências mas não para afirmações estatísticas robustas. Variações de ±20% são esperadas por aleatoriedade.

2. **2captcha não-independente:** As demos do 2captcha podem usar imagens fixas, tornando trials repetidas não-independentes.

3. **Raciocínio desativado:** Para economizar quota de API, o módulo de raciocínio por passo foi desativado nesta rodada. Os logs de raciocínio em falhas individuais ainda estão disponíveis em `logs/reasoning_*.md`.

4. **reCAPTCHA v2 no 2captcha:** Não houve coleta válida de dados por problema de Selenium. O dado local (100%) deve ser usado como referência para este tipo.

5. **Puzzle no 2captcha:** O filtro de conteúdo da OpenAI para imagens com pessoas torna o GPT-4o-mini inviável para puzzles com fundos fotográficos. Uma alternativa seria usar o Gemini (sem esse filtro) para este tipo específico.

6. **Prompt sensível ao formato:** Os primeiros testes mostraram que o GPT-4o-mini inseria espaços entre caracteres ("A B C D E" em vez de "ABCDE"). A correção do prompt foi necessária e demonstra que a formulação exata da instrução impacta diretamente a taxa de sucesso — um achado relevante sobre a sensibilidade dos modelos de linguagem a instruções de formato.

---

## 8. Arquivos Gerados

| Tipo | Localização |
|------|-------------|
| Logs de teste (JSON) | `logs/tests/test_20260610_163707.json` (2captcha), `logs/tests/test_20260610_164811.json` (local) |
| Logs de experimento (JSON) | `logs/experiments/run_20260610_165319.json` (noise), `logs/experiments/run_20260610_170454.json` (occlusion) |
| Relatórios de falha (Markdown) | `logs/reports/failure_analysis_20260610_*.md` |
| Gráficos (PNG) | `logs/charts/` — 19 gráficos no total |
| GIFs de sucesso | `successful_solves/` |
| GIFs de falha | `failed_solves/` |
| Logs de raciocínio (falhas) | `logs/reasoning_*.md` |
