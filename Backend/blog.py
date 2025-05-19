import os
import re
import json
import arxiv
import requests
import markdown
import logging
from PIL import Image
from io import BytesIO
import wikipedia as wiki_wiki
import google.generativeai as genai
from pathlib import Path
from dotenv import load_dotenv
from Backend.logger import logging
from newsapi import NewsApiClient
import wikipedia.exceptions as wiki_exceptions
from Backend.db_utils import ensure_api_keys

try:
    # Ensure API keys are available
    ensure_api_keys()
    
    # Use the keys
    HF_API_TOKEN = os.getenv('HF_API_TOKEN')
    GEN_API_KEY = os.getenv('GEN_API_KEY')
    

    
except Exception as e:
    logging.error(f"Error: {str(e)}")
load_dotenv()
# GEN_API_KEY = os.getenv("GEN_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
# HF_API_TOKEN = os.getenv("HF_API_TOKEN")


def fetch_wikipedia(topic: str) -> str:
    """Fetches summary content from Wikipedia."""
    try:
        # Fetch page for the given topic
        page = wiki_wiki.page(topic)
        logging.info(f"Fetching Wikipedia page for topic: {topic}")
        # Return the page summary
        return page.summary if page.content else "No content found for this topic."
    except wiki_wiki.exceptions.DisambiguationError as e:
        # If there is a disambiguation error, inform the user
        logging.error(f"Disambiguation error for topic '{topic}': {e.options}")
        return f"Disambiguation error: The topic is ambiguous. Suggestions: {e.options}"
    except wiki_wiki.exceptions.HTTPTimeoutError as e:
        # Handles any timeout errors
        logging.error(f"HTTP timeout error while fetching topic '{topic}': {e}")
        return f"HTTP timeout error: {e}"
    except wiki_wiki.exceptions.RedirectError as e:
        # If the page is a redirect, handle it
        logging.error(f"Redirect error for topic '{topic}': {e.args[0]}")
        return f"Redirect error: The page redirects to {e.args[0]}"
    except wiki_wiki.exceptions.PageError as e:
        # If the page doesn't exist, handle it
        logging.error(f"Page error for topic '{topic}': {e}")
        return f"Page error: The page '{topic}' doesn't exist."
    except Exception as e:
        logging.error(f"Unexpected error while fetching Wikipedia content for '{topic}': {e}")
        return f"Error fetching Wikipedia content: {e}"


def fetch_arxiv(query):
    try:
        client = arxiv.Client()
        search = arxiv.Search(query=query, max_results=1, sort_by=arxiv.SortCriterion.SubmittedDate)
        results = [result.summary for result in client.results(search)]
        logging.info(f"Fetched Arxiv results for query: {query}")
        return results[0] if results else "No Arxiv content found."
    except Exception as e:
        logging.error(f"Error fetching Arxiv content for query '{query}': {str(e)}")
        return f"Arxiv fetch error: {str(e)}"


def duckduckgo_instant_answer(query: str):
    """Fetch relevant content from DuckDuckGo Instant Answer API based on the query."""
    try:
        # Construct the API URL
        url = f"https://api.duckduckgo.com/?q={query}&format=json"

        # Make the request
        response = requests.get(url)
        response.raise_for_status()

        # Parse the JSON response
        data = response.json()

        # Check if we have a relevant answer
        if 'AbstractText' in data and data['AbstractText']:
            logging.info(f"Fetched DuckDuckGo result for query: {query}")
            return data['AbstractText']  # Return abstract answer
        elif 'RelatedTopics' in data and len(data['RelatedTopics']) > 0:
            logging.info(f"Fetched related DuckDuckGo result for query: {query}")
            return data['RelatedTopics'][0]['Text']  # Return first related topic text
        else:
            logging.warning(f"No relevant content found for DuckDuckGo query: {query}")
            return "No relevant content found."
    except Exception as e:
        logging.error(f"Error fetching DuckDuckGo content for query '{query}': {e}")
        return f"Error fetching DuckDuckGo content: {e}"


def fetch_news_newsapi(query):
    try:
        newsapi = NewsApiClient(api_key=NEWS_API_KEY)
        articles = newsapi.get_everything(q=query, language='en', sort_by='publishedAt')
        logging.info(f"Fetched news articles for query: {query}")
        return articles['articles'][0]['description'] if articles['articles'] else "No news articles found."
    except Exception as e:
        logging.error(f"Error fetching NewsAPI content for query '{query}': {str(e)}")
        return f"News fetch error (NewsAPI): {str(e)}"

def generate_blog_with_gemini(context, topic, style, length):
    try:
        genai.configure(api_key=GEN_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        logging.info(f"Generating blog with Gemini for topic: {topic}, style: {style}, length: {length}")

        # Correct prompt formatting with JSON escaping
        json_structure = json.dumps({
             "title": "Blog Title",
             "tags": ["Keyword1", "Keyword2", "Keyword3", "Keyword4", "Keyword5"],
             "content": "Full blog content with proper formatting, headings, and paragraphs. "
                        "Include max 2 image links using the markdown format and name should be same as given below:\n\n"
                        "![Description](blogs/image1.png)\n\n"
                        "![Another relevant description](blogs/image2.png)\n\n"
                        "This ensures images are embedded within the blog. and these images will be below prompt only.",
             "image_prompts": [
                 "A detailed description of an image related to the blog topic.",
                 "Another descriptive prompt for an image relevant to the content.",
                 "A third image prompt that complements the blog visually."
             ]
         }, indent=2)  # Properly formatted JSON template
 
        prompt = f'''
         Write a well-structured, engaging, and professional blog on the topic: "{topic} with style{style} and length {length}".
         Use the provided context to ensure factual accuracy. If relevant context is missing, generate a factually correct and well-researched blog based on your knowledge.
         The blog must be **suitable for publishing** and provide **valuable insights** to the reader.
 
         ### **Requirements:**
         - Maintain a **natural, professional, and engaging tone**.
         - Structure the content with **clear headings, subheadings, and well-formatted paragraphs**.
         - Ensure the blog is **informative, easy to read, and logically structured**.
         - Avoid unnecessary repetition and ensure a smooth flow of ideas.
         - **Include relevant images within the content** using markdown format (`![Alt Text](image_url)`).
 
         ### **Provided Context:**
         {context}
 
         ### **Recheck Before Returning the Answer:**
         - Verify the **title** is relevant, engaging, and reflects the blog content.
         - Ensure the **tags** are diverse, relevant, and limited to exactly five.
         - Check that the **content is well-structured, logically organized, and free of factual errors.**
         - **Confirm all image prompts are properly linked inside the blog content** (using `![Alt Text](image_url)`).
         - Validate that the **JSON format is strictly followed** without extra text or explanations.
 
         ### **Output Format (JSON):**
         Return the blog in the exact following JSON format:
 
         ```json
         {json_structure}
         ```
         '''

        response = model.generate_content(prompt)
        if response and hasattr(response, "text"):
            logging.info(f"Blog generated successfully for topic: {topic}")
            return response.text
        else:
            logging.error(f"Empty response from Gemini model for topic: {topic}")
            return {"error": "Empty response from Gemini model"}
    except Exception as e:
        logging.error(f"Error generating blog for topic '{topic}': {str(e)}")
        return {"error": f"Blog generation error: {str(e)}"}

def generate_image_from_prompt(image_prompt, output_path):
    try:
        API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
        headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
        payload = {"inputs": image_prompt}
        logging.info(f"Generating image for prompt: {image_prompt}")

        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()

        image = Image.open(BytesIO(response.content))
        image.save(output_path)
        logging.info(f"Image saved to: {output_path}")
        return output_path
    except Exception as e:
        logging.error(f"Image generation error for prompt '{image_prompt}': {e}")
        return None

def generate_images_from_blog_json(blog_json, output_dir="static/blogs"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    image_prompts = blog_json.get("image_prompts", [])
    image_path = []
    for idx, prompt in enumerate(image_prompts):
        filename = Path(output_dir) / f"image{idx + 1}.png"
        im_path = generate_image_from_prompt(prompt, filename)
        image_path.append(str(im_path))
    logging.info(f"Generated {len(image_path)} images from blog JSON")
    return image_path


def clean_json_string(json_string):
    cleaned_string = re.sub(r"```json|```", "", json_string).strip()
    cleaned_string = re.sub(r"[\x00-\x1F\x7F]", "", cleaned_string)
    return cleaned_string

def save_json_to_file(json_string, filename="corrected_blog.json"):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    corrected_json_str = clean_json_string(json_string)
    try:
        data = json.loads(corrected_json_str)
        with open(filename, "w", encoding="utf-8") as corrected_file:
            json.dump(data, corrected_file, indent=4, ensure_ascii=False)
        logging.info(f"Corrected JSON saved as '{filename}' ✅")
        return data
    except json.JSONDecodeError as e:
        logging.error(f"Error in JSON format: {e}")
        return None

def save_markdown_file(blog_data, image_paths, output_dir="static/blogs"):
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    title = blog_data.get("title", "Untitled Blog")
    content = blog_data.get("content", "")
    markdown_lines = [f"# {title}\n", content.strip() + "\n"]

    md_path = Path(output_dir) / "blogs.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(markdown_lines))

    logging.info(f"Markdown file saved to: {md_path}")
    return str(md_path)

def read_markdown_content(markdown_path: str) -> str:
    try:
        with open(markdown_path, "r", encoding="utf-8") as f:
            logging.info(f"Successfully read Markdown content from: {markdown_path}")
            return f.read()
    except Exception as e:
        logging.error(f"Failed to read Markdown file '{markdown_path}': {e}")
        raise RuntimeError(f"Failed to read Markdown file: {str(e)}")
