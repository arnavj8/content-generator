import requests
from dotenv import load_dotenv
import os
from pathlib import Path
import re
import time
from gtts import gTTS
from pydub import AudioSegment
import logging
from Backend.logger import logging
from Backend.db_utils import DatabaseManager,get_api_keys


try:
    keys = get_api_keys()
    
    # load_dotenv()   
    # Use the keys
    HF_API_TOKEN = os.getenv('HF_API_TOKEN')
    API_URL_SD = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
except Exception as e:
    logging.error(f"Failed to initialize API keys: {str(e)}")
    
    
# # Load environment variables

# # Get the API key for Hugging Face
# HF_API_TOKEN = os.getenv('HF_API_TOKEN')
# API_URL_SD = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
# headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}

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

    for scene in script_json.get("scenes", []):
        timestamp = scene.get("timestamp", "00:00")
        start_time = extract_start_time(timestamp)

        prompt = (
            f"A cinematic scene depicting {scene.get('scene_description', '')}. "
            f"The environment includes {scene.get('character_object_details', '')}. "
            f"The shot is taken using {scene.get('shot_type_camera_angle', '')} for dramatic effect. "
            f"The mood of the scene is {scene.get('mood_emotion', '')}. "
            f"Ultra-detailed, realistic, high-quality, professional lighting, dramatic composition."
        )

        output_path = f"{output_dir}/scene_{start_time}.png"
        payload = {"inputs": prompt}

        try:
            logging.info(f"Generating image for scene at {timestamp} with prompt: {prompt[:100]}...")
            response = requests.post(API_URL_SD, headers=headers, json=payload, timeout=60)

            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                logging.info(f"Image saved as {output_path}")
            else:
                error_message = response.json()
                logging.warning(f"Error generating image for scene {start_time}: {error_message}")

        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed for scene {start_time}: {str(e)}")

    logging.info("All images generated successfully.")

def generate_british_female_voice(text, output_path, max_retries=3):
    """Generate British female professional voice audio."""
    for attempt in range(max_retries):
        try:
            tts = gTTS(text=text, lang='en', tld='co.uk', slow=False)
            tts.save(output_path)
            audio_clip = AudioSegment.from_file(output_path)
            
            # Adjust audio properties for more professional sound
            audio_clip = audio_clip + 2  # Slightly increase volume
            audio_clip.export(output_path, format="mp3")
            
            return audio_clip
            
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(5)
            else:
                raise e

def generate_audio(script_json, output_dir, max_retries=3):
    """Generate audio from the voiceover text in the script JSON using British female professional voice."""
    output_dir.mkdir(parents=True, exist_ok=True)
    logging.info(f"Output directory for audio created at {output_dir}")

    scenes = script_json.get("scenes", [])
    for i, scene in enumerate(scenes):
        timestamp = scene.get("timestamp", "00:00")
        start_time = extract_start_time(timestamp)
        voiceover_text = scene.get("voiceover", "").strip()
        output_path = os.path.join(output_dir, f"scene_{i+1}.mp3")

        if not voiceover_text:
            logging.warning(f"Skipping scene {i+1}: No voiceover text provided.")
            continue

        try:
            logging.info(f"Generating British female professional voice for scene {i+1}")
            
            # Process the voiceover text for better speech
            processed_text = voiceover_text.replace('-', ' ').replace('_', ' ')
            
            # Generate the British female voice
            audio_clip = generate_british_female_voice(
                processed_text, 
                output_path, 
                max_retries
            )
            
            logging.info(f"Audio saved: {output_path} | Duration: {len(audio_clip) / 1000:.2f}s")

        except Exception as e:
            logging.error(f"Failed to generate audio for scene {i+1}: {e}")
            raise

    logging.info("All audio generation tasks completed.")

def process_script_with_voice_options(script_json, output_dir):
    """Process script with additional voice options and configurations."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Voice configuration options
    voice_configs = {
        'professional': {
            'slow': False,
            'tld': 'co.uk',
        },
        'formal': {
            'slow': True,
            'tld': 'co.uk',
        },
        'standard': {
            'slow': False,
            'tld': 'com',
        }
    }
    
