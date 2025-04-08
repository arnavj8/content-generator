import os
import subprocess
import requests
from moviepy.editor import AudioFileClip
from dotenv import load_dotenv
from pathlib import Path
import logging
from Backend.logger import logging
# Load environment variables
load_dotenv()

# Hugging Face API Token
HF_API_TOKEN = os.getenv('HF_API_TOKEN')
API_URL_MUSICGEN = "https://api-inference.huggingface.co/models/facebook/musicgen-small"
headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}

def generate_music_prompt(background_music_prompt, scenes, overall_video_mood):
    """Generate a music prompt based on scene moods and overall video theme."""
    intro_mood = scenes[0]["mood_emotion"]  # First scene's mood
    climax_mood = scenes[-1]["mood_emotion"]  # Last scene's mood
    transition_effects = {scene["suggested_transition_effect"] for scene in scenes}  # Unique transitions

    prompt = f"""
    Generate an {background_music_prompt} with {overall_video_mood}.
    Align the composition with the video's emotional shifts, scene transitions, and theme.

    - **Intro (0:00 - 0:10):** Music for a "{intro_mood}" atmosphere.
    - **Scene Progression (0:10 - {len(scenes) * 10}):** Evolving tone, adapting to: {', '.join([f'"{scene["mood_emotion"]}"' for scene in scenes])}.
    - **Climax ({(len(scenes) - 1) * 10} - {len(scenes) * 10}):** Emotionally intense with "{climax_mood}" orchestral elements.
    - **Transitions:** Smooth blending with effects like {', '.join(transition_effects)}.

    - **Instrumentation:** Cinematic orchestra with strings, brass, war drums, and choir vocals.
    - **Tempo Dynamics:** Adjust tempo based on emotional intensity.
    - **Mood Progression:** Start with "{intro_mood}" → evolve → conclude with "{climax_mood}".
    """
    return prompt

def generate_music(prompt, output_dir):
    """Generate background music using the Hugging Face API."""
    try:
        logging.info("Sending music generation request to the API...")
        payload = {"inputs": prompt}
        response = requests.post(API_URL_MUSICGEN, headers=headers, json=payload)
        response.raise_for_status()  # Raise HTTPError for bad responses

        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "background_music.mp3"

        with open(output_path, "wb") as f:
            f.write(response.content)
        logging.info(f"Music saved as {output_path}")

        # Convert to MP3 if needed
        converted_path = output_path.with_name(output_path.stem + "_converted.mp3")
        subprocess.run(['ffmpeg', '-i', str(output_path), '-acodec', 'libmp3lame', str(converted_path)], check=True)
        logging.info(f"Music converted to MP3 and saved as {converted_path}")

        # Replace the original file
        output_path.unlink()
        converted_path.rename(output_path)

        # Load audio clip (optional)
        music_clip = AudioFileClip(str(output_path))
        logging.info(f"Music duration: {music_clip.duration} seconds")
        music_clip.close()

    except requests.exceptions.RequestException as e:
        logging.error(f"HTTP error occurred: {e}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error during audio conversion: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

# Example usage (Uncomment for real use)
# current_path = Path(__file__).resolve()
# output_data_dir = current_path.parent / 'output' / 'video4'
# output_data_dir.mkdir(parents=True, exist_ok=True)
# music_output_dir = output_data_dir / 'output_music'
# 
# with open(output_data_dir / "video_script.json", "r", encoding="utf-8") as file:
#     script = json.load(file)
# 
# music_prompt = generate_music_prompt(script["background_music_prompt"], script["scenes"], script["overall_video_mood"])
# generate_music(music_prompt, music_output_dir)