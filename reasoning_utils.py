"""
Segunda chamada à API de IA para documentar o raciocínio por trás de cada resposta.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI
from google import genai
from google.genai import types

from ai_utils import image_to_base64

load_dotenv()

gemini_client = None
if os.getenv("GOOGLE_API_KEY"):
    gemini_client = genai.Client()

EXPLAIN_PROMPT = (
    "Você respondeu \"{answer}\" para a seguinte tarefa: {task_description}\n\n"
    "Explique passo a passo em português como chegou a essa conclusão: "
    "quais elementos visuais ou auditivos identificou, que padrões reconheceu "
    "e por que confia na resposta. Seja objetivo mas detalhado (3 a 6 frases)."
)


def explain_after_answer(provider, model, media_path, media_type, task_description, short_answer):
    """Obtém explicação do raciocínio da IA após a resposta curta."""
    if not media_path or not os.path.exists(media_path):
        return None
    prompt = EXPLAIN_PROMPT.format(
        answer=short_answer,
        task_description=task_description,
    )
    try:
        if provider == "openai":
            return explain_openai(model, media_path, media_type, prompt)
        return explain_gemini(model, media_path, media_type, prompt)
    except Exception as e:
        print(f"[REASONING] Falha ao obter raciocínio: {e}")
        return None


def explain_gemini(model, media_path, media_type, prompt):
    if not gemini_client:
        return None
    model_to_use = model if model else "gemini-2.5-flash"
    with open(media_path, "rb") as f:
        media_bytes = f.read()

    if media_type == "audio":
        mime = "audio/mpeg"
        if media_path.lower().endswith(".wav"):
            mime = "audio/wav"
        part = types.Part.from_bytes(data=media_bytes, mime_type=mime)
        response = gemini_client.models.generate_content(
            model=model_to_use,
            contents=[part, prompt],
        )
    else:
        part = types.Part.from_bytes(data=media_bytes, mime_type="image/png")
        response = gemini_client.models.generate_content(
            model=model_to_use,
            contents=[part, prompt],
        )
    return response.text.strip() if response.text else None


def explain_openai(model, media_path, media_type, prompt):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    model_to_use = model if model else "gpt-4o"

    if media_type == "audio":
        with open(media_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="gpt-4o-transcribe",
                file=audio_file,
                prompt="Transcreva o áudio para contexto.",
            )
        response = client.chat.completions.create(
            model=model_to_use,
            messages=[
                {
                    "role": "user",
                    "content": f"Transcrição do áudio: {transcription.text}\n\n{prompt}",
                }
            ],
            temperature=0.3,
            max_tokens=512,
        )
    else:
        base64_image = image_to_base64(media_path)
        response = client.chat.completions.create(
            model=model_to_use,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                        },
                    ],
                }
            ],
            temperature=0.3,
            max_tokens=512,
        )
    return response.choices[0].message.content.strip()
