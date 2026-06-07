"""
Gera relatório de taxa de falha por parâmetro de CAPTCHA.

Uso:
    python failure_report.py --experiment logs/experiments/run_20260607_120000.json
"""

import argparse
import csv
import json
from collections import defaultdict
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
    by_axis = defaultdict(lambda: defaultdict(lambda: {"success": 0, "total": 0}))
    for r in results:
        params = r.get("variant_params", {})
        success = r.get("success", False)
        for axis, value in params.items():
            if axis in ("name", "sweep", "vary", "value", "seed"):
                continue
            by_axis[axis][str(value)]["total"] += 1
            if success:
                by_axis[axis][str(value)]["success"] += 1
    return by_axis


def aggregate_by_variant_name(results):
    by_name = defaultdict(lambda: {"success": 0, "total": 0})
    for r in results:
        name = r.get("variant_name", "unknown")
        by_name[name]["total"] += 1
        if r.get("success"):
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
    if stats["total"] == 0:
        return 0.0
    return 100.0 * stats["success"] / stats["total"]


def top_weak_axes(by_axis, n=3):
    axis_worst = []
    for axis, values in by_axis.items():
        if not values:
            continue
        worst = min(values.items(), key=lambda x: success_rate(x[1]))
        axis_worst.append((axis, worst[0], success_rate(worst[1]), worst[1]["total"]))
    axis_worst.sort(key=lambda x: x[2])
    return axis_worst[:n]


def write_markdown(report_path, experiment, by_name, by_axis, response_analysis):
    results = experiment["results"]
    total = len(results)
    wins = sum(1 for r in results if r.get("success"))
    lines = [
        "# Relatório de Falhas da IA",
        "",
        f"- **Run ID:** {experiment.get('run_id', 'N/A')}",
        f"- **Provider:** {experiment.get('provider')} / {experiment.get('model')}",
        f"- **Taxa geral:** {wins}/{total} ({success_rate({'success': wins, 'total': total}):.1f}%)",
        "",
        "## Por variante",
        "",
        "| Variante | Sucesso | Total | Taxa |",
        "|----------|---------|-------|------|",
    ]
    for name, stats in sorted(by_name.items(), key=lambda x: success_rate(x[1])):
        rate = success_rate(stats)
        lines.append(f"| {name} | {stats['success']} | {stats['total']} | {rate:.1f}% |")

    for axis, values in sorted(by_axis.items()):
        lines.extend(["", f"## Eixo: `{axis}`", "", "| Valor | Sucesso | Total | Taxa |", "|-------|---------|-------|------|"])
        for value, stats in sorted(values.items(), key=lambda x: success_rate(x[1])):
            rate = success_rate(stats)
            lines.append(f"| {value} | {stats['success']} | {stats['total']} | {rate:.1f}% |")

    weakest = sorted(by_name.items(), key=lambda x: success_rate(x[1]))[:3]
    lines.extend(["", "## Top 3 variantes com mais falha", ""])
    for name, stats in weakest:
        lines.append(f"- **{name}:** {success_rate(stats):.1f}% de sucesso")

    weak_axes = top_weak_axes(by_axis, 3)
    lines.extend(["", "## Top 3 eixos de parâmetro mais fracos", ""])
    for axis, value, rate, n in weak_axes:
        lines.append(f"- **`{axis}={value}`:** {rate:.1f}% de sucesso ({n} tentativas)")

    ra = response_analysis
    lines.extend([
        "",
        "## Análise de respostas (IA vs ground truth)",
        "",
        f"- Tentativas com ground truth: {ra['total_with_ground_truth']}",
        f"- Distância de edição média: {ra['avg_edit_distance']}",
        f"- Erros parciais (distância > 0 mas não total): {ra['partial_errors']}",
        "",
        "### Confusões de caracteres",
        "",
    ])
    if ra["confusions"]:
        for label, count in ra["confusions"].items():
            lines.append(f"- {label}: {count}x")
    else:
        lines.append("_Nenhuma confusão registrada (sem ground truth nos resultados)._")

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
    parser.add_argument("--experiment", type=str, required=True, help="JSON gerado por run_experiments.py")
    args = parser.parse_args()

    exp_path = Path(args.experiment)
    experiment = load_experiment(exp_path)
    results = experiment.get("results", [])

    by_name = aggregate_by_variant_name(results)
    by_axis = aggregate_by_axis(results)
    response_analysis = analyze_responses(results)

    run_id = experiment.get("run_id", exp_path.stem)
    report_md = Path("logs/reports") / f"failure_analysis_{run_id}.md"
    report_csv = Path("logs/reports") / f"failure_analysis_{run_id}.csv"

    write_markdown(report_md, experiment, by_name, by_axis, response_analysis)
    write_csv(report_csv, by_axis)

    print(f"Relatório Markdown: {report_md}")
    print(f"Relatório CSV: {report_csv}")


if __name__ == "__main__":
    main()
