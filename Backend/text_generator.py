import google.generativeai as genai
from dotenv import load_dotenv
import os
import re
import json

load_dotenv()

# Get the API key for Google Generative AI
GEN_API_KEY = os.getenv('GEN_API_KEY')

if not GEN_API_KEY:
    print("GEN_API_KEY not found in environment variables.")
else:
    print("GEN_API_KEY loaded successfully.")

try:
    print("Configuring the generative AI API...")
    genai.configure(api_key=GEN_API_KEY)
    print("Generative AI API configured successfully.")
except Exception as e:
    print(f"Error while configuring Generative AI API: {e}")
    raise

def generate_video_script(topic,style):
    print(f"Generating video script for topic: {topic}")
    
    prompt = f"""
    You are a professional AI video script generator. Given a video topic and style, generate a detailed script and structured breakdown for an AI-generated video.

    ## Instructions:
    1. **Generate a structured script** with clear narration for voiceover.
    2. **Break the script into multiple scenes** (each 10 seconds long).
    3. For each scene, provide:
       - **Timestamp:** (Start - End)
       - **Voiceover:** (The spoken dialogue for this scene)
       - **Scene Description:** (What should be visually shown in this scene)
       - **Character & Object Details:** (To ensure consistency in generated images)
       - **Shot Type & Camera Angle:** (e.g., Wide shot, Close-up, Aerial view)
       - **Mood & Emotion:** (To determine music and voiceover tone)
       - **Suggested Transition Effect:** (Fade-in, Crossfade, Zoom, etc.)
    4. **Provide a final summary of the entire video mood** (e.g., inspirational, dramatic, educational).
    5. **Generate a background music prompt** based on the overall video theme and mood.
    6. **Ensure clarity, consistency, and coherence** in the storytelling.

    ## Example Input:
    **Topic:** "{topic}"

    ## Expected Output:
    JSON format with:
    {{
      "video_title": "{topic}",
      "scenes": [
        {{
          "timestamp": "00:00 - 00:10",
          "voiceover": "Example narration for first scene.",
          "scene_description": "Description of the first scene.",
          "character_object_details": "Characters, objects, and their details.",
          "shot_type_camera_angle": "Wide shot, aerial view, etc.",
          "mood_emotion": "Mood setting for this scene.",
          "suggested_transition_effect": "Transition effect (Fade-in, Zoom, etc.)"
        }},
        ...
      ],
      "overall_video_mood": "Final video mood description.",
      "background_music_prompt": "A cinematic orchestral soundtrack with a dramatic build-up, matching the video's emotional tone."
    }}
    """
    
    try:
        print("Sending prompt to the generative AI model...")
        model = genai.GenerativeModel("gemini-1.5-pro")  
        response = model.generate_content(prompt)
        print("Successfully received response from the AI model.")
        return response.text
    except Exception as e:
        print(f"Error during video script generation: {e}")
        return None


def extract_json(text):
    """Extract valid JSON from model output."""
    try:
        # Find JSON between triple backticks (```)
        matches = re.findall(r"```json\s*(\{.*?\})\s*```|```\s*(\{.*?\})\s*```", text, re.DOTALL)
        if matches:
            json_str = matches[0][0] if matches[0][0] else matches[0][1]  
            return json.loads(json_str)  # Convert to Python dictionary
        else:
            print("No valid JSON found between triple backticks.")
            return {"error": "No valid JSON found between triple backticks"}
    except json.JSONDecodeError as e:
        print(f"Invalid JSON format: {e}")
        return {"error": f"Invalid JSON format: {e}"}


def save_json(video_data, output_dir):
    """Save the video data to a JSON file in the given directory."""
    try:
        json_file_path = os.path.join(output_dir, "video_script.json")
        
        with open(json_file_path, "w", encoding="utf-8") as file:
            json.dump(video_data, file, indent=4, ensure_ascii=False)
        
        print(f"Video script saved to {json_file_path}")
    except Exception as e:
        print(f"Error saving video script to file: {e}")
