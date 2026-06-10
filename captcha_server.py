"""
Servidor Flask local de CAPTCHAs customizados para experimentos acadêmicos.

Uso:
    python captcha_server.py
    Abrir http://localhost:5000/text
"""

import os
import uuid
from flask import Flask, jsonify, make_response, render_template, request, session

from captcha_generators.text_captcha import (
    generate_text_captcha,
    parse_variant,
    parse_variant_complicated,
    variant_to_json,
)
from captcha_generators.grid_captcha import (
    generate_grid_captcha,
    parse_variant as parse_grid_variant,
    variant_to_json as grid_variant_to_json,
    check as check_grid,
)

app = Flask(__name__)
app.secret_key = os.getenv("CAPTCHA_SERVER_SECRET", "dev-captcha-lab-secret")

# Cache em memória — imagens não cabem no cookie de sessão Flask
_image_cache = {}   # token → bytes  (texto)
_grid_cache = {}    # token → list[bytes]  (grade)
_seed_answers = {}


@app.route("/")
def index():
    return (
        "<h1>CAPTCHA Lab</h1>"
        "<p><a href='/text'>CAPTCHA de texto simples</a></p>"
        "<p><a href='/complicated_text'>CAPTCHA de texto distorcido</a></p>"
        "<p><a href='/recaptcha_v2'>reCAPTCHA v2 sintético (grade)</a></p>"
        "<p>Exemplos: "
        "<a href='/text?noise=3&rotation=20'>/text?noise=3&rotation=20</a> | "
        "<a href='/recaptcha_v2?target_kind=both&target_count=3'>/recaptcha_v2?target_kind=both</a></p>"
    )


def _render_text_based_captcha(parser_fn, captcha_type, captcha_title):
    seed = request.args.get("seed")
    seed = int(seed) if seed is not None and str(seed).lstrip("-").isdigit() else None
    variant = parser_fn(request.args.to_dict())
    image_bytes, answer, variant = generate_text_captcha(variant, seed=seed)

    token = uuid.uuid4().hex
    _image_cache[token] = image_bytes
    session["image_token"] = token
    session["captcha_type"] = captcha_type
    session["answer"] = answer
    session["variant"] = variant
    if seed is not None:
        _seed_answers[seed] = {"answer": answer, "variant": variant}

    variant_json = variant_to_json(variant)
    variant_display = ", ".join(f"{k}={v}" for k, v in variant.items())
    return render_template(
        "text_captcha.html",
        captcha_title=captcha_title,
        variant_json=variant_json,
        variant_display=variant_display,
    )


@app.route("/text")
def text_captcha_page():
    return _render_text_based_captcha(parse_variant, "text", "CAPTCHA de Texto")


@app.route("/complicated_text")
def complicated_text_captcha_page():
    return _render_text_based_captcha(parse_variant_complicated, "complicated_text", "CAPTCHA de Texto Distorcido")


@app.route("/recaptcha_v2")
def recaptcha_v2_captcha_page():
    seed = request.args.get("seed")
    seed = int(seed) if seed is not None and str(seed).lstrip("-").isdigit() else None
    variant = parse_grid_variant(request.args.to_dict())
    tiles, solution, instruction, target_description, variant = generate_grid_captcha(variant, seed=seed)

    token = uuid.uuid4().hex
    _grid_cache[token] = tiles
    session["image_token"] = token
    session["captcha_type"] = "recaptcha_v2"
    session["solution"] = solution
    session["variant"] = {k: v for k, v in variant.items() if not k.startswith("_")}
    if seed is not None:
        _seed_answers[seed] = {"solution": solution, "variant": session["variant"]}

    return render_template(
        "grid_captcha.html",
        instruction=instruction,
        target_description=target_description,
        grid_token=token,
        tile_size=variant["tile_size"],
        variant_json=grid_variant_to_json(variant),
    )


@app.route("/grid-tile/<token>/<int:idx>.png")
def grid_tile(token, idx):
    tiles = _grid_cache.get(token)
    if not tiles or idx < 0 or idx >= len(tiles):
        return "Tile não encontrado", 404
    resp = make_response(tiles[idx])
    resp.headers["Content-Type"] = "image/png"
    return resp


@app.route("/captcha-image.png")
def captcha_image():
    token = session.get("image_token")
    image_bytes = _image_cache.get(token) if token else None
    if not image_bytes:
        return "Sessão expirada. Recarregue /text", 404
    resp = make_response(image_bytes)
    resp.headers["Content-Type"] = "image/png"
    return resp


@app.route("/api/verify", methods=["POST"])
def verify():
    data = request.get_json(silent=True) or {}
    captcha_type = session.get("captcha_type", "text")
    if captcha_type == "recaptcha_v2":
        submitted = data.get("selected") or []
        solution = session.get("solution") or []
        success = check_grid(solution, submitted)
    else:
        user_answer = (data.get("answer") or "").strip()
        correct = session.get("answer", "")
        success = user_answer.upper() == correct.upper()
    return jsonify({"success": success, "message": "Correto!" if success else "Incorreto."})


@app.route("/api/variant")
def get_variant():
    """Metadados da variante atual (para o bot registrar nos logs)."""
    return jsonify({"variant": session.get("variant", {}), "session_active": "answer" in session})


@app.route("/api/answer")
def get_answer():
    """Resposta correta — apenas localhost, para análise pós-experimento."""
    remote = request.remote_addr
    if remote not in ("127.0.0.1", "::1", None):
        return jsonify({"error": "Acesso restrito a localhost"}), 403
    captcha_type = session.get("captcha_type", "text")
    if captcha_type == "recaptcha_v2":
        return jsonify({"solution": session.get("solution"), "variant": session.get("variant", {})})
    return jsonify({"answer": session.get("answer"), "variant": session.get("variant", {})})


@app.route("/api/answer_by_seed/<int:seed>")
def get_answer_by_seed(seed):
    """Resposta por seed — para logging sem cookie do browser."""
    remote = request.remote_addr
    if remote not in ("127.0.0.1", "::1", None):
        return jsonify({"error": "Acesso restrito a localhost"}), 403
    entry = _seed_answers.get(seed)
    if not entry:
        return jsonify({"error": "Seed não encontrado"}), 404
    return jsonify(entry)


if __name__ == "__main__":
    print("CAPTCHA Lab em http://localhost:5000")
    print("Exemplo: http://localhost:5000/text?noise=2&rotation=15&seed=42")
    app.run(host="127.0.0.1", port=5000, debug=False)
