# Relatório de Falhas da IA

- **Run ID:** 20260610_165319
- **Provider:** openai / gpt-4o-mini
- **Taxa geral:** 27/35 (77.1%)

## Por variante

| Variante | Sucesso | Efetivos | Taxa |
|----------|---------|----------|------|
| noise_sweep_noise=5 | 2 | 5 | 40.0% |
| noise_sweep_noise=0 | 3 | 5 | 60.0% |
| noise_sweep_noise=1 | 4 | 5 | 80.0% |
| noise_sweep_noise=3 | 4 | 5 | 80.0% |
| noise_sweep_noise=4 | 4 | 5 | 80.0% |
| baseline | 5 | 5 | 100.0% |
| noise_sweep_noise=2 | 5 | 5 | 100.0% |

## Eixo: `char_set`

| Valor | Sucesso | Efetivos | Taxa |
|-------|---------|----------|------|
| alnum | 27 | 35 | 77.1% |

## Eixo: `font_size`

| Valor | Sucesso | Efetivos | Taxa |
|-------|---------|----------|------|
| 36 | 27 | 35 | 77.1% |

## Eixo: `length`

| Valor | Sucesso | Efetivos | Taxa |
|-------|---------|----------|------|
| 5 | 27 | 35 | 77.1% |

## Eixo: `noise`

| Valor | Sucesso | Efetivos | Taxa |
|-------|---------|----------|------|
| 5 | 2 | 5 | 40.0% |
| 0 | 8 | 10 | 80.0% |
| 1 | 4 | 5 | 80.0% |
| 3 | 4 | 5 | 80.0% |
| 4 | 4 | 5 | 80.0% |
| 2 | 5 | 5 | 100.0% |

## Eixo: `overlap`

| Valor | Sucesso | Efetivos | Taxa |
|-------|---------|----------|------|
| 0 | 27 | 35 | 77.1% |

## Eixo: `rotation`

| Valor | Sucesso | Efetivos | Taxa |
|-------|---------|----------|------|
| 0 | 27 | 35 | 77.1% |

## Eixo: `wave`

| Valor | Sucesso | Efetivos | Taxa |
|-------|---------|----------|------|
| 0 | 27 | 35 | 77.1% |

## Top 3 variantes com mais falha

- **noise_sweep_noise=5:** 40.0% de sucesso (5 efetivos)
- **noise_sweep_noise=0:** 60.0% de sucesso (5 efetivos)
- **noise_sweep_noise=1:** 80.0% de sucesso (5 efetivos)

## Top 3 eixos de parâmetro mais fracos

- **`noise=5`:** 40.0% de sucesso (5 tentativas efetivas)
- **`rotation=0`:** 77.1% de sucesso (35 tentativas efetivas)
- **`overlap=0`:** 77.1% de sucesso (35 tentativas efetivas)

## Análise de respostas de texto (IA vs ground truth)

- Tentativas com ground truth: 35
- Distância de edição média: 0.23
- Erros parciais (distância > 0 mas < comprimento): 8

### Confusões de caracteres

- O/0: 4x
- length_mismatch: 4x
- Y/T: 1x
- T/Y: 1x
- B/P: 1x
- P/B: 1x
- I/1: 1x

## Raciocínio da IA nas falhas

_Nenhuma entrada de raciocínio encontrada no solve\_log.json para as sessões que falharam._
_Verifique se o solve\_log.json está na pasta `logs/`._
