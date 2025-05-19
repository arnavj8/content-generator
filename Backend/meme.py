import os
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path
import logging
from Backend.logger import logging
from Backend.db_utils import ensure_api_keys

try:
    ensure_api_keys()

    # Set default keys as last resort

# Use the environment variables
    HF_API_TOKEN = os.getenv('HF_API_TOKEN')
    GEN_API_KEY = os.getenv('GEN_API_KEY')

    logging.info(f"API keys loaded - HF: {'Set' if HF_API_TOKEN else 'Not set'}, Gemini: {'Set' if GEN_API_KEY else 'Not set'}")

except Exception as e:
    logging.error(f"Error ensuring API keys: {str(e)}")
# load_dotenv()

# GEN_API_KEY = os.getenv("GEN_API_KEY")
# HF_API_TOKEN = os.getenv("HF_API_TOKEN")

def generate_meme_content(prompt, emotion, language="english"):
    """Generate meme caption, image prompt, font style, text color, and position using Gemini API."""
    logging.info("Configuring Gemini API with the provided key.")
    genai.configure(api_key=GEN_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash-latest")

    lang_instruction = "in English" if language.lower() == "english" else "in Hindi"

    logging.info("Generating meme content using Gemini API.")
    response = model.generate_content(
        f"Generate a short, funny meme caption under 10 words {lang_instruction} and an image description for: {prompt}. "
        f"The image should be meme-style, expressive, and based on the emotion {emotion}. "
        f"Also suggest a good meme-matching text color (red, green, yellow, white, etc.), and whether the text should be placed at 'top' or 'bottom'. "
        f"Format response as: 'Caption: <caption> | Image: <image description> | Color: <color> | Position: <top/bottom>'"
    )

    if response and "| Image:" in response.text:
        parts = response.text.split("|")
        caption = parts[0].replace("Caption:", "").strip()
        image_description = parts[1].replace("Image:", "").strip()
        text_color = parts[2].replace("Color:", "").strip()
        text_position = parts[3].replace("Position:", "").strip().lower()
        logging.info("Meme content generated successfully.")
    else:
        logging.warning("Meme content generation failed, using default values.")
        caption = "AI is too funny!" if language == "english" else "एआई बहुत मज़ेदार है!"
        image_description = f"A funny, exaggerated meme-style image about {prompt}. Cartoonish, expressive, meme-worthy."
        text_color = "white"
        text_position = "top"

    return caption, image_description, text_color, text_position, language

def generate_meme_image(image_prompt):
    """Generate a meme-style image from a given prompt using Hugging Face API."""
    logging.info("Sending image prompt to Hugging Face API.")
    payload = {"inputs": image_prompt}
    API_URL_SD = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    response = requests.post(API_URL_SD, headers=headers, json=payload, timeout=60)

    if response.status_code == 200:
        logging.info("Image generated successfully.")
        return Image.open(BytesIO(response.content))
    else:
        logging.error("Error generating image: " + response.text)
        raise Exception("Error generating image: " + response.text)

def add_meme_text(image, text, text_color, position, language):
    """Overlay meme text dynamically with font, color, and positioning."""
    logging.info("Adding text to the meme image.")
    draw = ImageDraw.Draw(image)
    font_paths = {
        "english": "static/arial.ttf",
        "hindi": "static/arial_hindi.ttf"
    }

    selected_font = font_paths["hindi"] if language.lower() == "hindi" else font_paths["english"]

    try:
        font_size = int(image.height * 0.07)
        font = ImageFont.truetype(selected_font, size=font_size)
    except:
        logging.warning("Failed to load custom font, using default font.")
        font = ImageFont.load_default()

    width, height = image.size
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (width - text_width) / 2
    y = 10 if position == "top" else height - text_height - 30

    for offset in [(-3, -3), (3, -3), (-3, 3), (3, 3)]:
        draw.text((x + offset[0], y + offset[1]), text, font=font, fill="black")

    draw.text((x, y), text, fill=text_color, font=font, stroke_width=3, stroke_fill="black")
    logging.info("Text added to the meme successfully.")
    return image
