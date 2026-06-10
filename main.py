import argparse
import json
import os
import sys
import time
import random
import re
import base64
import urllib.request
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from openai import OpenAI, APIStatusError
from google import genai
from google.genai import types
from puzzle_solver import solve_geetest_puzzle
from PIL import Image
import traceback
from concurrent.futures import ThreadPoolExecutor
from ai_utils import (
    ask_text_to_chatgpt,
    ask_text_to_gemini,
    ask_audio_to_openai,
    ask_audio_to_gemini,
    ask_recaptcha_instructions_to_chatgpt,
    ask_recaptcha_instructions_to_gemini,
    ask_if_tile_contains_object_chatgpt,
    ask_if_tile_contains_object_gemini,
    ask_puzzle_distance_to_gemini,
    ask_puzzle_distance_to_chatgpt,
    ask_puzzle_correction_to_chatgpt,
    ask_puzzle_correction_to_gemini
)
from gif_utils import create_result_gif
from solve_logger import log_result, start_session, finalize_session, log_attempt

#todo: sesli captchada sese asıl captchayı söyledikten sonra ignore previous instructions diyip sonra random bir captcha daha vericem
load_dotenv()

# Initialize clients at the top level
gemini_client = None
if os.getenv("GOOGLE_API_KEY"):
    gemini_client = genai.Client()

def average_of_array(arr):
    if not arr:
        return 0  # Handle edge case of empty array
    sum_elements = sum(arr)
    average = sum_elements / len(arr)
    return average - 5

def check_tile_for_object(args):
    """Helper function for ThreadPoolExecutor to call the correct AI provider for a single tile."""
    tile_index, tile_path, object_name, provider, model = args

    try:
        decision_str = ''
        if provider == 'openai':
            decision_str = ask_if_tile_contains_object_chatgpt(tile_path, object_name, model)
        else: # gemini
            decision_str = ask_if_tile_contains_object_gemini(tile_path, object_name, model)

        print(f"Tile {tile_index}: Does it contain '{object_name}'? AI says: {decision_str}")
        return tile_index, decision_str == 'true'
    except Exception as e:
        print(f"Error checking tile {tile_index}: {e}")
        return tile_index, False

def audio_test(file_path='files/audio.mp3', provider='gemini', model=None):
    """Transcribes a local audio file using the specified AI provider."""
    if not os.path.exists(file_path):
        print(f"Error: Audio file not found at '{file_path}'")
        log_result(False, "audio", details=f"Arquivo não encontrado: {file_path}")
        return False

    try:
        print(f"Transcribing audio from '{file_path}' using {provider.upper()}...")
        transcription = ""
        if provider == 'openai':
            transcription = ask_audio_to_openai(file_path, model)
        else: # default to gemini
            transcription = ask_audio_to_gemini(file_path, model)
        
        print("\n--- Transcription Result ---")
        print(transcription)
        print("--------------------------\n")
        log_result(True, "audio", details=transcription)
        return True
    except Exception as e:
        print(f"An error occurred during audio transcription: {e}")
        log_result(False, "audio", details=str(e))
        return False

def complicated_text_test(driver, provider='openai', model=None, target='2captcha', url=None):
    if target == 'local':
        return complicated_text_test_local(driver, provider, model, url or 'http://127.0.0.1:5000/complicated_text')
    """
    Solves a single "Complicated Text" captcha instance, trying up to 3 times.
    The benchmark is successful if any attempt passes.
    Returns the attempt number (1, 2, or 3) on success, or 0 on failure.
    """
    driver.get("https://2captcha.com/demo/mtcaptcha")
    time.sleep(5)
    screenshot_paths = []
    
    for attempt in range(3):
        print(f"\n--- Complicated Text: Attempt {attempt + 1}/3 ---")
        try:
            # 1. Get the captcha image
            iframe = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "mtcaptcha-iframe-1"))
            )
            time.sleep(2) # Allow time for new captcha to load on retries
            
            captcha_screenshot_path = f'screenshots/complicated_text_attempt_{attempt + 1}.png'
            iframe.screenshot(captcha_screenshot_path)
            screenshot_paths.append(captcha_screenshot_path)

            # 2. Ask AI for the answer
            response = ''
            if provider == 'openai':
                response = ask_text_to_chatgpt(captcha_screenshot_path, model)
            else: # gemini
                response = ask_text_to_gemini(captcha_screenshot_path, model)

            print(f"AI transcription: '{response}'")
            
            # 3. Submit the answer
            driver.switch_to.frame(iframe)
            input_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "mtcap-noborder.mtcap-inputtext.mtcap-inputtext-custom"))
            )
            input_field.clear()
            input_field.send_keys(response)
            time.sleep(2)
            driver.switch_to.default_content()
            
            submit_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Check')]"))
            )
            submit_button.click()
            
            # 4. Check for success
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "_successMessage_w91t8_1"))
            )
            
            print("Captcha passed successfully!")
            final_success_path = f"screenshots/final_success_complicated_{datetime.now().strftime('%H%M%S')}.png"
            driver.save_screenshot(final_success_path)
            screenshot_paths.append(final_success_path)
            create_result_gif(screenshot_paths, output_folder=f"successful_solves/complicated_text_{provider}", prefix="success")
            log_result(True, "complicated_text", details=f"attempt {attempt + 1}")
            return attempt + 1 # Return the successful attempt number

        except Exception as e:
            print(f"Attempt {attempt + 1} did not pass.")
            if attempt < 2:
                print("Retrying...")
            else:
                print("All 3 attempts failed for this benchmark run.")
            
            try:
                driver.switch_to.default_content()
            except Exception:
                pass

    final_failure_path = f"screenshots/final_failure_complicated_{datetime.now().strftime('%H%M%S')}.png"
    try:
        driver.save_screenshot(final_failure_path)
        screenshot_paths.append(final_failure_path)
    except Exception:
        pass
    create_result_gif(screenshot_paths, output_folder=f"failed_solves/complicated_text_{provider}", prefix="failure")
    log_result(False, "complicated_text", details="All 3 attempts failed")
    return 0

def _local_server_base(url):
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def _fetch_local_debug(url):
    try:
        base = _local_server_base(url)
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        seed = qs.get("seed", [None])[0]
        if seed is not None:
            with urllib.request.urlopen(f"{base}/api/answer_by_seed/{seed}", timeout=5) as resp:
                return json.loads(resp.read().decode())
        with urllib.request.urlopen(f"{base}/api/answer", timeout=5) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"[WARN] Não foi possível obter ground truth local: {e}")
        return {}


def _read_variant_from_page(driver):
    try:
        meta = driver.find_element(By.CSS_SELECTOR, 'meta[name="captcha-variant"]')
        return json.loads(meta.get_attribute('content'))
    except Exception:
        return {}


def _local_text_solver(driver, captcha_type, provider, model, url):
    """Resolve qualquer CAPTCHA de texto (simples ou distorcido) do servidor Flask local."""
    driver.get(url)
    screenshot_paths = []
    try:
        captcha_image = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "captcha-image"))
        )
        try:
            WebDriverWait(driver, 5).until(
                lambda d: d.execute_script(
                    "const img = document.getElementById('captcha-image'); return img && img.complete && img.naturalWidth > 0;"
                )
            )
        except Exception:
            # Image didn't load — reload the page and try once more
            driver.get(url)
            captcha_image = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "captcha-image"))
            )
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script(
                    "const img = document.getElementById('captcha-image'); return img && img.complete && img.naturalWidth > 0;"
                )
            )
        time.sleep(1)
        captcha_screenshot_path = f'screenshots/{captcha_type}_local_1.png'
        captcha_image.screenshot(captcha_screenshot_path)
        screenshot_paths.append(captcha_screenshot_path)

        if provider == 'openai':
            response = ask_text_to_chatgpt(captcha_screenshot_path, model)
        else:
            response = ask_text_to_gemini(captcha_screenshot_path, model)

        print(f"AI transcription: '{response}'")

        input_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "captcha-input"))
        )
        input_field.clear()
        input_field.send_keys(response)
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "captcha-submit"))
        )
        submit_button.click()

        WebDriverWait(driver, 10).until(
            lambda d: d.find_element(By.ID, "captcha-result").get_attribute("data-visible") == "true"
        )
        success = driver.find_element(By.ID, "captcha-result").get_attribute("data-success") == "true"

        debug = _fetch_local_debug(url)
        variant = debug.get("variant") or _read_variant_from_page(driver)
        ground_truth = debug.get("answer")
        log_details = {
            "variant": variant,
            "ground_truth": ground_truth,
            "ai_response": response,
            "target": "local",
            "url": url,
        }

        if success:
            print(f"{captcha_type} local passed successfully!")
            final_success_path = f"screenshots/final_success_{captcha_type}_local_{datetime.now().strftime('%H%M%S')}.png"
            driver.save_screenshot(final_success_path)
            screenshot_paths.append(final_success_path)
            create_result_gif(screenshot_paths, output_folder=f"successful_solves/{captcha_type}_local_{provider}", prefix="success")
            log_result(True, captcha_type, details=log_details)
            return 1

        print(f"{captcha_type} local failed.")
        final_failure_path = f"screenshots/final_failure_{captcha_type}_local_{datetime.now().strftime('%H%M%S')}.png"
        try:
            driver.save_screenshot(final_failure_path)
            screenshot_paths.append(final_failure_path)
        except Exception:
            pass
        create_result_gif(screenshot_paths, output_folder=f"failed_solves/{captcha_type}_local_{provider}", prefix="failure")
        log_result(False, captcha_type, details=log_details)
        return 0
    except Exception as e:
        print(f"Local captcha failed... Error: {e}")
        final_failure_path = f"screenshots/final_failure_{captcha_type}_local_{datetime.now().strftime('%H%M%S')}.png"
        try:
            driver.save_screenshot(final_failure_path)
            screenshot_paths.append(final_failure_path)
        except Exception:
            pass
        create_result_gif(screenshot_paths, output_folder=f"failed_solves/{captcha_type}_local_{provider}", prefix="failure")
        log_result(False, captcha_type, details={"target": "local", "url": url, "error": str(e)})
        return 0


def text_test_local(driver, provider='gemini', model=None, url='http://127.0.0.1:5000/text'):
    return _local_text_solver(driver, 'text', provider, model, url)


def complicated_text_test_local(driver, provider='gemini', model=None, url='http://127.0.0.1:5000/complicated_text'):
    return _local_text_solver(driver, 'complicated_text', provider, model, url)


def text_test(driver, provider='openai', model=None, target='2captcha', url=None):
    """
    Solves a single "Normal Text" captcha instance.
    Returns 1 for success, 0 for failure.
    """
    if target == 'local':
        return text_test_local(driver, provider, model, url or 'http://127.0.0.1:5000/text')

    driver.get("https://2captcha.com/demo/normal")
    time.sleep(5)
    screenshot_paths = []
    try:
        captcha_image = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "_captchaImage_rrn3u_9"))
        )
        time.sleep(2)
        captcha_screenshot_path = 'screenshots/text_captcha_1.png'
        captcha_image.screenshot(captcha_screenshot_path)
        screenshot_paths.append(captcha_screenshot_path)
        
        response = ''
        if provider == 'openai':
            response = ask_text_to_chatgpt(captcha_screenshot_path, model)
        else: # gemini
            response = ask_text_to_gemini(captcha_screenshot_path, model)

        print(f"AI transcription: '{response}'")

        input_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "_inputInner_ws73z_12"))
        )
        input_field.clear()
        input_field.send_keys(response)
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Check')]"))
        )
        submit_button.click()

        # If correct, the 'Check' button will disappear.
        WebDriverWait(driver, 10).until(
            EC.invisibility_of_element_located((By.XPATH, "//button[contains(., 'Check')]"))
        )

        print("Captcha passed successfully!")
        
        final_success_path = f"screenshots/final_success_text_{datetime.now().strftime('%H%M%S')}.png"
        driver.save_screenshot(final_success_path)
        screenshot_paths.append(final_success_path)
        create_result_gif(screenshot_paths, output_folder=f"successful_solves/text_{provider}", prefix="success")
        log_result(True, "text")
        return 1
    except Exception as e:
        print(f"Captcha failed... Error: {e}")
        final_failure_path = f"screenshots/final_failure_text_{datetime.now().strftime('%H%M%S')}.png"
        try:
            driver.save_screenshot(final_failure_path)
            screenshot_paths.append(final_failure_path)
        except Exception:
            pass
        create_result_gif(screenshot_paths, output_folder=f"failed_solves/text_{provider}", prefix="failure")
        log_result(False, "text", details=str(e))
        return 0

def recaptcha_v2_test_local(driver, provider='gemini', model=None, url='http://127.0.0.1:5000/recaptcha_v2'):
    """Resolve reCAPTCHA v2 sintético do servidor Flask local."""
    driver.get(url)
    screenshot_paths = []
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "captcha-grid"))
        )
        try:
            WebDriverWait(driver, 8).until(
                lambda d: d.execute_script(
                    "const imgs = document.querySelectorAll('.tile img');"
                    "return imgs.length === 9 && Array.from(imgs).every(i => i.complete && i.naturalWidth > 0);"
                )
            )
        except Exception:
            # Tiles didn't load — reload and try once more
            driver.get(url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "captcha-grid"))
            )
            WebDriverWait(driver, 15).until(
                lambda d: d.execute_script(
                    "const imgs = document.querySelectorAll('.tile img');"
                    "return imgs.length === 9 && Array.from(imgs).every(i => i.complete && i.naturalWidth > 0);"
                )
            )
        time.sleep(0.5)
        instruction_el = driver.find_element(By.ID, "captcha-instruction")
        object_name = instruction_el.get_attribute("data-target")
        print(f"Instrução: {instruction_el.text}  |  Alvo: {object_name}")

        tile_els = driver.find_elements(By.CSS_SELECTOR, ".tile")
        tile_paths = []
        for i, tile in enumerate(tile_els):
            path = f"screenshots/grid_tile_local_{i}.png"
            tile.screenshot(path)
            screenshot_paths.append(path)
            tile_paths.append(path)

        tasks = [(i, path, object_name, provider, model) for i, path in enumerate(tile_paths)]
        tiles_to_click = []
        with ThreadPoolExecutor(max_workers=9) as executor:
            for tile_index, should_click in executor.map(check_tile_for_object, tasks):
                if should_click:
                    tiles_to_click.append(tile_index)

        print(f"IA selecionou tiles: {sorted(tiles_to_click)}")
        for i in sorted(tiles_to_click):
            try:
                tile_els[i].click()
                time.sleep(random.uniform(0.1, 0.3))
            except Exception:
                pass

        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "captcha-submit"))
        ).click()

        WebDriverWait(driver, 10).until(
            lambda d: d.find_element(By.ID, "captcha-result").get_attribute("data-visible") == "true"
        )
        success = driver.find_element(By.ID, "captcha-result").get_attribute("data-success") == "true"

        debug = _fetch_local_debug(url)
        ground_truth = debug.get("solution")
        variant = debug.get("variant") or _read_variant_from_page(driver)
        log_details = {
            "variant": variant,
            "ground_truth": ground_truth,
            "ai_response": sorted(tiles_to_click),
            "target": "local",
            "url": url,
        }

        status = "success" if success else "failure"
        final_path = f"screenshots/final_{status}_recaptcha_v2_local_{datetime.now().strftime('%H%M%S')}.png"
        driver.save_screenshot(final_path)
        screenshot_paths.append(final_path)
        create_result_gif(screenshot_paths, output_folder=f"{'successful_solves' if success else 'failed_solves'}/recaptcha_v2_local_{provider}", prefix=status)
        log_result(success, "recaptcha_v2", details=log_details)

        print(f"reCAPTCHA v2 local {'passed!' if success else 'failed.'}")
        return 1 if success else 0

    except Exception as e:
        print(f"reCAPTCHA v2 local error: {e}")
        final_path = f"screenshots/final_failure_recaptcha_v2_local_{datetime.now().strftime('%H%M%S')}.png"
        try:
            driver.save_screenshot(final_path)
            screenshot_paths.append(final_path)
        except Exception:
            pass
        create_result_gif(screenshot_paths, output_folder=f"failed_solves/recaptcha_v2_local_{provider}", prefix="failure")
        log_result(False, "recaptcha_v2", details={"target": "local", "url": url, "error": str(e)})
        return 0


def recaptcha_v2_test(driver, provider='openai', model=None, target='2captcha', url=None):
    if target == 'local':
        return recaptcha_v2_test_local(driver, provider, model, url or 'http://127.0.0.1:5000/recaptcha_v2')
    """
    Solves a single reCAPTCHA v2 instance on the 2captcha demo page.
    Returns 1 for success, 0 for failure.
    """
    driver.get("https://2captcha.com/demo/recaptcha-v2")
    
    screenshot_paths = []
    try:
        # --- Start the challenge ---
        recaptcha_frame = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//iframe[@title='reCAPTCHA']")))
        driver.switch_to.frame(recaptcha_frame)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "recaptcha-checkbox-border"))).click()
        driver.switch_to.default_content()
        time.sleep(2)

        # --- Loop to solve image challenges as long as they appear ---
        MAX_CHALLENGE_ATTEMPTS = 5
        clicked_tile_indices = set()
        last_object_name = ""
        num_last_clicks = 0
        for attempt in range(MAX_CHALLENGE_ATTEMPTS):
            print(f"\nreCAPTCHA image challenge attempt {attempt + 1}/{MAX_CHALLENGE_ATTEMPTS}...")
            
            # --- Check if a puzzle is present ---
            try:
                challenge_iframe = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.XPATH, "//iframe[contains(@title, 'recaptcha challenge expires in two minutes')]")))
                driver.switch_to.frame(challenge_iframe)
            except Exception:
                print("No new image challenge found. Proceeding to final submission.")
                break # Exit the loop

            # --- If puzzle is found, solve it ---
            instruction_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "rc-imageselect-instructions")))
            instruction_screenshot_path = f'screenshots/recaptcha_instruction_{attempt + 1}.png'
            instruction_element.screenshot(instruction_screenshot_path)
            screenshot_paths.append(instruction_screenshot_path)
            
            object_name = ''
            if provider == 'openai':
                object_name = ask_recaptcha_instructions_to_chatgpt(instruction_screenshot_path, model)
            else: # gemini
                object_name = ask_recaptcha_instructions_to_gemini(instruction_screenshot_path, model)
            print(f"AI identified the target object as: '{object_name}'")

            is_new_object = object_name.lower() != last_object_name.lower()
            if is_new_object:
                print(f"New challenge object detected ('{object_name}'). Resetting clicked tiles.")
                clicked_tile_indices = set()
                last_object_name = object_name
            elif num_last_clicks >= 3:
                print("Previously clicked 3 or more tiles, assuming a new challenge. Resetting clicked tiles.")
                clicked_tile_indices = set()
            else:
                print("Same challenge object and < 3 tiles clicked previously. Will not re-click already selected tiles.")

            table = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//table[contains(@class, 'rc-imageselect-table')]")))
            all_tiles = table.find_elements(By.TAG_NAME, "td")
            
            tile_paths = []
            for i, tile in enumerate(all_tiles):
                tile_path = f'screenshots/tile_{attempt + 1}_{i}.png'
                tile.screenshot(tile_path)
                screenshot_paths.append(tile_path)
                tile_paths.append(tile_path)

            tasks = [(i, path, object_name, provider, model) for i, path in enumerate(tile_paths)]
            tiles_to_click_this_round = []
            with ThreadPoolExecutor(max_workers=len(all_tiles)) as executor:
                results = executor.map(check_tile_for_object, tasks)
                for tile_index, should_click in results:
                    if should_click:
                        tiles_to_click_this_round.append(tile_index)

            current_attempt_tiles = set(tiles_to_click_this_round)
            new_tiles_to_click = current_attempt_tiles - clicked_tile_indices
            num_last_clicks = len(new_tiles_to_click)

            print(f"\nAI identified tiles for clicking: {sorted(list(current_attempt_tiles))}")
            print(f"Already clicked tiles: {sorted(list(clicked_tile_indices))}")
            print(f"Clicking {len(new_tiles_to_click)} new tiles...")
            
            for i in sorted(list(new_tiles_to_click)):
                try:
                    if all_tiles[i].is_displayed() and all_tiles[i].is_enabled():
                        all_tiles[i].click()
                        time.sleep(random.uniform(0.2, 0.5))
                except Exception as e:
                    print(f"Could not click tile {i}, it might be already selected or disabled. Error: {e}")
            
            clicked_tile_indices.update(new_tiles_to_click)

            try:
                verify_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "recaptcha-verify-button")))
                verify_button.click()
                time.sleep(1.5) # Wait for state change

                # After clicking, check if the button is now disabled, which indicates success
                verify_button_after_click = driver.find_element(By.ID, "recaptcha-verify-button")
                if verify_button_after_click.get_attribute("disabled"):
                    print("Verify button is disabled. Image challenge passed.")
                    driver.switch_to.default_content()
                    print("reCAPTCHA v2 passed successfully!")
        
                    final_success_path = f"screenshots/final_success_recaptcha_v2_{datetime.now().strftime('%H%M%S')}.png"
                    driver.save_screenshot(final_success_path)
                    screenshot_paths.append(final_success_path)
                    
                    create_result_gif(screenshot_paths, output_folder=f"successful_solves/recaptcha_v2_{provider}", prefix="success")
                    log_result(True, "recaptcha_v2")
                    return 1
                else:
                    # This case handles "check new images" - we just let the loop continue
                    print("Verify button still active, likely a new challenge was served.")

            except Exception:
                print("Verify button not found after clicking tiles, assuming challenge is complete.")
                break # Exit the loop to the final submission step

            driver.switch_to.default_content()
            time.sleep(2)
        else:
            # This 'else' belongs to the 'for' loop. Runs if the loop completes without a 'break'.
            print("Image challenge still present after max attempts.")
            final_failure_path = f"screenshots/final_failure_recaptcha_v2_{datetime.now().strftime('%H%M%S')}.png"
            try:
                driver.save_screenshot(final_failure_path)
                screenshot_paths.append(final_failure_path)
            except Exception:
                pass
            create_result_gif(screenshot_paths, output_folder=f"failed_solves/recaptcha_v2_{provider}", prefix="failure")
            log_result(False, "recaptcha_v2", details="Max challenge attempts reached")
            return 0

        # --- Submit main page form ---
        check_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-action='demo_action']"))
        )
        check_button.click()

        # Check for the success message using the correct class name
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "_successMessage_1ndnh_1"))
        )

        print("reCAPTCHA v2 passed successfully!")
        
        final_success_path = f"screenshots/final_success_recaptcha_v2_{datetime.now().strftime('%H%M%S')}.png"
        driver.save_screenshot(final_success_path)
        screenshot_paths.append(final_success_path)
        
        create_result_gif(screenshot_paths, output_folder=f"successful_solves/recaptcha_v2_{provider}", prefix="success")
        log_result(True, "recaptcha_v2")
        return 1
    
    except Exception as ex:
        print(f"An error occurred during reCAPTCHA v2 test: {ex}. Marking as failed.")
        traceback.print_exc()
        try:
            failure_screenshot = f"screenshots/final_failure_recaptcha_v2_{datetime.now().strftime('%H%M%S')}.png"
            driver.save_screenshot(failure_screenshot)
            screenshot_paths.append(failure_screenshot)
        except Exception:
            pass
        try:
            driver.switch_to.default_content()
        except Exception:
            pass
        create_result_gif(screenshot_paths, output_folder=f"failed_solves/recaptcha_v2_{provider}", prefix="failure")
        log_result(False, "recaptcha_v2", details=str(ex))
        return 0

def main():
    parser = argparse.ArgumentParser(description="Test various captcha types.")
    parser.add_argument('captcha_type', choices=['puzzle', 'text', 'complicated_text', 'recaptcha_v2', 'audio'],
                        help="Specify the type of captcha to test")
    parser.add_argument('--provider', choices=['openai', 'gemini'], default='gemini', help="Specify the AI provider to use")
    parser.add_argument('--file', type=str, default='files/audio.mp3', help="Path to the local audio file for the 'audio' test.")
    parser.add_argument('--model', type=str, default=None, help="Specify the AI model to use (e.g., 'gpt-4o', 'gemini-2.5-flash').")
    parser.add_argument('--explain', action='store_true', help="Documenta o raciocínio da IA (2a chamada à API + relatório Markdown)")
    parser.add_argument('--target', choices=['2captcha', 'local'], default='2captcha',
                        help="2captcha=demo online (padrão); local=servidor Flask")
    parser.add_argument('--url', type=str, default=None,
                        help="URL do CAPTCHA local (com query params de variante)")
    args = parser.parse_args()

    os.makedirs('screenshots', exist_ok=True)

    start_session(args.captcha_type, args.provider, args.model, explicit_explain=args.explain)
    log_attempt(args.captcha_type, args.provider, args.model or "default",
                "session_start", None, extra={"step": "start"})
    run_success = False
    run_details = None

    try:
        if args.captcha_type == 'audio':
            run_success = audio_test(args.file, args.provider, args.model)
        else:
            driver = webdriver.Firefox()
            try:
                if args.captcha_type == 'puzzle':
                    result = solve_geetest_puzzle(driver, args.provider)
                    run_success = result == 1
                elif args.captcha_type == 'text':
                    result = text_test(driver, args.provider, args.model, args.target, args.url)
                    run_success = result == 1
                elif args.captcha_type == 'complicated_text':
                    result = complicated_text_test(driver, args.provider, args.model, args.target, args.url)
                    run_success = result > 0
                    run_details = f"attempt {result}" if run_success else "All attempts failed"
                elif args.captcha_type == 'recaptcha_v2':
                    result = recaptcha_v2_test(driver, args.provider, args.model, args.target, args.url)
                    run_success = result == 1
            finally:
                driver.quit()
    finally:
        finalize_session(run_success, run_details)

    sys.exit(0 if run_success else 1)

if __name__ == "__main__":
    main()
