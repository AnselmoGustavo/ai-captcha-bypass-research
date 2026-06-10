"""Gera grade 3x3 de CAPTCHA sintético com formas e cores controláveis."""

import json
import math
import random
from io import BytesIO

from PIL import Image, ImageDraw

SHAPES = ["circle", "square", "triangle", "star", "hexagon"]

COLORS = {
    "red":    (220,  50,  50),
    "blue":   ( 50, 100, 220),
    "green":  ( 50, 180,  80),
    "yellow": (220, 200,  50),
    "purple": (150,  50, 200),
}

SHAPE_PT = {
    "circle":   "círculo",
    "square":   "quadrado",
    "triangle": "triângulo",
    "star":     "estrela",
    "hexagon":  "hexágono",
}
SHAPE_PT_PLURAL = {
    "circle":   "círculos",
    "square":   "quadrados",
    "triangle": "triângulos",
    "star":     "estrelas",
    "hexagon":  "hexágonos",
}
COLOR_PT = {
    "red":    "vermelho",
    "blue":   "azul",
    "green":  "verde",
    "yellow": "amarelo",
    "purple": "roxo",
}
COLOR_PT_PLURAL_F = {
    "red":    "vermelhas",
    "blue":   "azuis",
    "green":  "verdes",
    "yellow": "amarelas",
    "purple": "roxas",
}

GRID_SIZE = 9

DEFAULT_VARIANT = {
    "target_kind":     "shape",   # shape | color | both
    "target_count":    3,         # tiles matching (1-6)
    "distractor_mode": "random",  # random | similar
    "noise":           0,         # 0-3
    "tile_size":       80,
}


def parse_variant(params):
    variant = dict(DEFAULT_VARIANT)
    for key in DEFAULT_VARIANT:
        if key not in params or params[key] in (None, ""):
            continue
        raw = params[key]
        if key in ("target_count", "noise", "tile_size"):
            try:
                variant[key] = int(raw)
            except ValueError:
                pass
        else:
            variant[key] = raw
    if variant["target_kind"] not in ("shape", "color", "both"):
        variant["target_kind"] = "shape"
    if variant["distractor_mode"] not in ("random", "similar"):
        variant["distractor_mode"] = "random"
    variant["target_count"] = max(1, min(variant["target_count"], GRID_SIZE - 1))
    return variant


def check(solution, submission):
    """Compara conjunto de índices corretos com os selecionados pelo bot."""
    return set(solution) == {int(x) for x in submission}


# ── shape drawing ─────────────────────────────────────────────────────────────

def _polygon_pts(cx, cy, r, n, start_deg=0):
    return [
        (cx + r * math.cos(math.radians(start_deg + 360 * i / n)),
         cy + r * math.sin(math.radians(start_deg + 360 * i / n)))
        for i in range(n)
    ]


def _star_pts(cx, cy, r_out, r_in, n=5):
    pts = []
    for i in range(2 * n):
        r = r_out if i % 2 == 0 else r_in
        angle = math.radians(-90 + 180 * i / n)
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    return pts


def _draw_shape(draw, shape, color_rgb, size):
    pad = int(size * 0.18)
    x0, y0, x1, y1 = pad, pad, size - pad, size - pad
    cx, cy = size / 2, size / 2
    r = (size / 2) - pad
    if shape == "circle":
        draw.ellipse([x0, y0, x1, y1], fill=color_rgb)
    elif shape == "square":
        draw.rectangle([x0, y0, x1, y1], fill=color_rgb)
    elif shape == "triangle":
        draw.polygon([(cx, y0), (x1, y1), (x0, y1)], fill=color_rgb)
    elif shape == "star":
        draw.polygon(_star_pts(cx, cy, r, r * 0.42), fill=color_rgb)
    elif shape == "hexagon":
        draw.polygon(_polygon_pts(cx, cy, r, 6, start_deg=-30), fill=color_rgb)


def _make_tile(shape, color_key, noise, rng, tile_size):
    img = Image.new("RGB", (tile_size, tile_size), (245, 245, 245))
    draw = ImageDraw.Draw(img)
    _draw_shape(draw, shape, COLORS[color_key], tile_size)
    for _ in range(noise * 12):
        draw.point(
            (rng.randint(0, tile_size - 1), rng.randint(0, tile_size - 1)),
            fill=(rng.randint(80, 200),) * 3,
        )
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ── tile selection logic ───────────────────────────────────────────────────────

def _matches(shape, color_key, target_shape, target_color, target_kind):
    if target_kind == "shape":
        return shape == target_shape
    if target_kind == "color":
        return color_key == target_color
    return shape == target_shape and color_key == target_color


def _pick_distractor(target_shape, target_color, target_kind, distractor_mode, rng):
    for _ in range(200):
        if distractor_mode == "similar":
            if target_kind == "both":
                if rng.random() < 0.5:
                    s, c = target_shape, rng.choice([c for c in COLORS if c != target_color])
                else:
                    s, c = rng.choice([sh for sh in SHAPES if sh != target_shape]), target_color
            elif target_kind == "shape":
                s, c = target_shape, rng.choice([c for c in COLORS if c != target_color])
            else:
                s, c = rng.choice([sh for sh in SHAPES if sh != target_shape]), target_color
        else:
            s = rng.choice(SHAPES)
            c = rng.choice(list(COLORS.keys()))
        if not _matches(s, c, target_shape, target_color, target_kind):
            return s, c
    # guaranteed fallback
    return next(sh for sh in SHAPES if sh != target_shape), next(co for co in COLORS if co != target_color)


def _build_instruction(target_shape, target_color, target_kind):
    if target_kind == "shape":
        return (
            f"Selecione todos os {SHAPE_PT_PLURAL[target_shape]}",
            SHAPE_PT[target_shape],
        )
    if target_kind == "color":
        return (
            f"Selecione todas as figuras {COLOR_PT_PLURAL_F[target_color]}",
            f"figura {COLOR_PT[target_color]}",
        )
    return (
        f"Selecione todos os {SHAPE_PT_PLURAL[target_shape]} {COLOR_PT[target_color]}s",
        f"{SHAPE_PT[target_shape]} {COLOR_PT[target_color]}",
    )


# ── public API ─────────────────────────────────────────────────────────────────

def generate_grid_captcha(variant, seed=None):
    """
    Gera 9 tiles PNG, a solução e a instrução.

    Returns:
        tiles (list[bytes])       — 9 imagens PNG, uma por posição da grade
        solution (list[int])      — índices (0-8) que são a resposta correta
        instruction (str)         — texto em português para o usuário
        target_description (str)  — descrição curta para o prompt da IA
        variant (dict)            — variante final com _target_shape/_target_color
    """
    rng = random.Random(seed)
    v = dict(variant)

    target_shape = rng.choice(SHAPES)
    target_color = rng.choice(list(COLORS.keys()))
    target_kind = v["target_kind"]

    instruction, target_description = _build_instruction(target_shape, target_color, target_kind)

    positions = list(range(GRID_SIZE))
    rng.shuffle(positions)
    solution = sorted(positions[: v["target_count"]])
    non_solution = positions[v["target_count"] :]

    tiles_spec = {}
    for idx in solution:
        if target_kind == "shape":
            tiles_spec[idx] = (target_shape, rng.choice(list(COLORS.keys())))
        elif target_kind == "color":
            tiles_spec[idx] = (rng.choice(SHAPES), target_color)
        else:
            tiles_spec[idx] = (target_shape, target_color)

    for idx in non_solution:
        tiles_spec[idx] = _pick_distractor(target_shape, target_color, target_kind, v["distractor_mode"], rng)

    tiles = [_make_tile(*tiles_spec[i], v["noise"], rng, v["tile_size"]) for i in range(GRID_SIZE)]

    v["_target_shape"] = target_shape
    v["_target_color"] = target_color

    return tiles, solution, instruction, target_description, v


def variant_to_json(variant):
    return json.dumps({k: v for k, v in variant.items() if not k.startswith("_")}, ensure_ascii=False)
