"""
Logger para registrar o comportamento da IA ao resolver CAPTCHAs.
Salva em logs/solve_log.json cada tentativa com:
- timestamp
- tipo de CAPTCHA
- provider/modelo usado
- prompt enviado
- resposta da IA
- resultado (sucesso/falha)
"""

import os
import json
from datetime import datetime

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "solve_log.json")


def _ensure_log_file():
    os.makedirs(LOG_DIR, exist_ok=True)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)


def log_attempt(captcha_type, provider, model, prompt, ai_response, success=None, extra=None):
    """
    Registra uma tentativa de resolução de CAPTCHA.

    Args:
        captcha_type: Tipo do CAPTCHA (text, puzzle, recaptcha_v2, etc.)
        provider: Provider usado (openai, gemini)
        model: Modelo específico (gpt-4o, gemini-2.5-flash, etc.)
        prompt: O prompt enviado para a IA
        ai_response: A resposta retornada pela IA
        success: True/False/None se ainda não sabe
        extra: Dict com informações adicionais (ex: correções, distância calculada)
    """
    _ensure_log_file()

    entry = {
        "timestamp": datetime.now().isoformat(),
        "captcha_type": captcha_type,
        "provider": provider,
        "model": model,
        "prompt": prompt[:500] if prompt else None,  # Limita o tamanho do prompt no log
        "ai_response": str(ai_response),
        "success": success,
        "extra": extra
    }

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        logs = json.load(f)

    logs.append(entry)

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

    print(f"[LOG] {captcha_type} | {provider}/{model} | resposta: {ai_response[:80] if ai_response else 'N/A'}")


def log_result(success, captcha_type=None, details=None):
    """
    Atualiza o último registro com o resultado final (sucesso ou falha).
    """
    _ensure_log_file()

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        logs = json.load(f)

    if logs:
        logs[-1]["success"] = success
        if details:
            if logs[-1].get("extra") is None:
                logs[-1]["extra"] = {}
            logs[-1]["extra"]["result_details"] = details

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

    status = "SUCESSO" if success else "FALHA"
    print(f"[LOG] Resultado: {status}")


def get_summary():
    """Retorna um resumo das tentativas logadas."""
    _ensure_log_file()

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        logs = json.load(f)

    total = len(logs)
    successes = sum(1 for l in logs if l.get("success") is True)
    failures = sum(1 for l in logs if l.get("success") is False)
    pending = sum(1 for l in logs if l.get("success") is None)

    by_type = {}
    for l in logs:
        ct = l.get("captcha_type", "unknown")
        if ct not in by_type:
            by_type[ct] = {"total": 0, "success": 0, "fail": 0}
        by_type[ct]["total"] += 1
        if l.get("success") is True:
            by_type[ct]["success"] += 1
        elif l.get("success") is False:
            by_type[ct]["fail"] += 1

    return {
        "total_attempts": total,
        "successes": successes,
        "failures": failures,
        "pending": pending,
        "by_type": by_type
    }
