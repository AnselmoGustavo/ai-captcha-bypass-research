"""Gera imagens de CAPTCHA de texto com parâmetros controláveis."""

import json
import math
import random
import string
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont


CHAR_SETS = {
    "alnum": string.ascii_uppercase + string.digits,
    "mixed_case": string.ascii_letters + string.digits,
    "symbols": string.ascii_letters + string.digits + "O0Il1",
}

DEFAULT_VARIANT = {
    "noise": 0,
    "rotation": 0,
    "overlap": 0,
    "length": 5,
    "font_size": 36,
    "char_set": "alnum",
    "bg_color": "#f0f0f0",
    "fg_color": "#1a1a1a",
    "wave": 0,
}


def parse_variant(params):
    """Mescla query params com defaults e normaliza tipos."""
    variant = dict(DEFAULT_VARIANT)
    for key in DEFAULT_VARIANT:
        if key not in params or params[key] in (None, ""):
            continue
        raw = params[key]
        if key in ("noise", "overlap", "length", "font_size", "wave", "rotation"):
            variant[key] = int(raw)
        else:
            variant[key] = raw
    if variant["char_set"] not in CHAR_SETS:
        variant["char_set"] = "alnum"
    return variant


def _get_font(size):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        try:
            return ImageFont.truetype("C:/Windows/Fonts/arial.ttf", size)
        except OSError:
            return ImageFont.load_default()


def generate_text_captcha(variant, seed=None):
    """
    Gera PNG em bytes e a string correta.
    Returns: (image_bytes, answer, variant_dict)
    """
    rng = random.Random(seed)
    v = dict(variant)
    charset = CHAR_SETS[v["char_set"]]
    answer = "".join(rng.choice(charset) for _ in range(v["length"]))

    width = max(180, v["length"] * v["font_size"] + 40)
    height = v["font_size"] + 60
    img = Image.new("RGB", (width, height), v["bg_color"])
    draw = ImageDraw.Draw(img)
    font = _get_font(v["font_size"])

    x = 20
    for i, char in enumerate(answer):
        char_img = Image.new("RGBA", (v["font_size"] + 10, v["font_size"] + 20), (0, 0, 0, 0))
        char_draw = ImageDraw.Draw(char_img)
        char_draw.text((5, 5), char, fill=v["fg_color"], font=font)

        angle = rng.randint(-v["rotation"], v["rotation"]) if v["rotation"] else 0
        char_img = char_img.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)

        if v["wave"]:
            y_offset = int(math.sin(i * 0.8) * v["wave"] * 4)
        else:
            y_offset = 0

        overlap_px = v["overlap"] * 4
        img.paste(char_img, (x - overlap_px, 20 + y_offset), char_img)
        x += v["font_size"] - overlap_px + rng.randint(2, 8)

    for _ in range(v["noise"] * 8):
        x1, y1 = rng.randint(0, width - 1), rng.randint(0, height - 1)
        x2, y2 = rng.randint(0, width - 1), rng.randint(0, height - 1)
        draw.line([(x1, y1), (x2, y2)], fill=v["fg_color"], width=1)
    for _ in range(v["noise"] * 15):
        draw.point((rng.randint(0, width - 1), rng.randint(0, height - 1)), fill=v["fg_color"])

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue(), answer, v


def variant_to_json(variant):
    return json.dumps(variant, ensure_ascii=False)
