"""
Gera gráficos de taxa de sucesso e tempo de resolução a partir dos logs de experimentos.

Uso:
    # Um arquivo (test run ou sweep)
    python plot_results.py --experiment logs/tests/test_20260610_133700.json
    python plot_results.py --experiment logs/experiments/run_20260610_120000.json

    # Todos os arquivos automaticamente
    python plot_results.py --all

    # Diretório de saída customizado
    python plot_results.py --all --output-dir logs/charts
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless — sem janela gráfica
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

OUTPUT_DIR = Path("logs/charts")

# Paleta
_GREEN  = "#34a853"
_RED    = "#d93025"
_BLUE   = "#1a73e8"
_GRAY   = "#5f6368"
_YELLOW = "#fbbc04"


# ── utilitários ───────────────────────────────────────────────────────────────

def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _rate(success, total):
    return 100.0 * success / total if total else 0.0


def _bar_color(rate):
    if rate >= 70:
        return _GREEN
    if rate >= 40:
        return _YELLOW
    return _RED


def _label_bars(ax, bars, rates, extra_lines=None):
    """Escreve % e n= acima de cada barra."""
    for bar, rate in zip(bars, rates):
        label = f"{rate:.0f}%"
        if extra_lines:
            label += "\n" + extra_lines[bars.index(bar) if hasattr(bars, "index") else list(bars).index(bar)]
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1.5,
            label,
            ha="center", va="bottom", fontsize=9, fontweight="bold",
        )


def _finish(fig, ax, out_path):
    ax.spines[["top", "right"]].set_visible(False)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}%"))
    ax.set_ylim(0, 118)
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out_path


# ── gráficos para test runs (run_tests.py) ────────────────────────────────────

def _agg_by_type(results):
    by_type = defaultdict(lambda: {"success": 0, "total": 0, "elapsed": []})
    for r in results:
        t = r.get("type") or r.get("captcha_type") or "unknown"
        by_type[t]["total"] += 1
        if r.get("success"):
            by_type[t]["success"] += 1
        if r.get("elapsed_s") is not None:
            by_type[t]["elapsed"].append(r["elapsed_s"])
    return by_type


def chart_success_by_type(experiment, run_id, output_dir):
    """Barras: taxa de sucesso por tipo de CAPTCHA."""
    by_type = _agg_by_type(experiment.get("results", []))
    if not by_type:
        return None

    labels = sorted(by_type.keys())
    rates  = [_rate(by_type[t]["success"], by_type[t]["total"]) for t in labels]
    totals = [by_type[t]["total"] for t in labels]

    fig, ax = plt.subplots(figsize=(max(6, len(labels) * 2), 5))
    bars = ax.bar(labels, rates, color=[_bar_color(r) for r in rates],
                  edgecolor="white", linewidth=0.8, width=0.55)

    for bar, rate, n in zip(bars, rates, totals):
        wins = round(rate * n / 100)
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
                f"{rate:.0f}%\n{wins}/{n}",
                ha="center", va="bottom", fontsize=10, fontweight="bold")

    provider = experiment.get("provider", "")
    model    = experiment.get("model", "")
    ax.set_title(f"Taxa de Sucesso por Tipo de CAPTCHA\n{provider}/{model}  |  run {run_id}",
                 fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Tipo de CAPTCHA", fontsize=11)
    ax.set_ylabel("Taxa de Sucesso (%)", fontsize=11)
    ax.axhline(50, color=_GRAY, linestyle="--", linewidth=0.8, alpha=0.5)

    return _finish(fig, ax, output_dir / f"success_by_type_{run_id}.png")


def chart_elapsed_by_type(experiment, run_id, output_dir):
    """Box plot de tempo de resolução por tipo."""
    by_type = _agg_by_type(experiment.get("results", []))
    labels = sorted(by_type.keys())
    data   = [by_type[t]["elapsed"] for t in labels]

    # Só vale a pena se houver pelo menos 2 amostras em algum tipo
    if not any(len(d) >= 2 for d in data):
        return None

    fig, ax = plt.subplots(figsize=(max(6, len(labels) * 2), 5))
    bp = ax.boxplot(data, tick_labels=labels, patch_artist=True,
                    medianprops={"color": "white", "linewidth": 2},
                    whiskerprops={"linewidth": 1.2},
                    capprops={"linewidth": 1.2})
    for patch in bp["boxes"]:
        patch.set_facecolor(_BLUE)
        patch.set_alpha(0.75)

    ax.set_title(f"Tempo de Resolução por Tipo\nrun {run_id}",
                 fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Tipo de CAPTCHA", fontsize=11)
    ax.set_ylabel("Tempo (s)", fontsize=11)
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()

    out = output_dir / f"elapsed_by_type_{run_id}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out


# ── gráficos para experiment runs (run_experiments.py) ────────────────────────

def _agg_by_axis(results):
    by_axis = defaultdict(lambda: defaultdict(lambda: {"success": 0, "total": 0}))
    for r in results:
        params  = r.get("variant_params", {})
        success = r.get("success", False)
        for axis, value in params.items():
            if axis in ("name", "sweep", "vary", "value", "seed"):
                continue
            by_axis[axis][str(value)]["total"] += 1
            if success:
                by_axis[axis][str(value)]["success"] += 1
    return by_axis


def chart_success_by_axis(experiment, run_id, output_dir):
    """Um gráfico de barras por eixo de parâmetro."""
    by_axis = _agg_by_axis(experiment.get("results", []))
    if not by_axis:
        return []

    captcha_type = experiment.get("captcha_type", "")
    provider     = experiment.get("provider", "")
    model        = experiment.get("model", "")
    paths        = []

    for axis, values in sorted(by_axis.items()):
        try:
            sorted_vals = sorted(values.keys(), key=float)
        except (ValueError, TypeError):
            sorted_vals = sorted(values.keys())

        rates  = [_rate(values[v]["success"], values[v]["total"]) for v in sorted_vals]
        totals = [values[v]["total"] for v in sorted_vals]

        fig, ax = plt.subplots(figsize=(max(6, len(sorted_vals) * 2), 5))
        bars = ax.bar(sorted_vals, rates,
                      color=[_bar_color(r) for r in rates],
                      edgecolor="white", linewidth=0.8, width=0.55)

        for bar, rate, n in zip(bars, rates, totals):
            wins = round(rate * n / 100)
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
                    f"{rate:.0f}%\n{wins}/{n}",
                    ha="center", va="bottom", fontsize=10, fontweight="bold")

        ax.set_title(
            f"Taxa de Sucesso × {axis}\n{captcha_type} | {provider}/{model}  |  run {run_id}",
            fontsize=13, fontweight="bold", pad=12,
        )
        ax.set_xlabel(axis, fontsize=11)
        ax.set_ylabel("Taxa de Sucesso (%)", fontsize=11)
        ax.axhline(50, color=_GRAY, linestyle="--", linewidth=0.8, alpha=0.5)

        paths.append(_finish(fig, ax, output_dir / f"axis_{axis}_{run_id}.png"))

    return paths


def chart_sweep_line(experiment, run_id, output_dir):
    """Linha de taxa de sucesso ao longo dos valores do parâmetro variado (occlusion_sweep etc.)."""
    results     = experiment.get("results", [])
    vary_axis   = None
    sweep_data  = defaultdict(lambda: {"success": 0, "total": 0})

    for r in results:
        params = r.get("variant_params", {})
        vary   = params.get("vary")
        value  = params.get("value")
        if vary is None or value is None:
            return None  # não é sweep estruturado
        if vary_axis is None:
            vary_axis = vary
        if vary != vary_axis:
            return None  # múltiplos eixos no mesmo arquivo — não suportado aqui
        sweep_data[str(value)]["total"] += 1
        if r.get("success"):
            sweep_data[str(value)]["success"] += 1

    if not sweep_data or vary_axis is None:
        return None

    try:
        xs_sorted = sorted(sweep_data.keys(), key=float)
        xs_num    = [float(x) for x in xs_sorted]
    except (ValueError, TypeError):
        xs_sorted = sorted(sweep_data.keys())
        xs_num    = list(range(len(xs_sorted)))

    rates = [_rate(sweep_data[v]["success"], sweep_data[v]["total"]) for v in xs_sorted]

    captcha_type = experiment.get("captcha_type", "")
    provider     = experiment.get("provider", "")
    model        = experiment.get("model", "")

    fig, ax = plt.subplots(figsize=(max(7, len(xs_num) * 1.8), 5))
    ax.plot(xs_num, rates, marker="o", color=_BLUE, linewidth=2, markersize=8, zorder=3)
    ax.fill_between(xs_num, rates, alpha=0.12, color=_BLUE)
    for x, rate in zip(xs_num, rates):
        ax.text(x, rate + 2.5, f"{rate:.0f}%", ha="center", fontsize=9, fontweight="bold")

    ax.set_title(
        f"Taxa de Sucesso × {vary_axis} (sweep)\n{captcha_type} | {provider}/{model}  |  run {run_id}",
        fontsize=13, fontweight="bold", pad=12,
    )
    ax.set_xlabel(vary_axis, fontsize=11)
    ax.set_ylabel("Taxa de Sucesso (%)", fontsize=11)
    ax.set_xticks(xs_num)
    ax.set_xticklabels(xs_sorted)
    ax.axhline(50, color=_GRAY, linestyle="--", linewidth=0.8, alpha=0.5)

    return _finish(fig, ax, output_dir / f"sweep_{vary_axis}_{run_id}.png")


# ── ponto de entrada ───────────────────────────────────────────────────────────

def process_file(path, output_dir):
    experiment = _load(path)
    run_id     = experiment.get("run_id", Path(path).stem)
    results    = experiment.get("results", [])
    generated  = []

    has_variants = any(r.get("variant_params") for r in results)

    if has_variants:
        # Experiment run
        sweep_chart = chart_sweep_line(experiment, run_id, output_dir)
        if sweep_chart:
            generated.append(sweep_chart)
        generated.extend(chart_success_by_axis(experiment, run_id, output_dir))
    else:
        # Test run
        p = chart_success_by_type(experiment, run_id, output_dir)
        if p:
            generated.append(p)
        p = chart_elapsed_by_type(experiment, run_id, output_dir)
        if p:
            generated.append(p)

    return generated


def main():
    parser = argparse.ArgumentParser(description="Gera gráficos de taxa de sucesso dos experimentos")
    group  = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--experiment", type=str,
                       help="JSON de run_experiments.py ou run_tests.py")
    group.add_argument("--all", action="store_true",
                       help="Processa todos os JSONs em logs/tests/ e logs/experiments/")
    parser.add_argument("--output-dir", type=str, default="logs/charts",
                        help="Diretório de saída (padrão: logs/charts)")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)

    if args.all:
        files  = sorted(Path("logs/tests").glob("*.json"))
        files += sorted(Path("logs/experiments").glob("*.json"))
        if not files:
            print("Nenhum arquivo JSON encontrado em logs/tests/ ou logs/experiments/")
            return
        total = 0
        for path in files:
            generated = process_file(path, output_dir)
            for g in generated:
                print(f"Gráfico gerado: {g}")
                total += 1
        print(f"\n{total} gráfico(s) gerado(s) em {output_dir}/")
    else:
        generated = process_file(args.experiment, output_dir)
        for g in generated:
            print(f"Gráfico gerado: {g}")
        if not generated:
            print("Nenhum gráfico foi gerado (dados insuficientes).")


if __name__ == "__main__":
    main()
