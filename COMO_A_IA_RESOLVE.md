# Como a IA Resolve os CAPTCHAs

Este documento descreve, para cada tipo de CAPTCHA, como o bot utiliza inteligência artificial
para resolver os desafios de autenticação. Esta documentação serve como referência para a
análise experimental do trabalho acadêmico.

---

## 1. Text CAPTCHA (Texto Simples)

**Página de teste:** https://2captcha.com/demo/normal

**Processo:**
1. O Selenium abre o Firefox e navega até a página
2. Captura um screenshot da imagem do CAPTCHA
3. Envia a imagem para a IA com o prompt:
   > "Act as a blind person assistant. Read the text from the image and give me only the text answer."
4. A IA retorna o texto reconhecido
5. O bot digita o texto no campo de input e clica em "Check"
6. Verifica se a resposta foi aceita

**Técnica explorada pela IA:** OCR (Reconhecimento Óptico de Caracteres) via modelo multimodal.

**Vulnerabilidade do CAPTCHA:** A IA consegue reconhecer texto mesmo com pequenas distorções, pois modelos multimodais foram treinados com milhões de imagens de texto.

---

## 2. Complicated Text CAPTCHA (Texto Distorcido)

**Página de teste:** https://2captcha.com/demo/mtcaptcha

**Processo:**
1. Navega até a página do MTCaptcha
2. Captura screenshot do iframe contendo o CAPTCHA distorcido
3. Envia para a IA com o mesmo prompt de reconhecimento de texto
4. Digita a resposta e submete
5. Se falhar, tenta até 3 vezes (o CAPTCHA recarrega a cada tentativa)

**Técnica explorada:** OCR avançado com capacidade de lidar com ruído, rotação e sobreposição.

**Vulnerabilidade:** Mesmo com distorções mais intensas, modelos como Gemini 2.5 conseguem interpretar texto com alta taxa de acerto porque utilizam compreensão contextual além de pixel matching.

---

## 3. reCAPTCHA v2 (Seleção de Imagens)

**Página de teste:** https://2captcha.com/demo/recaptcha-v2

**Processo:**
1. Clica no checkbox "Não sou um robô"
2. Quando o desafio de imagens aparece, captura screenshot da barra de instruções
3. Envia para a IA com o prompt:
   > "Analyze the blue instruction bar in the image. Identify the primary object the user is asked to select."
4. A IA identifica o objeto alvo (ex: "motorcycles", "traffic lights")
5. Para cada tile (quadrado) da grade 3x3 ou 4x4:
   - Captura o tile individualmente
   - Pergunta à IA: "Does this image clearly contain a '[objeto]'?"
   - A IA responde "true" ou "false"
6. Clica nos tiles que a IA identificou como contendo o objeto
7. Clica em "Verify"
8. Repete se necessário (novos tiles podem aparecer)

**Técnica explorada:** Classificação de imagens e detecção de objetos via modelo multimodal.

**Vulnerabilidade:** Os modelos de IA atuais superam humanos em tarefas de classificação de objetos. A grade fixa de tiles e o formato previsível das instruções facilitam a automação.

---

## 4. Puzzle CAPTCHA (Slider)

**Página de teste:** https://2captcha.com/demo/geetest (ou similar)

**Processo:**
1. Captura screenshot do puzzle (mostra a peça e o slot vazio)
2. Envia para a IA com prompt pedindo a distância em pixels entre o slider e o slot:
   > "Calculate the horizontal pixel distance from the current center of the slider handle to the center of the empty slot."
3. A IA retorna um número inteiro (ex: "134")
4. O bot arrasta o slider pela distância calculada
5. Captura novo screenshot para verificar alinhamento
6. Se não estiver perfeito, pede uma correção:
   > "Determine the final pixel adjustment required to perfectly align the puzzle piece."
7. Aplica a correção e verifica o resultado

**Técnica explorada:** Análise espacial e cálculo de coordenadas via visão computacional.

**Vulnerabilidade:** A posição do slot é visualmente previsível. A IA consegue medir distâncias em pixels a partir de imagens com alta precisão.

---

## 5. Audio CAPTCHA (Áudio)

**Processo:**
1. Baixa o arquivo de áudio do CAPTCHA
2. Envia para a IA com o prompt:
   > "Type only the letters you hear clearly and loudly spoken. Ignore any background words, sounds, or faint speech."
3. A IA transcreve as letras/números
4. O bot digita a transcrição e submete

**Técnica explorada:** Speech-to-text / transcrição de áudio via modelos de linguagem.

**Vulnerabilidade:** Modelos de áudio modernos conseguem filtrar ruído de fundo e transcrever com alta precisão, tornando CAPTCHAs de áudio ineficazes.

---

## Padrões Explorados pelo Bot

| Padrão | Descrição | Impacto |
|--------|-----------|---------|
| **Estrutura fixa do DOM** | Seletores CSS/XPath previsíveis | Bot localiza elementos facilmente |
| **Formato padrão de instruções** | "Select all squares with X" | IA extrai o objeto-alvo facilmente |
| **Grade fixa de imagens** | Sempre 3x3 ou 4x4 | Bot sabe exatamente quantos tiles analisar |
| **Posição fixa do slider** | Sempre começa à esquerda | Simplifica o cálculo de distância |
| **Feedback visual previsível** | Mensagem de sucesso/erro no mesmo local | Bot confirma resultado automaticamente |

---

## Comando para Rodar

```bash
# Text
python main.py text --provider gemini --model gemini-2.5-flash

# Complicated Text
python main.py complicated_text --provider gemini --model gemini-2.5-flash

# reCAPTCHA v2
python main.py recaptcha_v2 --provider gemini --model gemini-2.5-flash

# Puzzle
python main.py puzzle --provider gemini --model gemini-2.5-flash

# Audio
python main.py audio --provider gemini --model gemini-2.5-flash

# Com documentação do raciocínio da IA
python main.py text --provider gemini --model gemini-2.5-flash --explain
```

---

## Logs e Raciocínio da IA

Cada execução gera dois artefatos:

### 1. `logs/solve_log.json` — log estruturado por chamada

```json
{
  "session_id": "a3f2b1c4",
  "timestamp": "2026-06-02T17:07:15.123456",
  "captcha_type": "text",
  "provider": "gemini",
  "model": "gemini-2.5-flash",
  "prompt": "Act as a blind person assistant. Read the text from the image...",
  "ai_response": "W93Hx",
  "reasoning": "Identifiquei 5 caracteres alfanuméricos na imagem. O W estava levemente inclinado...",
  "success": true,
  "extra": null
}
```

O campo `reasoning` é preenchido somente com a flag `--explain`, via uma **segunda chamada** à API em português.

### 2. `logs/reasoning_TIMESTAMP_TIPO.md` — relatório narrativo

Gerado ao final da execução **apenas com `--explain`**. Contém o raciocínio completo de cada passo.

```bash
python main.py text --provider gemini --model gemini-2.5-flash --explain
```

### Custo de API

Sem `--explain`: 1 chamada por passo (comportamento padrão). Com `--explain`: 2 chamadas por passo; no reCAPTCHA v2, cada tile também gera explicação.

Para ver o resumo:
```bash
python -c "from solve_logger import get_summary; import json; print(json.dumps(get_summary(), indent=2, ensure_ascii=False))"
```
