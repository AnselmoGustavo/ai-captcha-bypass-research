# Relatório de Falhas da IA

- **Run ID:** 20260610_170454
- **Provider:** openai / gpt-4o-mini
- **Taxa geral:** 20/30 (66.7%)

## Por variante

| Variante | Sucesso | Efetivos | Taxa |
|----------|---------|----------|------|
| occlusion_sweep_occlusion=4 | 1 | 5 | 20.0% |
| baseline | 3 | 5 | 60.0% |
| occlusion_sweep_occlusion=1 | 3 | 5 | 60.0% |
| occlusion_sweep_occlusion=0 | 4 | 5 | 80.0% |
| occlusion_sweep_occlusion=3 | 4 | 5 | 80.0% |
| occlusion_sweep_occlusion=2 | 5 | 5 | 100.0% |

## Eixo: `char_set`

| Valor | Sucesso | Efetivos | Taxa |
|-------|---------|----------|------|
| alnum | 20 | 30 | 66.7% |

## Eixo: `font_size`

| Valor | Sucesso | Efetivos | Taxa |
|-------|---------|----------|------|
| 36 | 20 | 30 | 66.7% |

## Eixo: `length`

| Valor | Sucesso | Efetivos | Taxa |
|-------|---------|----------|------|
| 5 | 20 | 30 | 66.7% |

## Eixo: `noise`

| Valor | Sucesso | Efetivos | Taxa |
|-------|---------|----------|------|
| 0 | 3 | 5 | 60.0% |
| 2 | 17 | 25 | 68.0% |

## Eixo: `occlusion`

| Valor | Sucesso | Efetivos | Taxa |
|-------|---------|----------|------|
| 4 | 1 | 5 | 20.0% |
| 1 | 3 | 5 | 60.0% |
| 0 | 4 | 5 | 80.0% |
| 3 | 4 | 5 | 80.0% |
| 2 | 5 | 5 | 100.0% |

## Eixo: `overlap`

| Valor | Sucesso | Efetivos | Taxa |
|-------|---------|----------|------|
| 0 | 20 | 30 | 66.7% |

## Eixo: `rotation`

| Valor | Sucesso | Efetivos | Taxa |
|-------|---------|----------|------|
| 0 | 3 | 5 | 60.0% |
| 15 | 17 | 25 | 68.0% |

## Eixo: `wave`

| Valor | Sucesso | Efetivos | Taxa |
|-------|---------|----------|------|
| 0 | 20 | 30 | 66.7% |

## Top 3 variantes com mais falha

- **occlusion_sweep_occlusion=4:** 20.0% de sucesso (5 efetivos)
- **baseline:** 60.0% de sucesso (5 efetivos)
- **occlusion_sweep_occlusion=1:** 60.0% de sucesso (5 efetivos)

## Top 3 eixos de parâmetro mais fracos

- **`occlusion=4`:** 20.0% de sucesso (5 tentativas efetivas)
- **`noise=0`:** 60.0% de sucesso (5 tentativas efetivas)
- **`rotation=0`:** 60.0% de sucesso (5 tentativas efetivas)

## Análise de respostas de texto (IA vs ground truth)

- Tentativas com ground truth: 30
- Distância de edição média: 0.5
- Erros parciais (distância > 0 mas < comprimento): 10

### Confusões de caracteres

- length_mismatch: 4x
- O/0: 1x
- I/T: 1x
- T/Q: 1x
- Q/D: 1x
- D/H: 1x
- H/R: 1x
- 7/R: 1x
- R/7: 1x
- F/E: 1x
- F/I: 1x
- A/4: 1x
- I/1: 1x
- G/C: 1x
- E/I: 1x
- G/E: 1x
- I/Y: 1x
- Y/V: 1x
- U/6: 1x
- 6/P: 1x

## Raciocínio da IA nas falhas

_Nenhuma entrada de raciocínio encontrada no solve\_log.json para as sessões que falharam._
_Verifique se o solve\_log.json está na pasta `logs/`._
