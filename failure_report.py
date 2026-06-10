"""
Gera relatório de taxa de falha por parâmetro de CAPTCHA.

Uso:
    python failure_report.py --experiment logs/experiments/run_20260607_120000.json
"""

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

CONFUSION_HINTS = {
    frozenset({"O", "0"}): "O/0",
    frozenset({"l", "1"}): "l/1",
    frozenset({"I", "1"}): "I/1",
    frozenset({"I", "l"}): "I/l",
    frozenset({"S", "5"}): "S/5",
    frozenset({"Z", "2"}): "Z/2",
    frozenset({"B", "8"}): "B/8",
}


def load_experiment(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_solve_log(solve_log_path="logs/solve_log.json"):
    path = Path(solve_log_path)
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def collect_failure_reasoning(results, solve_log):
    """Agrupa entradas de raciocínio do solve_log para as sessões que falharam."""
    failed_sids = {
        r.get("session_id")
        for r in results
        if not r.get("success") and r.get("session_id")
    }
    if not failed_sids:
        return []
    by_session = defaultdict(list)
    for entry in solve_log:
        if entry.get("session_id") in failed_sids and entry.get("reasoning"):
            by_session[entry["session_id"]].append(entry)
    return [{"session_id": sid, "entries": ents} for sid, ents in by_session.items()]


def aggregate_by_type(results):
    """Agrega resultados por tipo de CAPTCHA (para runs do run_tests.py)."""
    by_type = defaultdict(lambda: {"success": 0, "total": 0, "api_errors": 0})
    for r in results:
        t = r.get("type") or r.get("captcha_type") or "unknown"
        by_type[t]["total"] += 1
        if r.get("error_type"):
            by_type[t]["api_errors"] += 1
        elif r.get("success"):
            by_type[t]["success"] += 1
    return dict(by_type)


def analyze_grid_responses(results):
    """Calcula falsos positivos e negativos para resultados de grade (ground_truth como lista)."""
    grid = [r for r in results if isinstance(r.get("ground_truth"), list)]
    if not grid:
        return None
    total = len(grid)
    tp_sum = fp_sum = fn_sum = 0
    for r in grid:
        gt = set(r.get("ground_truth") or [])
        ai = {int(x) for x in (r.get("ai_response") or [])}
        tp_sum += len(gt & ai)
        fp_sum += len(ai - gt)
        fn_sum += len(gt - ai)
    return {
        "total": total,
        "avg_true_positives":  round(tp_sum  / total, 2),
        "avg_false_positives": round(fp_sum  / total, 2),
        "avg_false_negatives": round(fn_sum  / total, 2),
        "precision": round(tp_sum / (tp_sum + fp_sum), 3) if (tp_sum + fp_sum) else 0.0,
        "recall":    round(tp_sum / (tp_sum + fn_sum), 3) if (tp_sum + fn_sum) else 0.0,
    }


def edit_distance(a, b):
    """Distância de Levenshtein entre duas strings."""
    if a is None or b is None:
        return None
    a, b = str(a).upper(), str(b).upper()
    if len(a) < len(b):
        return edit_distance(b, a)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            curr.append(min(curr[-1] + 1, prev[j] + 1, prev[j - 1] + cost))
        prev = curr
    return prev[-1]


def character_confusions(ground_truth, ai_response):
    """Conta pares de caracteres trocados (ex.: O↔0)."""
    if not ground_truth or not ai_response:
        return {}
    gt, ai = str(ground_truth).upper(), str(ai_response).upper()
    confusions = defaultdict(int)
    for g, a in zip(gt, ai):
        if g != a:
            label = CONFUSION_HINTS.get(frozenset({g, a}), f"{g}/{a}")
            confusions[label] += 1
    max_len = max(len(gt), len(ai))
    if len(gt) != len(ai):
        confusions["length_mismatch"] += abs(len(gt) - len(ai))
    return dict(confusions)


def aggregate_by_axis(results):
    by_axis = defaultdict(lambda: defaultdict(lambda: {"success": 0, "total": 0, "api_errors": 0}))
    for r in results:
        params = r.get("variant_params", {})
        for axis, value in params.items():
            if axis in ("name", "sweep", "vary", "value", "seed"):
                continue
            by_axis[axis][str(value)]["total"] += 1
            if r.get("error_type"):
                by_axis[axis][str(value)]["api_errors"] += 1
            elif r.get("success", False):
                by_axis[axis][str(value)]["success"] += 1
    return by_axis


def aggregate_by_variant_name(results):
    by_name = defaultdict(lambda: {"success": 0, "total": 0, "api_errors": 0})
    for r in results:
        name = r.get("variant_name", "unknown")
        by_name[name]["total"] += 1
        if r.get("error_type"):
            by_name[name]["api_errors"] += 1
        elif r.get("success"):
            by_name[name]["success"] += 1
    return by_name


def analyze_responses(results):
    confusions = defaultdict(int)
    distances = []
    partial_correct = 0
    total_with_gt = 0

    for r in results:
        gt = r.get("ground_truth")
        ai = r.get("ai_response")
        if not gt or not ai:
            continue
        total_with_gt += 1
        dist = edit_distance(gt, ai)
        if dist is not None:
            distances.append(dist)
            if 0 < dist < len(str(gt)):
                partial_correct += 1
        for label, count in character_confusions(gt, ai).items():
            confusions[label] += count

    avg_dist = sum(distances) / len(distances) if distances else 0
    return {
        "total_with_ground_truth": total_with_gt,
        "avg_edit_distance": round(avg_dist, 2),
        "partial_errors": partial_correct,
        "confusions": dict(sorted(confusions.items(), key=lambda x: -x[1])),
    }


def success_rate(stats):
    effective = stats["total"] - stats.get("api_errors", 0)
    if effective == 0:
        return 0.0
    return 100.0 * stats["success"] / effective


def top_weak_axes(by_axis, n=3):
    axis_worst = []
    for axis, values in by_axis.items():
        if not values:
            continue
        # ignora valores onde todos os trials foram erro de API
        effective_values = {v: s for v, s in values.items()
                            if (s["total"] - s.get("api_errors", 0)) > 0}
        if not effective_values:
            continue
        worst = min(effective_values.items(), key=lambda x: success_rate(x[1]))
        effective_n = worst[1]["total"] - worst[1].get("api_errors", 0)
        axis_worst.append((axis, worst[0], success_rate(worst[1]), effective_n))
    axis_worst.sort(key=lambda x: x[2])
    return axis_worst[:n]


def _api_note(stats):
    """Retorna string '(+N API)' quando há erros de API, ou '' quando não há."""
    n = stats.get("api_errors", 0)
    return f" (+{n} API)" if n else ""


def write_markdown(report_path, experiment, by_name, by_axis, response_analysis,
                   by_type=None, grid_analysis=None, failure_reasoning=None):
    results = experiment["results"]
    total = len(results)
    api_error_results = [r for r in results if r.get("error_type")]
    wins = sum(1 for r in results if r.get("success"))
    effective_total = total - len(api_error_results)
    overall_stats = {"success": wins, "total": total, "api_errors": len(api_error_results)}

    lines = [
        "# Relatório de Falhas da IA",
        "",
        f"- **Run ID:** {experiment.get('run_id', 'N/A')}",
        f"- **Provider:** {experiment.get('provider')} / {experiment.get('model')}",
        f"- **Taxa geral:** {wins}/{effective_total} ({success_rate(overall_stats):.1f}%)"
        + (f" — _{len(api_error_results)} trial(s) excluídos por erro de API_" if api_error_results else ""),
        "",
    ]

    # Aviso de erros de API
    if api_error_results:
        error_labels = {
            "api_quota":       "Cota da API esgotada (429 RESOURCE_EXHAUSTED)",
            "api_unavailable": "API indisponível (503/502)",
            "api_timeout":     "Timeout da API",
            "api_key_invalid": "API key inválida (400 INVALID_ARGUMENT)",
        }
        counts = Counter(r["error_type"] for r in api_error_results)
        lines.extend([
            "> **Aviso:** Trials inválidos por erro de API foram excluídos das taxas de sucesso abaixo.",
            "> As taxas refletem apenas tentativas onde o bot chegou a interagir com o CAPTCHA.",
            ">",
        ])
        for etype, count in sorted(counts.items()):
            label = error_labels.get(etype, etype)
            lines.append(f"> - **{label}:** {count} trial(s)")
        lines.append("")

    # Por tipo (run_tests.py)
    if by_type:
        has_api = any(s.get("api_errors") for s in by_type.values())
        header = "| Tipo | Sucesso | Efetivos | Taxa |" + (" API erros |" if has_api else "")
        sep    = "|------|---------|----------|------|" + ("-----------|" if has_api else "")
        lines.extend(["## Por tipo de CAPTCHA", "", header, sep])
        for t, stats in sorted(by_type.items(), key=lambda x: success_rate(x[1])):
            effective = stats["total"] - stats.get("api_errors", 0)
            row = f"| {t} | {stats['success']} | {effective} | {success_rate(stats):.1f}% |"
            if has_api:
                row += f" {stats.get('api_errors', 0)} |"
            lines.append(row)
        lines.append("")

    # Por variante (run_experiments.py)
    if by_name:
        has_api = any(s.get("api_errors") for s in by_name.values())
        header = "| Variante | Sucesso | Efetivos | Taxa |" + (" API erros |" if has_api else "")
        sep    = "|----------|---------|----------|------|" + ("-----------|" if has_api else "")
        lines.extend(["## Por variante", "", header, sep])
        for name, stats in sorted(by_name.items(), key=lambda x: success_rate(x[1])):
            effective = stats["total"] - stats.get("api_errors", 0)
            row = f"| {name} | {stats['success']} | {effective} | {success_rate(stats):.1f}% |"
            if has_api:
                row += f" {stats.get('api_errors', 0)} |"
            lines.append(row)

    for axis, values in sorted(by_axis.items()):
        has_api = any(s.get("api_errors") for s in values.values())
        header = "| Valor | Sucesso | Efetivos | Taxa |" + (" API erros |" if has_api else "")
        sep    = "|-------|---------|----------|------|" + ("-----------|" if has_api else "")
        lines.extend(["", f"## Eixo: `{axis}`", "", header, sep])
        for value, stats in sorted(values.items(), key=lambda x: success_rate(x[1])):
            effective = stats["total"] - stats.get("api_errors", 0)
            row = f"| {value} | {stats['success']} | {effective} | {success_rate(stats):.1f}% |"
            if has_api:
                row += f" {stats.get('api_errors', 0)} |"
            lines.append(row)

    if by_name:
        weakest = sorted(by_name.items(), key=lambda x: success_rate(x[1]))[:3]
        lines.extend(["", "## Top 3 variantes com mais falha", ""])
        for name, stats in weakest:
            effective = stats["total"] - stats.get("api_errors", 0)
            note = _api_note(stats)
            lines.append(f"- **{name}:** {success_rate(stats):.1f}% de sucesso ({effective} efetivos{note})")

    if by_axis:
        weak_axes = top_weak_axes(by_axis, 3)
        lines.extend(["", "## Top 3 eixos de parâmetro mais fracos", ""])
        for axis, value, rate, n in weak_axes:
            lines.append(f"- **`{axis}={value}`:** {rate:.1f}% de sucesso ({n} tentativas efetivas)")

    # Análise de texto (distância de edição, confusões)
    ra = response_analysis
    if ra["total_with_ground_truth"] > 0:
        lines.extend([
            "",
            "## Análise de respostas de texto (IA vs ground truth)",
            "",
            f"- Tentativas com ground truth: {ra['total_with_ground_truth']}",
            f"- Distância de edição média: {ra['avg_edit_distance']}",
            f"- Erros parciais (distância > 0 mas < comprimento): {ra['partial_errors']}",
            "",
            "### Confusões de caracteres",
            "",
        ])
        if ra["confusions"]:
            for label, count in ra["confusions"].items():
                lines.append(f"- {label}: {count}x")
        else:
            lines.append("_Nenhuma confusão registrada._")

    # Análise da grade (FP/FN)
    if grid_analysis:
        ga = grid_analysis
        lines.extend([
            "",
            "## Análise da grade reCAPTCHA v2 (falsos positivos/negativos)",
            "",
            f"- Tentativas analisadas: {ga['total']}",
            f"- Tiles corretos clicados (TP médio por tentativa): **{ga['avg_true_positives']}**",
            f"- Tiles errados clicados (FP médio por tentativa):  **{ga['avg_false_positives']}**",
            f"- Tiles corretos perdidos (FN médio por tentativa): **{ga['avg_false_negatives']}**",
            f"- Precisão global: **{ga['precision']:.1%}**",
            f"- Recall global:   **{ga['recall']:.1%}**",
            "",
        ])

    # Raciocínio das falhas
    if failure_reasoning:
        lines.extend(["", "## Raciocínio da IA nas falhas", "",
                       "_Extraído do solve\\_log.json para cada sessão que falhou._", ""])
        for group in failure_reasoning:
            lines.append(f"### Sessão `{group['session_id']}`")
            lines.append("")
            for i, entry in enumerate(group["entries"], 1):
                step_label = (entry.get("extra") or {}).get("step") or entry.get("captcha_type", f"passo {i}")
                lines.append(f"**Passo {i} — {step_label}** | Resposta da IA: `{entry.get('ai_response', 'N/A')}`")
                lines.append("")
                lines.append(entry["reasoning"])
                lines.append("")
            lines.append("---")
            lines.append("")
    elif failure_reasoning is not None:
        lines.extend(["", "## Raciocínio da IA nas falhas", "",
                       "_Nenhuma entrada de raciocínio encontrada no solve\\_log.json para as sessões que falharam._",
                       "_Verifique se o solve\\_log.json está na pasta `logs/`._", ""])

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def write_csv(csv_path, by_axis):
    rows = []
    for axis, values in by_axis.items():
        for value, stats in values.items():
            rows.append({
                "axis": axis,
                "value": value,
                "success": stats["success"],
                "total": stats["total"],
                "rate_pct": round(success_rate(stats), 2),
            })
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["axis", "value", "success", "total", "rate_pct"])
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda r: (r["axis"], r["rate_pct"])))


def main():
    parser = argparse.ArgumentParser(description="Relatório de falhas por parâmetro")
    parser.add_argument("--experiment", type=str, required=True,
                        help="JSON gerado por run_experiments.py ou run_tests.py")
    parser.add_argument("--solve-log", type=str, default="logs/solve_log.json",
                        help="Caminho para solve_log.json (padrão: logs/solve_log.json)")
    args = parser.parse_args()

    exp_path = Path(args.experiment)
    experiment = load_experiment(exp_path)
    results = experiment.get("results", [])

    # Análises existentes (sweep/variante) — só fazem sentido se há variant_params
    has_variants = any(r.get("variant_params") for r in results)
    by_name = aggregate_by_variant_name(results) if has_variants else {}
    by_axis  = aggregate_by_axis(results)         if has_variants else {}

    # Análise por tipo (test runs)
    by_type = aggregate_by_type(results) if not has_variants else {}

    response_analysis = analyze_responses(results)
    grid_analysis     = analyze_grid_responses(results)

    # Raciocínio das falhas via solve_log
    solve_log         = load_solve_log(args.solve_log)
    failure_reasoning = collect_failure_reasoning(results, solve_log)

    run_id = experiment.get("run_id", exp_path.stem)
    report_md  = Path("logs/reports") / f"failure_analysis_{run_id}.md"
    report_csv = Path("logs/reports") / f"failure_analysis_{run_id}.csv"

    write_markdown(report_md, experiment, by_name, by_axis, response_analysis,
                   by_type=by_type, grid_analysis=grid_analysis,
                   failure_reasoning=failure_reasoning if solve_log else None)
    if by_axis:
        write_csv(report_csv, by_axis)
        print(f"Relatório CSV:      {report_csv}")

    print(f"Relatório Markdown: {report_md}")


if __name__ == "__main__":
    main()
