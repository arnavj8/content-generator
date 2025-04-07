import os
import requests
from PIL import Image
from io import BytesIO
import base64
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# API keys
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
GEMINI_API_KEY = os.getenv("GEN_API_KEY")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

def generate_prompt_with_gemini(topic: str, style: str) -> str:
    """
    Use Gemini API to generate a rich, creative image prompt.
    """
    prompt_input = (
        f"Generate a highly descriptive, visually rich prompt for an AI image generation model "
        f"based on the topic '{topic}' in the '{style}' style. Avoid camera settings, but include artistic elements."
    )
    try:
        model = genai.GenerativeModel("gemini-1.5-pro")
        response = model.generate_content(prompt_input)
        prompt_text = response.text.strip()
        return prompt_text
    except Exception as e:
        raise RuntimeError(f"Gemini prompt generation failed: {e}")

def generate_image_from_topic_and_style(topic: str, style: str):
    """
    Generate image using Hugging Face Stable Diffusion based on Gemini-enhanced prompt.
    
    Returns:
        Tuple[str, str]: (description, base64 image string)
    """
    try:
        # Step 1: Generate enhanced prompt
        enhanced_prompt = generate_prompt_with_gemini(topic, style)

        # Step 2: Call Hugging Face API with enhanced prompt
        API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
        headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
        payload = {"inputs": enhanced_prompt}

        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()

        # Step 3: Process and encode the image
        image = Image.open(BytesIO(response.content))
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        description = f"Generated image for topic '{topic}' in '{style}' style using enhanced prompt."
        return description, image_base64

    except Exception as e:
        raise RuntimeError(f"Image generation failed: {e}")
