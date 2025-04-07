import os
import json
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from Backend.meme import generate_meme_content, add_meme_text,generate_meme_image
from Backend.blog import fetch_news_newsapi,fetch_arxiv,fetch_wikipedia,generate_blog_with_gemini,duckduckgo_instant_answer,save_json_to_file,generate_image_from_prompt,generate_images_from_blog_json,save_markdown_file,read_markdown_content
from Backend.images import generate_image_from_topic_and_style

# Create FastAPI app
app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Pydantic models for input validation
class MemeRequest(BaseModel):
    topic: str
    style: str
    language: str

class BlogRequest(BaseModel):
    topic: str
    style: str
    length: str

class ImageRequest(BaseModel):
    topic: str
    style: str
    
@app.get("/", response_class=FileResponse)
async def serve_home():
    return FileResponse("static/home.html")

# API to generate meme
@app.post("/generate_meme")
async def generate_meme(request: MemeRequest):
    topic = request.topic
    style = request.style
    language = request.language
    # Generate meme content
    meme_caption, image_prompt, text_color, text_position, language = generate_meme_content(topic, style,language)

    # Generate meme image
    try:
        meme_image = generate_meme_image(image_prompt)
        meme_image_path = os.path.join("static", "generated_meme.png")
        meme_image.save(meme_image_path)

        # Add meme text
        final_meme = add_meme_text(meme_image, meme_caption, text_color, text_position, language)
        final_meme.save(meme_image_path)

        # Return meme caption and image URL
        return {
            "caption": meme_caption,
            "image_url": f"/static/generated_meme.png"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating meme: {str(e)}")

# Serve the static files (images)
@app.get("/static/{file_path}")
async def get_file(file_path: str):
    file_location = os.path.join("static", file_path)
    if os.path.exists(file_location):
        return FileResponse(file_location)
    else:
        raise HTTPException(status_code=404, detail="File not found")

@app.post("/generate_blog")
async def generate_blog(request: BlogRequest):
    topic = request.topic
    style = request.style
    length= request.length
    try:
        print("taking contents...")
        context = ""
        sources = [fetch_wikipedia, fetch_arxiv, fetch_news_newsapi, duckduckgo_instant_answer]
        for source in sources:
            context += source(topic) + "\n\n"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Context fetching error: {str(e)}")

    # Step 2: Generate blog with Gemini
    try:
        print("creating blog...")
        raw_blog = generate_blog_with_gemini(context, topic,style,length)
        if isinstance(raw_blog, dict) and "error" in raw_blog:
            raise ValueError(raw_blog["error"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Blog generation error: {str(e)}")

    # Step 3: Clean and save the blog JSON
    try:
        parsed_data = save_json_to_file(raw_blog, filename="static/blogs/final_blog.json")
        if parsed_data is None:
            raise ValueError("Invalid blog JSON structure.")

        # Generate images
        image_paths = generate_images_from_blog_json(parsed_data)
        
        print(image_paths)
        # Save blog as Markdown with image links
        markdown_path= save_markdown_file(parsed_data, image_paths, output_dir="static/blogs")
        print(markdown_path)
        show = read_markdown_content(markdown_path=markdown_path)
        print(" show : ",show)
        return show

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"JSON saving/parsing error: {str(e)}")

@app.post("/generate-image/")
async def generate_image_api(request: ImageRequest):
    try:
        description, image_base64 = generate_image_from_topic_and_style(
            request.topic, request.style
        )
        return {
            "description": description,
            "image": image_base64
        }
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


# Run FastAPI app
if __name__ == "__main__":
    if not os.path.exists("static"):
        os.makedirs("static")

    uvicorn.run(app, host="0.0.0.0", port=8000)
