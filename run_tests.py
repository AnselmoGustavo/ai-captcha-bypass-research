"""
Executa bateria completa de testes para todos os tipos de CAPTCHA suportados.

Uso:
    # Locais (text + complicated_text), sobe servidor automaticamente
    python run_tests.py --start-server

    # Escolher tipos e trials
    python run_tests.py --start-server --types text complicated_text --trials 5

    # Contra o 2captcha
    python run_tests.py --target 2captcha --types text recaptcha_v2 puzzle --trials 2

    # Escolher provider/modelo
    python run_tests.py --start-server --provider gemini --model gemini-2.5-flash
"""

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path("logs/tests")

LOCAL_TYPES = ["text", "complicated_text"]
REMOTE_TYPES = ["text", "complicated_text", "recaptcha_v2", "puzzle"]

LOCAL_URLS = {
    "text": "http://127.0.0.1:5000/text",
    "complicated_text": "http://127.0.0.1:5000/complicated_text",
}


def wait_for_server(timeout=20):
    for _ in range(timeout):
        try:
            urllib.request.urlopen("http://127.0.0.1:5000/", timeout=2)
            return True
        except Exception:
            time.sleep(1)
    return False


def run_trial(captcha_type, provider, model, target, url=None):
    cmd = [sys.executable, "main.py", captcha_type, "--provider", provider, "--target", target]
    if model:
        cmd.extend(["--model", model])
    if url:
        cmd.extend(["--url", url])
    result = subprocess.run(cmd)
    return result.returncode == 0


def print_summary(results, types_run):
    print("\n" + "=" * 50)
    print(f"{'Tipo':<25} {'Resultado':>10} {'Taxa':>8}")
    print("-" * 50)
    total_wins = 0
    total_runs = 0
    for ct in types_run:
        ct_results = [r for r in results if r["type"] == ct]
        wins = sum(1 for r in ct_results if r["success"])
        total = len(ct_results)
        rate = f"{wins / total * 100:.0f}%" if total else "—"
        total_wins += wins
        total_runs += total
        print(f"{ct:<25} {wins:>4}/{total:<5} {rate:>8}")
    print("=" * 50)
    overall = f"{total_wins / total_runs * 100:.0f}%" if total_runs else "—"
    print(f"{'TOTAL':<25} {total_wins:>4}/{total_runs:<5} {overall:>8}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Bateria de testes de CAPTCHA")
    parser.add_argument(
        "--types", nargs="+", default=None,
        help="Tipos a testar. Padrão: 'text complicated_text' (local) ou 'text complicated_text recaptcha_v2 puzzle' (2captcha)",
    )
    parser.add_argument("--trials", type=int, default=3, help="Tentativas por tipo (padrão: 3)")
    parser.add_argument("--target", choices=["2captcha", "local"], default="local")
    parser.add_argument("--provider", type=str, default="gemini")
    parser.add_argument("--model", type=str, default="gemini-2.5-flash")
    parser.add_argument(
        "--start-server", action="store_true",
        help="Inicia captcha_server.py automaticamente (necessário para --target local)",
    )
    args = parser.parse_args()

    types_to_run = args.types or (LOCAL_TYPES if args.target == "local" else REMOTE_TYPES)

    server_proc = None
    if args.start_server:
        print("Iniciando captcha_server.py...")
        server_proc = subprocess.Popen([sys.executable, "captcha_server.py"])
        if not wait_for_server():
            print("Erro: servidor não respondeu em tempo.")
            if server_proc:
                server_proc.terminate()
            sys.exit(1)
        print("Servidor OK.\n")

    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        results = []

        print(f"Bateria {run_id} | target={args.target} | {args.provider}/{args.model}")
        print(f"Tipos: {', '.join(types_to_run)} | {args.trials} trial(s) cada\n")

        for captcha_type in types_to_run:
            url = LOCAL_URLS.get(captcha_type) if args.target == "local" else None
            wins = 0
            print(f"--- {captcha_type} ---")
            for trial in range(1, args.trials + 1):
                print(f"  trial {trial}/{args.trials}...", end=" ", flush=True)
                t0 = time.time()
                success = run_trial(captcha_type, args.provider, args.model, args.target, url)
                elapsed = round(time.time() - t0, 1)
                wins += int(success)
                status = "OK" if success else "FAIL"
                print(f"{status} ({elapsed}s)")
                results.append({
                    "type": captcha_type,
                    "trial": trial,
                    "success": success,
                    "elapsed_s": elapsed,
                    "target": args.target,
                })
                time.sleep(1)
            print(f"  Subtotal: {wins}/{args.trials}\n")

        out_path = OUTPUT_DIR / f"test_{run_id}.json"
        run_log = {
            "run_id": run_id,
            "target": args.target,
            "provider": args.provider,
            "model": args.model,
            "trials_per_type": args.trials,
            "results": results,
        }
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(run_log, f, ensure_ascii=False, indent=2)

        print_summary(results, types_to_run)
        print(f"Log salvo em: {out_path}")
        print(f"Relatório:    python failure_report.py --experiment {out_path}")

    finally:
        if server_proc:
            server_proc.terminate()
            server_proc.wait(timeout=5)


if __name__ == "__main__":
    main()
