import os
import base64
import re
import time
from dotenv import load_dotenv
from openai import OpenAI, APIStatusError
from google import genai
from google.genai import types
from solve_logger import log_attempt, is_reasoning_enabled

load_dotenv()

# --- Client Initialization ---
gemini_client = None
if os.getenv("GOOGLE_API_KEY"):
    gemini_client = genai.Client()


def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def _log_with_reasoning(captcha_type, provider, model, prompt, result, media_path=None,
                        media_type="image", task_desc=None, extra=None):
    reasoning = None
    if is_reasoning_enabled() and media_path and os.path.exists(media_path):
        from reasoning_utils import explain_after_answer
        reasoning = explain_after_answer(
            provider, model, media_path, media_type,
            task_desc or captcha_type, str(result),
        )
    log_attempt(captcha_type, provider, model, prompt, result, reasoning=reasoning, extra=extra)


# --- OpenAI Functions ---
def ask_text_to_chatgpt(image_path, model=None):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    base64_image = image_to_base64(image_path)
    short_prompt = ("Act as a blind person assistant. Read the text from the image and give me only the text answer.")
    model_to_use = model if model else "gpt-4o"
    response = client.chat.completions.create(
        model=model_to_use,
        messages=[
            {"role": "system", "content": [{"type": "text", "text": short_prompt}]},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}},
                {"type": "text", "text": "Give the only text from the image. If there is no text, give me empty string."}
            ]},
        ],
        temperature=1, max_tokens=256, top_p=1, frequency_penalty=0, presence_penalty=0
    )
    result = response.choices[0].message.content
    _log_with_reasoning("text", "openai", model_to_use, short_prompt, result, image_path,
                        task_desc="Reconhecer texto do CAPTCHA na imagem")
    return result

def ask_puzzle_distance_to_chatgpt(image_path, model=None):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    base64_image = image_to_base64(image_path)
    prompt = """
As an assistant designed to help a visually impaired individual, I need your keen observation to navigate the visual world around me by describing the relative positions and characteristics of objects in an image.

Specifically, I need your help with a CAPTCHA puzzle involving a slider. This is crucial for me to maintain my digital interactions and independence. Here's what I need you to do:

    Your Task: Carefully examine the provided image to identify the slider handle (the white circle with a vertical line in its center) and the target slot (the empty black rectangular area).

    My Goal: I need to drag the slider so that the middle vertical line of the slider handle aligns exactly with the horizontal center of the empty slot.

    The Information I Need: Please calculate the horizontal pixel distance from the current center of the slider handle to the center of the empty slot.

    Important Notes for Calculation:

        The movement should be horizontal only.

        If the handle is already perfectly aligned with the slot, please return 0.

        Do not return a negative number — you can assume the handle always starts to the left of the target.

        Please cap the value at 260 pixels; if the calculation exceeds this, still report 260.

        Return only the integer. No units, no explanation, no additional text. It's vital that I get this information quickly and precisely.

Expected Output Example: 134 (a single integer only)

"""
    model_to_use = model if model else "gpt-4o"
    
    response = client.chat.completions.create(
        model=model_to_use,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}]}
        ],
        temperature=0, max_tokens=50
    )
    content = response.choices[0].message.content.strip()
    match = re.search(r'-?\d+', content)
    result = match.group(0) if match else None
    if result is None:
        print(f"Warning: OpenAI distance response did not contain an integer: '{content}'.")
    _log_with_reasoning("puzzle", "openai", model_to_use, prompt[:200], result or content, image_path,
                        task_desc="Calcular distância horizontal em pixels do slider até o slot", extra={"step": "distance"})
    return result

def ask_puzzle_correction_to_chatgpt(image_path, model=None):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    base64_image = image_to_base64(image_path)
    prompt = """
**CRITICAL ALIGNMENT CORRECTION.**
Your task is to determine the final pixel adjustment required to **perfectly align** the puzzle piece into its slot.
* A **perfect fit** means the puzzle piece sits **flush** in the slot with **no visible gray gaps** on either side.
* **Look carefully**: If you see **any gray space** between the piece and the slot, then the alignment is incorrect.
* If the piece is **too far to the left**, provide a **positive integer** (move right).
* If the piece is **too far to the right**, provide a **negative integer** (move left).
* If the alignment is **already perfect**, respond with `0`.
⚠️ **Do not guess**. Only respond with a non-zero value if you can clearly identify a misalignment.
⚠️ **Output only the integer. Nothing else. No units, no words.**
"""
    model_to_use = model if model else "gpt-4o"

    response = client.chat.completions.create(
        model=model_to_use,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}]}
        ],
        temperature=0, max_tokens=50
    )
    content = response.choices[0].message.content.strip()
    match = re.search(r'-?\d+', content)
    result = match.group(0) if match else None
    if result is None:
        print(f"Warning: OpenAI correction response did not contain an integer: '{content}'.")
    _log_with_reasoning("puzzle", "openai", model_to_use, prompt[:200], result or content, image_path,
                        task_desc="Corrigir alinhamento fino da peça do puzzle", extra={"step": "correction"})
    return result

def ask_puzzle_correction_direction_to_openai(image_path, model=None):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    base64_image = image_to_base64(image_path)
    prompt = (
        "You are an expert in visual analysis for automation. Your task is to determine the direction of movement needed to solve a slider puzzle. "
        "Analyze the provided image, which shows the result of a first attempt. The puzzle piece is the element that was moved from the left. The target is the empty, darker slot it needs to fit into. "
        "If the puzzle piece is to the LEFT of the target slot, you must respond with only a single '+' character. "
        "If the puzzle piece is to the RIGHT of the target slot, you must respond with only a single '-' character. "
        "Do not provide any other characters, words, or explanations. Your entire response must be either '+' or '-'."
    )
    model_to_use = model if model else "gpt-4o"
    response = client.chat.completions.create(
        model=model_to_use,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}]}
        ]
    )
    result = response.choices[0].message.content.strip()
    _log_with_reasoning("puzzle", "openai", model_to_use, prompt, result, image_path,
                        task_desc="Determinar direção de correção do slider (+ ou -)", extra={"step": "direction"})
    return result

def ask_best_fit_to_openai(image_paths, model=None):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = """
You are given multiple images of a puzzle CAPTCHA attempt. Your task is to select the image where the puzzle piece is placed most correctly into the slot.
The most important rule is that there must be no visible black gap or dark space between the piece and the slot edges. An image with any gap must be disqualified.
Among images with no gaps, choose the one with the most precise fit and least misalignment.
Ignore all other UI elements like sliders or buttons.
Respond with only the index number (e.g., 0, 1, 2) of the best image.
"""
    
    user_content = [{"type": "text", "text": prompt}]
    for path in image_paths:
        base64_image = image_to_base64(path)
        user_content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}})

    model_to_use = model if model else "gpt-4o"

    response = client.chat.completions.create(
        model=model_to_use,
        messages=[
            {"role": "system", "content": "You are an expert at analyzing puzzle captcha images."},
            {"role": "user", "content": user_content}
        ]
    )
    content = response.choices[0].message.content.strip()
    match = re.search(r'\d+', content)
    result = match.group(0) if match else None
    if result is None:
        print(f"Warning: OpenAI best-fit response did not contain an integer: '{content}'.")
    media_path = image_paths[0] if image_paths else None
    _log_with_reasoning("puzzle", "openai", model_to_use, prompt[:200], result or content, media_path,
                        task_desc="Selecionar a imagem com melhor encaixe do puzzle", extra={"step": "best_fit"})
    return result

def ask_audio_to_openai(audio_path, model=None):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = "what is the captcha answer?"
    model_to_use = model if model else "gpt-4o-transcribe"
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with open(audio_path, "rb") as audio_file:
                response = client.audio.transcriptions.create(model=model_to_use, file=audio_file, prompt=prompt)
            cleaned_transcription = re.sub(r'[^a-zA-Z0-9]', '', response.text.strip())
            _log_with_reasoning("audio", "openai", model_to_use, prompt, cleaned_transcription, audio_path,
                                media_type="audio", task_desc="Transcrever letras do CAPTCHA de áudio")
            return cleaned_transcription
        except APIStatusError as e:
            if e.status_code == 503 and attempt < max_retries - 1:
                wait_time = 3 * (attempt + 1)
                print(f"OpenAI API is overloaded (503). Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"OpenAI API error after retries: {e}")
                raise e
        except Exception as e:
            print(f"An unexpected error occurred during OpenAI audio transcription: {e}")
            raise e
    raise Exception("Failed to get transcription from OpenAI after multiple retries.")

def ask_recaptcha_instructions_to_chatgpt(image_path, model=None):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    base64_image = image_to_base64(image_path)
    prompt = "Analyze the blue instruction bar in the image. Identify the primary object the user is asked to select. For example, if it says 'Select all squares with motorcycles', the object is 'motorcycles'. Respond with only the single object name in lowercase. If the instruction is to 'click skip', return 'skip'."
    model_to_use = model if model else "gpt-4o"
    response = client.chat.completions.create(
        model=model_to_use,
        messages=[
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
            ]}
        ],
        temperature=0, max_tokens=50
    )
    result = response.choices[0].message.content.strip().lower()
    _log_with_reasoning("recaptcha_v2", "openai", model_to_use, prompt, result, image_path,
                        task_desc="Identificar objeto alvo nas instruções do reCAPTCHA", extra={"step": "instructions"})
    return result

def ask_if_tile_contains_object_chatgpt(image_path, object_name, model=None):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    base64_image = image_to_base64(image_path)
    prompt = f"Does this image clearly contain a '{object_name}' or a recognizable part of a '{object_name}'? Respond only with 'true' if you are certain. If you are unsure or cannot tell confidently, respond only with 'false'."
    model_to_use = model if model else "gpt-4o"
    response = client.chat.completions.create(
        model=model_to_use,
        messages=[
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
            ]}
        ],
        temperature=0, max_tokens=10
    )
    result = response.choices[0].message.content.strip().lower()
    _log_with_reasoning("recaptcha_v2", "openai", model_to_use, prompt, result, image_path,
                        task_desc=f"Verificar se o tile contém '{object_name}'", extra={"step": "tile_check", "object": object_name})
    return result

# --- Gemini Functions ---
def ask_text_to_gemini(image_path, model=None):
    if not gemini_client: raise Exception("Gemini API key not configured.")
    prompt = "Act as a blind person assistant. Read the text from the image and give me only the text answer."
    with open(image_path, 'rb') as f: image_bytes = f.read()
    model_to_use = model if model else "gemini-2.5-pro"
    response = gemini_client.models.generate_content(model=model_to_use, contents=[types.Part.from_bytes(data=image_bytes, mime_type='image/png'), prompt])
    result = response.text.strip()
    _log_with_reasoning("text", "gemini", model_to_use, prompt, result, image_path,
                        task_desc="Reconhecer texto do CAPTCHA na imagem")
    return result

def ask_puzzle_distance_to_gemini(image_path, model=None):
    if not gemini_client: raise Exception("Gemini API key not configured.")
    prompt = """
Analyze the image and determine the correct slider movement needed to solve the puzzle CAPTCHA.
* The goal is to drag the slider **so that the center line of the three-line slider handle** (the vertical bar in the middle of the white circle) aligns **exactly with the horizontal center of the black slot** shown in the puzzle area.
* The alignment is considered correct only if the **middle vertical line of the handle** is in **perfect vertical alignment** with the **center of the empty slot**.
* You must calculate the **horizontal pixel distance** from the current center of the handle to the center of the empty slot.
* The movement should be **horizontal only**.
* Return the number of **pixels to move the slider to the right** to reach perfect alignment.
* **If the handle is already perfectly aligned with the slot, return 0.**
* **Do not return a negative number** — assume the handle always starts to the **left** of the target.
* **Cap the value at 260** if it exceeds this maximum range.
* **Return only the integer**. No units. No explanation.
**Expected output:** A single integer (e.g., `134`)

"""
    with open(image_path, 'rb') as f: image_bytes = f.read()
    model_to_use = model if model else "gemini-2.5-pro"
    response = gemini_client.models.generate_content(
        model=model_to_use,
        contents=[types.Part.from_bytes(data=image_bytes, mime_type='image/png'), prompt]
    )
    result = response.text
    _log_with_reasoning("puzzle", "gemini", model_to_use, prompt[:200], result, image_path,
                        task_desc="Calcular distância horizontal em pixels do slider até o slot", extra={"step": "distance"})
    return result

def ask_puzzle_correction_to_gemini(image_path, model=None):
    if not gemini_client: raise Exception("Gemini API key not configured.")
    prompt = """
**CRITICAL ALIGNMENT CORRECTION.**
Your task is to determine the final pixel adjustment required to **perfectly align** the puzzle piece into its slot.
* A **perfect fit** means the puzzle piece sits **flush** in the slot with **no visible gray gaps** on either side.
* **Look carefully**: If you see **any gray space** between the piece and the slot, then the alignment is incorrect.
* If the piece is **too far to the left**, provide a **positive integer** (move right).
* If the piece is **too far to the right**, provide a **negative integer** (move left).
* If the alignment is **already perfect**, respond with `0`.
⚠️ **Do not guess**. Only respond with a non-zero value if you can clearly identify a misalignment.
⚠️ **Output only the integer. Nothing else. No units, no words.**
"""
    with open(image_path, 'rb') as f: image_bytes = f.read()
    model_to_use = model if model else "gemini-2.5-pro"
    response = gemini_client.models.generate_content(
        model=model_to_use,
        contents=[types.Part.from_bytes(data=image_bytes, mime_type='image/png'), prompt]
    )
    result = response.text
    _log_with_reasoning("puzzle", "gemini", model_to_use, prompt[:200], result, image_path,
                        task_desc="Corrigir alinhamento fino da peça do puzzle", extra={"step": "correction"})
    return result

def ask_puzzle_correction_direction_to_gemini(image_path, model=None):
    if not gemini_client: raise Exception("Gemini API key not configured.")
    prompt = (
        "You are an expert in visual analysis for automation. Your task is to determine the direction of movement needed to solve a slider puzzle. "
        "Analyze the provided image, which shows the result of a first attempt. The puzzle piece is the element that was moved from the left. The target is the empty, darker slot it needs to fit into. "
        "If the puzzle piece is to the LEFT of the target slot, you must respond with only a single '+' character. "
        "If the puzzle piece is to the RIGHT of the target slot, you must respond with only a single '-' character. "
        "Do not provide any other characters, words, or explanations. Your entire response must be either '+' or '-'."
    )
    with open(image_path, 'rb') as f: image_bytes = f.read()
    model_to_use = model if model else "gemini-2.5-pro"
    response = gemini_client.models.generate_content(
        model=model_to_use,
        contents=[types.Part.from_bytes(data=image_bytes, mime_type='image/png'), prompt]
    )
    result = response.text.strip()
    _log_with_reasoning("puzzle", "gemini", model_to_use, prompt, result, image_path,
                        task_desc="Determinar direção de correção do slider (+ ou -)", extra={"step": "direction"})
    return result

def ask_best_fit_to_gemini(image_paths, model=None):
    if not gemini_client: raise Exception("Gemini API key not configured.")
    prompt = """
You are given multiple images of a puzzle CAPTCHA attempt. Your task is to select the image where the puzzle piece is placed most correctly into the slot.
The most important rule is that there must be no visible black gap or dark space between the piece and the slot edges. An image with any gap must be disqualified.
Among images with no gaps, choose the one with the most precise fit and least misalignment.
Ignore all other UI elements like sliders or buttons.
Respond with only the index number (e.g., 0, 1, 2) of the best image.
"""
    content_parts = [prompt]
    for path in image_paths:
        with open(path, 'rb') as f:
            image_bytes = f.read()
        content_parts.append(types.Part.from_bytes(data=image_bytes, mime_type='image/png'))

    model_to_use = model if model else "gemini-2.5-pro"
    response = gemini_client.models.generate_content(model=model_to_use, contents=content_parts)
    result = response.text.strip()
    media_path = image_paths[0] if image_paths else None
    _log_with_reasoning("puzzle", "gemini", model_to_use, prompt[:200], result, media_path,
                        task_desc="Selecionar a imagem com melhor encaixe do puzzle", extra={"step": "best_fit"})
    return result

def ask_audio_to_gemini(audio_path, model=None):
    if not gemini_client: raise Exception("Gemini API key not configured.")
    system_instruction = "The audio is in American English. Type only the letters you hear clearly and loudly spoken. Ignore any background words, sounds, or faint speech. Enter the letters in the exact order they are spoken."
    with open(audio_path, 'rb') as f: audio_bytes = f.read()
    audio_part = types.Part.from_bytes(data=audio_bytes, mime_type='audio/mpeg')
    model_to_use = model if model else "gemini-2.5-pro"
    response = gemini_client.models.generate_content(
        model=model_to_use,
        config=types.GenerateContentConfig(system_instruction=system_instruction),
        contents=["Transcribe the captcha from the audio file.", audio_part]
    )
    cleaned_transcription = re.sub(r'[^a-zA-Z0-9]', '', response.text.strip())
    _log_with_reasoning("audio", "gemini", model_to_use, system_instruction, cleaned_transcription, audio_path,
                        media_type="audio", task_desc="Transcrever letras do CAPTCHA de áudio")
    return cleaned_transcription

def ask_recaptcha_instructions_to_gemini(image_path, model=None):
    if not gemini_client: raise Exception("Gemini API key not configured.")
    prompt = """
    Analyze the blue instruction bar in the image. Identify the primary object the user is asked to select. 
    For example, if it says 'Select all squares with motorcycles', the object is 'motorcycles'. 
    Respond with only the single object name in lowercase. If the instruction is to 'click skip', return 'skip'.
    """
    with open(image_path, 'rb') as f: image_bytes = f.read()
    model_to_use = model if model else "gemini-2.5-pro"
    response = gemini_client.models.generate_content(model=model_to_use, contents=[types.Part.from_bytes(data=image_bytes, mime_type='image/png'), prompt])
    result = response.text.strip().lower()
    _log_with_reasoning("recaptcha_v2", "gemini", model_to_use, prompt.strip(), result, image_path,
                        task_desc="Identificar objeto alvo nas instruções do reCAPTCHA", extra={"step": "instructions"})
    return result

def ask_if_tile_contains_object_gemini(image_path, object_name, model=None):
    if not gemini_client: raise Exception("Gemini API key not configured.")
    prompt = f"Does this image clearly contain a '{object_name}' or a recognizable part of a '{object_name}'? Respond only with 'true' if you are certain. If you are unsure or cannot tell confidently, respond only with 'false'."
    with open(image_path, 'rb') as f: image_bytes = f.read()
    model_to_use = model if model else "gemini-2.5-pro"
    response = gemini_client.models.generate_content(model=model_to_use, contents=[types.Part.from_bytes(data=image_bytes, mime_type='image/png'), prompt])
    result = response.text.strip().lower()
    _log_with_reasoning("recaptcha_v2", "gemini", model_to_use, prompt, result, image_path,
                        task_desc=f"Verificar se o tile contém '{object_name}'", extra={"step": "tile_check", "object": object_name})
    return result
