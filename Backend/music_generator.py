import os
import subprocess
import requests
from moviepy.editor import AudioFileClip

from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

HF_API_TOKEN = os.getenv('HF_API_TOKEN')

API_URL_MUSICGEN = "https://api-inference.huggingface.co/models/facebook/musicgen-small"

headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}

def generate_music_prompt(background_music_prompt, scenes, overall_video_mood):
    """Dynamically generate a music prompt based on scene moods, pacing, and video theme."""
    
    intro_mood = scenes[0]["mood_emotion"]  # Extract mood of the first scene
    climax_mood = scenes[-1]["mood_emotion"]  # Extract mood of the final scene
    transition_effects = {scene["suggested_transition_effect"] for scene in scenes}  # Unique transitions used

    return f"""
    Generate an {background_music_prompt} with {overall_video_mood}.
    The composition should align with the video's emotional shifts, scene transitions, and overall theme.

    - **Intro (0:00 - 0:10):** Music that matches a "{intro_mood}" atmosphere, setting the stage for the video.
    - **Scene Progression (0:10 - {len(scenes) * 10}):** Gradual evolution in tone, adapting to scene-specific moods and transitions:
      {', '.join([f'"{scene["mood_emotion"]}"' for scene in scenes])}.
    - **Climax ({(len(scenes) - 1) * 10} - {len(scenes) * 10}):** Emotionally intense, reflecting "{climax_mood}" with appropriate orchestral elements.
    - **Transitions:** Ensure smooth blending between moods, considering transitions like {', '.join(transition_effects)}.
    
    - **Instrumentation:** Cinematic orchestra with adaptive use of strings, brass, war drums, and choir vocals.
    - **Tempo Dynamics:** Adjust tempo dynamically based on the emotional intensity of scenes.
    - **Mood Progression:** Start with "{intro_mood}" → evolve based on scene moods → conclude with "{climax_mood}".
    
    Ensure seamless transitions, a consistent thematic arc, and a dynamic one-shot generation approach.
    """

def generate_music(prompt, output_dir):
    """Generate background music based on user text input using Hugging Face API."""
    payload = {"inputs": prompt}
    response = requests.post(API_URL_MUSICGEN, headers=headers, json=payload)
    
    # os.makedirs(os.path.dirname(output_dir), exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "background_music.mp3"
    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"Music saved as {output_path}")
        
        # # Convert FLAC to MP3 using ffmpeg
        try:
            converted_path = f"{output_path}".replace('.mp3', '_converted.mp3')
            subprocess.run(['ffmpeg', '-i', output_path, '-acodec', 'libmp3lame', converted_path], check=True)
            print(f"Music converted to MP3 and saved as {converted_path}")
            
            # Remove the original FLAC file
            os.remove(output_path)
            
            # Rename the converted file to the original name
            os.rename(converted_path, output_path)
            
            # Load the audio clip for further processing (optional)
            # music_clip = AudioFileClip(output_path)
            music_clip = AudioFileClip(str(output_path))

            print(f"Music duration: {music_clip.duration} seconds")
            music_clip.close()
        except subprocess.CalledProcessError as e:
            print(f"Error during FLAC to MP3 conversion: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
    else:
        print(f"Error generating music: {response.json()}")


       
# import json
# current_path = Path(__file__).resolve()
# root_path = current_path.parent.parent
# output_data_dir = root_path / 'output/video4'
# output_data_dir.mkdir(parents=True, exist_ok=True)
# music_output_dir = output_data_dir / 'output_music'
# json_file = output_data_dir / "video_script.json"
# with json_file.open("r", encoding="utf-8") as file:
#     script = json.load(file)     
# music_prompt = generate_music_prompt(script["background_music_prompt"], script["scenes"], script["overall_video_mood"])
# generate_music(music_prompt, music_output_dir)