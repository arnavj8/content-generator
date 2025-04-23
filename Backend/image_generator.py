import requests
from dotenv import load_dotenv
import os
from pathlib import Path
import re
import logging
import time
import random
from Backend.logger import logging
from Backend.db_utils import ensure_api_keys

try:
    # Ensure API keys are available
    ensure_api_keys()
    
    # Use the keys
    HF_API_TOKEN = os.getenv('HF_API_TOKEN')

    API_URL_SD = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    
except Exception as e:
    logging.error(f"Error: {str(e)}")

def extract_start_time(timestamp):
    """Extracts the start time in seconds from a timestamp string (e.g., '00:10 - 00:20')."""
    match = re.match(r"(\d{2}):(\d{2})", timestamp)
    if match:
        minutes, seconds = map(int, match.groups())
        return minutes * 60 + seconds
    return 0  # Default to 0 if parsing fails

def generate_images_from_script(script_json, output_dir):
    """Generate images for each scene based on the script JSON using Hugging Face API."""
    output_dir.mkdir(parents=True, exist_ok=True)
    logging.info(f"Output directory created at {output_dir}")
    
    MAX_RETRIES = 3
    initial_timeout = 60
    
    for i, scene in enumerate(script_json.get("scenes", [])):
        timestamp = scene.get("timestamp", "00:00") 
        start_time = extract_start_time(timestamp)
        
        prompt = (
            f"A cinematic scene depicting {scene.get('scene_description', '')}. "
            f"The environment includes {scene.get('character_object_details', '')}. "
            f"The shot is taken using {scene.get('shot_type_camera_angle', '')} for dramatic effect. "
            f"The mood of the scene is {scene.get('mood_emotion', '')}. "
            f"Ultra-detailed, realistic, high-quality, professional lighting, dramatic composition."
        )

        output_path = f"{output_dir}/scene_{i+1}.png"
        payload = {"inputs": prompt}

        # Implement retry logic with exponential backoff
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logging.info(f"Generating image for scene {i+1} (Attempt {attempt}/{MAX_RETRIES}) with prompt: {prompt[:100]}...")
                
                # Calculate timeout with exponential backoff
                timeout = initial_timeout * (2 ** (attempt - 1))
                
                response = requests.post(API_URL_SD, headers=headers, json=payload, timeout=timeout)

                if response.status_code == 200:
                    with open(output_path, "wb") as f:
                        f.write(response.content)
                    logging.info(f"Image saved as {output_path}")
                    break  # Success, exit retry loop
                elif response.status_code == 429:  # Too Many Requests
                    # Wait longer between retries if rate limited
                    wait_time = 10 * attempt + random.uniform(1, 5)
                    logging.warning(f"Rate limit hit for scene {i+1}. Waiting {wait_time:.2f} seconds before retry...")
                    time.sleep(wait_time)
                else:
                    error_message = response.json() if response.content else f"HTTP {response.status_code}"
                    logging.warning(f"Error generating image for scene {i+1}: {error_message}")
                    if attempt < MAX_RETRIES:
                        wait_time = 5 * attempt
                        logging.info(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)

            except requests.exceptions.Timeout:
                logging.warning(f"Timeout occurred for scene {i+1} (Attempt {attempt}/{MAX_RETRIES})")
                if attempt < MAX_RETRIES:
                    wait_time = 5 * attempt
                    logging.info(f"Retrying with longer timeout in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logging.error(f"All retry attempts failed for scene {i+1} due to timeout")
            
            except requests.exceptions.RequestException as e:
                logging.error(f"Request failed for scene {i+1}: {str(e)}")
                if attempt < MAX_RETRIES:
                    wait_time = 5 * attempt
                    logging.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logging.error(f"All retry attempts failed for scene {i+1}")

    logging.info("Image generation process completed.")
    
    # Count successful generations
    generated_images = list(output_dir.glob("scene_*.png"))
    logging.info(f"Successfully generated {len(generated_images)} out of {len(script_json.get('scenes', []))} images.")