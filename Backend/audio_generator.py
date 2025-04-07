import requests

from dotenv import load_dotenv
import os
from pathlib import Path
import re
import time
from gtts import gTTS
from pydub import AudioSegment


# Load environment variables
load_dotenv()

# Get the API key for Hugging Face
HF_API_TOKEN = os.getenv('HF_API_TOKEN')

API_URL_SD = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"

# Headers with authentication
headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}

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
    
    # Loop through each scene and generate an image
    for scene in script_json.get("scenes", []):
        timestamp = scene.get("timestamp", "00:00")  # Default timestamp if missing
        start_time = extract_start_time(timestamp)  # Convert timestamp to seconds
        
        prompt = (
            f"A cinematic scene depicting {scene.get('scene_description', '')}. "
            f"The environment includes {scene.get('character_object_details', '')}. "
            f"The shot is taken using {scene.get('shot_type_camera_angle', '')} for dramatic effect. "
            f"The mood of the scene is {scene.get('mood_emotion', '')}. "
            f"Ultra-detailed, realistic, high-quality, professional lighting, dramatic composition."
        )

        output_path = f"{output_dir}/scene_{start_time}.png"  # Save with start_time in seconds
        
        # Prepare the request payload
        payload = {"inputs": prompt}

        try:
            response = requests.post(API_URL_SD, headers=headers, json=payload, timeout=60)  # Added timeout
            
            # Check if the response is successful
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                print(f"Image saved as {output_path}")
            else:
                print(f"Error generating image for scene {start_time}: {response.json()}")
        except requests.exceptions.RequestException as e:
            print(f"Request failed for scene {start_time}: {str(e)}")
    
    print("All images generated successfully.")

def generate_audio(script_json, output_dir, language='en', max_retries=3):
    """Generate audio from the voiceover text in the script JSON and save as mp3 files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    scenes = script_json.get("scenes", [])
    for i, scene in enumerate(scenes):
        timestamp = scene.get("timestamp", "00:00")  # Default timestamp if missing
        start_time = extract_start_time(timestamp)  # Convert timestamp to seconds
        voiceover_text = scene.get("voiceover", "").strip()
        output_path = os.path.join(output_dir, f"scene_{i+1}.mp3")

        if not voiceover_text:
            print(f"Skipping scene {i+1}: No voiceover text provided.")
            continue

        for attempt in range(max_retries):
            try:
                # Generate the TTS (Text-to-Speech) audio file
                tts = gTTS(voiceover_text, lang=language)
                tts.save(output_path)

                # Load the audio file and check its validity
                audio_clip = AudioSegment.from_file(output_path)
                print(f"Audio saved: {output_path} | Duration: {len(audio_clip) / 1000:.2f}s")

                break  # Exit retry loop on success
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Failed to generate audio for scene {i+1}. Retrying... ({attempt + 1}/{max_retries})")
                    time.sleep(5)  # Retry after waiting for 5 seconds
                else:
                    print(f"Failed after {max_retries} attempts: {e}")
                    raise

    print("All audio generation tasks completed.")