"""
Executa bateria de experimentos contra CAPTCHAs locais.

Pré-requisito: servidor rodando (ou use --start-server):
    python captcha_server.py

Uso:
    python run_experiments.py
    python run_experiments.py --sweep noise_sweep --trials 3
    python run_experiments.py --start-server --sweep noise_sweep --trials 2
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

from solve_logger import get_latest_session_metadata

EXPERIMENTS_FILE = Path("experiments/text_variants.json")
OUTPUT_DIR = Path("logs/experiments")
DEFAULT_BASE = "http://127.0.0.1:5000/text"


def load_config():
    with open(EXPERIMENTS_FILE, encoding="utf-8") as f:
        return json.load(f)


def build_variants(config, sweep_name=None):
    variants = [{"name": "baseline", **config["baseline"]}]
    for sweep in config["sweeps"]:
        if sweep_name and sweep["name"] != sweep_name:
            continue
        for value in sweep["values"]:
            variant = dict(config["baseline"])
            variant.update(sweep.get("fixed", {}))
            variant[sweep["vary"]] = value
            variants.append({
                "name": f"{sweep['name']}_{sweep['vary']}={value}",
                "sweep": sweep["name"],
                "vary": sweep["vary"],
                "value": value,
                **{k: v for k, v in variant.items() if k not in ("name", "sweep", "vary", "value")},
            })
    return variants


def variant_url(base_url, variant, seed):
    params = {k: v for k, v in variant.items() if k not in ("name", "sweep", "vary", "value")}
    params["seed"] = seed
    return f"{base_url}?{urlencode(params)}"


def run_trial(url, provider, model):
    cmd = [
        sys.executable, "main.py", "text",
        "--target", "local",
        "--url", url,
        "--provider", provider,
    ]
    if model:
        cmd.extend(["--model", model])
    result = subprocess.run(cmd)
    return result.returncode == 0


def wait_for_server(base_url, timeout=15):
    import urllib.request
    health = base_url.replace("/text", "/") if "/text" in base_url else base_url
    for _ in range(timeout):
        try:
            urllib.request.urlopen(health, timeout=2)
            return True
        except Exception:
            time.sleep(1)
    return False


def main():
    parser = argparse.ArgumentParser(description="Roda experimentos de CAPTCHA local")
    parser.add_argument("--sweep", type=str, default=None, help="Nome do sweep (ex: noise_sweep)")
    parser.add_argument("--trials", type=int, default=None, help="Tentativas por variante")
    parser.add_argument("--base-url", type=str, default=DEFAULT_BASE)
    parser.add_argument("--provider", type=str, default="gemini")
    parser.add_argument("--model", type=str, default="gemini-2.5-flash")
    parser.add_argument("--start-server", action="store_true", help="Inicia captcha_server.py em subprocess")
    args = parser.parse_args()

    server_proc = None
    if args.start_server:
        print("Iniciando captcha_server.py...")
        server_proc = subprocess.Popen([sys.executable, "captcha_server.py"])
        if not wait_for_server(args.base_url):
            print("Erro: servidor local não respondeu a tempo.")
            if server_proc:
                server_proc.terminate()
            sys.exit(1)

    try:
        config = load_config()
        trials = args.trials or config.get("trials_per_variant", 5)
        variants = build_variants(config, args.sweep)

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_log = {
            "run_id": run_id,
            "provider": args.provider,
            "model": args.model,
            "trials_per_variant": trials,
            "sweep": args.sweep,
            "results": [],
        }

        print(f"Iniciando experimento {run_id} — {len(variants)} variantes × {trials} trials")

        for variant in variants:
            name = variant["name"]
            for trial in range(trials):
                seed = hash((run_id, name, trial)) % (2**31)
                url = variant_url(args.base_url, variant, seed)
                print(f"\n--- {name} | trial {trial + 1}/{trials} ---")
                print(f"URL: {url}")
                t0 = time.time()
                success = run_trial(url, args.provider, args.model)
                elapsed = round(time.time() - t0, 1)
                meta = get_latest_session_metadata()
                run_log["results"].append({
                    "variant_name": name,
                    "variant_params": {k: v for k, v in variant.items() if k not in ("name", "sweep", "vary", "value")},
                    "trial": trial + 1,
                    "seed": seed,
                    "url": url,
                    "success": success,
                    "elapsed_s": elapsed,
                    "ground_truth": meta.get("ground_truth"),
                    "ai_response": meta.get("ai_response"),
                    "variant": meta.get("variant"),
                    "session_id": meta.get("session_id"),
                })
                time.sleep(1)

        out_path = OUTPUT_DIR / f"run_{run_id}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(run_log, f, ensure_ascii=False, indent=2)

        total = len(run_log["results"])
        wins = sum(1 for r in run_log["results"] if r["success"])
        print(f"\nConcluído: {wins}/{total} sucessos. Log: {out_path}")
        print(f"Relatório: python failure_report.py --experiment {out_path}")
    finally:
        if server_proc:
            server_proc.terminate()
            server_proc.wait(timeout=5)


if __name__ == "__main__":
    main()
