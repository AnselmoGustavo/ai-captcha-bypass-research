"""
Logger para registrar o comportamento da IA ao resolver CAPTCHAs.
Salva em logs/solve_log.json cada tentativa com:
- timestamp
- session_id
- tipo de CAPTCHA
- provider/modelo usado
- prompt enviado
- resposta da IA
- raciocínio da IA (2a chamada)
- resultado (sucesso/falha)
"""

import os
import json
import uuid
import threading
from datetime import datetime

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "solve_log.json")

_current_session = None
_log_lock = threading.Lock()


def _ensure_log_file():
    os.makedirs(LOG_DIR, exist_ok=True)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)


def start_session(captcha_type, provider, model, explicit_explain=False):
    """Inicia uma sessão de resolução e retorna o session_id.

    O raciocínio é sempre capturado (explain_reasoning=True).
    O relatório Markdown só é escrito em falhas ou quando explicit_explain=True.
    """
    global _current_session
    session_id = uuid.uuid4().hex[:8]
    _current_session = {
        "session_id": session_id,
        "captcha_type": captcha_type,
        "provider": provider,
        "model": model or "default",
        "started_at": datetime.now().isoformat(),
        "explain_reasoning": True,
        "explicit_explain": explicit_explain,
    }
    return session_id


def is_reasoning_enabled():
    return bool(_current_session and _current_session.get("explain_reasoning"))


def get_current_session():
    return _current_session


def get_session_entries():
    """Retorna entradas do log pertencentes à sessão atual."""
    if not _current_session:
        return []
    session_id = _current_session["session_id"]
    _ensure_log_file()
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        logs = json.load(f)
    return [entry for entry in logs if entry.get("session_id") == session_id]


def _step_label(entry):
    extra = entry.get("extra") or {}
    step = extra.get("step")
    labels = {
        "distance": "Cálculo de distância do slider",
        "correction": "Correção de alinhamento",
        "direction": "Direção de correção",
        "best_fit": "Seleção do melhor encaixe",
        "instructions": "Identificação do objeto alvo",
        "tile_check": "Verificação de tile",
    }
    if step in labels:
        label = labels[step]
        if step == "tile_check" and extra.get("object"):
            label += f" ({extra['object']})"
        return label
    return entry.get("captcha_type", "passo")


def finalize_session(success, details=None):
    """Gera relatório Markdown da sessão (se --explain) e limpa o estado."""
    global _current_session
    if not _current_session:
        return None

    session = _current_session
    should_report = (not success) or session.get("explicit_explain", False)
    if not should_report:
        _current_session = None
        return None
    entries = [
        e for e in get_session_entries()
        if (e.get("extra") or {}).get("step") != "start"
    ]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(
        LOG_DIR,
        f"reasoning_{timestamp}_{session['captcha_type']}.md",
    )
    os.makedirs(LOG_DIR, exist_ok=True)

    status = "SUCESSO" if success else "FALHA"
    lines = [
        "# Relatório de Raciocínio da IA",
        "",
        f"- **Sessão:** {session['session_id']}",
        f"- **Tipo:** {session['captcha_type']}",
        f"- **Provider:** {session['provider']} / {session['model']}",
        f"- **Início:** {session['started_at']}",
        f"- **Resultado:** {status}",
    ]
    if details:
        lines.append(f"- **Detalhes:** {details}")
    lines.extend(["", "---", ""])

    if not entries:
        lines.append("_Nenhuma chamada à IA registrada nesta sessão._")
    else:
        for i, entry in enumerate(entries, 1):
            lines.append(f"## Passo {i} — {_step_label(entry)}")
            lines.append("")
            lines.append(f"**Resposta da IA:** `{entry.get('ai_response', 'N/A')}`")
            lines.append("")
            reasoning = entry.get("reasoning")
            if reasoning:
                lines.append("**Raciocínio:**")
                lines.append(reasoning)
            else:
                lines.append("_Raciocínio não disponível para este passo._")
            lines.append("")
            lines.append("---")
            lines.append("")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"[LOG] Relatório de raciocínio salvo em {report_path}")
    _current_session = None
    return report_path


def log_attempt(captcha_type, provider, model, prompt, ai_response, success=None, extra=None, reasoning=None):
    """
    Registra uma tentativa de resolução de CAPTCHA.
    """
    _ensure_log_file()

    entry = {
        "session_id": _current_session["session_id"] if _current_session else None,
        "timestamp": datetime.now().isoformat(),
        "captcha_type": captcha_type,
        "provider": provider,
        "model": model,
        "prompt": prompt[:500] if prompt else None,
        "ai_response": str(ai_response) if ai_response is not None else None,
        "reasoning": reasoning,
        "success": success,
        "extra": extra,
    }

    with _log_lock:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs = json.load(f)
        logs.append(entry)
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)

    print(f"[LOG] {captcha_type} | {provider}/{model} | resposta: {str(ai_response)[:80] if ai_response else 'N/A'}")


def log_result(success, captcha_type=None, details=None):
    """
    Atualiza os registros da sessão atual com o resultado final.
    """
    _ensure_log_file()

    session_id = _current_session["session_id"] if _current_session else None

    with _log_lock:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs = json.load(f)

        updated = False
        for entry in logs:
            if session_id and entry.get("session_id") != session_id:
                continue
            entry["success"] = success
            if details:
                if entry.get("extra") is None:
                    entry["extra"] = {}
                entry["extra"]["result_details"] = details
            updated = True

        if not updated:
            logs.append({
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "captcha_type": (_current_session or {}).get("captcha_type") or captcha_type,
                "provider": (_current_session or {}).get("provider"),
                "model": (_current_session or {}).get("model"),
                "prompt": None,
                "ai_response": None,
                "reasoning": None,
                "success": success,
                "extra": {"result_details": details} if details else None,
            })

        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)

    status = "SUCESSO" if success else "FALHA"
    print(f"[LOG] Resultado: {status}")


def _classify_error(error_str):
    """Classifica o tipo de erro a partir da mensagem de exceção."""
    if not error_str:
        return None
    s = str(error_str)
    if "429" in s or "RESOURCE_EXHAUSTED" in s:
        return "api_quota"
    if "503" in s or "502" in s or "SERVICE_UNAVAILABLE" in s:
        return "api_unavailable"
    if "timeout" in s.lower() or "timed out" in s.lower():
        return "api_timeout"
    if "API_KEY_INVALID" in s or "API key not valid" in s:
        return "api_key_invalid"
    return None


def get_latest_session_metadata():
    """Retorna metadados da sessão mais recente em solve_log.json."""
    _ensure_log_file()
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        logs = json.load(f)
    if not logs:
        return {}

    last_sid = logs[-1].get("session_id")
    session_logs = [e for e in logs if e.get("session_id") == last_sid]
    ai_response = None
    ground_truth = None
    variant = None
    success = None
    error_type = None

    for entry in session_logs:
        if entry.get("ai_response"):
            ai_response = entry.get("ai_response")
        details = (entry.get("extra") or {}).get("result_details")
        if isinstance(details, dict):
            ground_truth = details.get("ground_truth") or ground_truth
            variant = details.get("variant") or variant
            ai_response = details.get("ai_response") or ai_response
            if details.get("error") and error_type is None:
                error_type = _classify_error(str(details["error"]))
        elif isinstance(details, str) and error_type is None:
            error_type = _classify_error(details)
        if entry.get("success") is not None:
            success = entry.get("success")

    return {
        "session_id": last_sid,
        "ai_response": ai_response,
        "ground_truth": ground_truth,
        "variant": variant,
        "success": success,
        "error_type": error_type,
    }


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
        "by_type": by_type,
    }
