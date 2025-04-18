# 🎨 CreativeNexusAI

**CreativeNexusAI** is an all-in-one AI-powered content creation studio that empowers users to generate **blogs**, **images**, **videos**, and **memes** in just a few clicks. Leveraging powerful models via **Google Gemini** and **HuggingFace**, it’s perfect for creators, marketers, and developers looking to scale creativity at lightning speed.

---

## 🚀 Features

- ✍️ **Blog Generator** – Create SEO-friendly blog posts by specifying topic, tone, and length.
- 🖼️ **Image Generator** – Generate stunning visuals from text prompts (anime, realistic, oil painting styles & more).
- 🎥 **Video Generator** – Convert written topics into styled short videos (documentary, cinematic).
- 😂 **Meme Generator** – Make hilarious and multilingual memes with emotion-based captions.
- 🤖 **Chatbot Assistant** – Built-in chatbot for help, guidance, and exploration.

---

## 🧩 How It Works

### ✍️ Blog Generator

- Input topic, style, and length.
- Sends a POST request to `/generate_blog`.
- Uses Gemini/HuggingFace to return markdown content rendered with Tailwind + `marked.js`.

### 🖼️ Image Generator

- Enter image description + style.
- Sends request to `/generate-image`.
- Returns base64 image, rendered with `<img>` tag.

### 🎥 Video Generator

- Accepts topic + optional style.
- Calls `/generate_video`, returns a video blob.
- Preview via `URL.createObjectURL`.

### 😂 Meme Generator

- Inputs: idea, emotion, and language.
- Endpoint: `/generate_meme`.
- Output: caption + meme image.

---

## 🛠 Tech Stack

### 💡 Backend

- **Framework**: FastAPI
- **Endpoints**:
  - `/generate_blog`
  - `/generate-image`
  - `/generate_meme`
  - `/generate_video`
  - `/api/chat`
  - `/api/initialize`
  - `/api/status`

### 🎨 Frontend

- HTML + TailwindCSS + Vanilla JavaScript
- `marked.js` for markdown rendering
- Feather Icons, Typing Sound FX, Chatbot UI

### 🤖 AI Services

- **Google Gemini API**  
  - Text Generation: `gemini-1.5-pro`  
  - Embeddings: `models/embedding-001`

- **HuggingFace Models**  
  - Image Generation: `stabilityai/stable-diffusion-xl-base-1.0`  
  - Music Generation: `facebook/musicgen-small`

### 🗄️ Database

- **MongoDB Atlas** – stores API keys and settings

---

## ⚙️ Getting Started

### 1. Clone the Repo

```bash
git clone https://github.com/your-username/CreativeNexusAI.git
cd CreativeNexusAI
```

### 2. Configure API Keys

On the app's configuration panel, enter:

- **MongoDB URI**  
  Format:  
  `mongodb+srv://username:password@cluster.mongodb.net/dbname?retryWrites=true&w=majority`

- **Google Gemini API Key** → [Get here](https://makersuite.google.com/app/apikey)
- **HuggingFace API Key** → [Get here](https://huggingface.co/settings/tokens)

### 3. Run the Backend

```bash
uvicorn main:app --reload
```

### 4. View in Browser

Navigate to:  
`http://localhost:8000`

---

## 🌍 Deployment

The app is **deployed on Render** using **Quick FastAPI + static deployment**. To replicate the deployment:

1. Push your code to GitHub.
2. Go to [Render](https://render.com).
3. Select **New Web Service** → Connect your GitHub repo.
4. Configure the backend:

   - **Environment**: Python 3.x
   - **Build Command**:
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     uvicorn main:app --host=0.0.0.0 --port=10000
     ```
   - **Environment Variables**:  
     Add your:
     - `MONGODB_URI`
     - `GEMINI_API_KEY`
     - `HUGGINGFACE_API_KEY`

5. For static frontend:
   - Serve via FastAPI static routes, or
   - Deploy via Render Static Site (point to frontend folder)

---

## 🔍 Use Cases

🎯 Marketing Automation
Generate blogs, images, and videos at scale to power brand campaigns effortlessly.

🏫 EdTech Content
Turn educational topics into blogs, explainers, and memes for better learning.

📱 Social Media Studio
Create trendy, multilingual content packs for reels, posts, and viral memes.

🚀 Startup MVP Tool
Build or demo AI-powered content generation features rapidly using modular FastAPI endpoints.

🌐 Multilingual Reach
Produce emotion-based, language-adaptive content for diverse global audiences.

🧠 Personal Branding
Boost your portfolio with AI-generated blogs, visuals, and videos in minutes.

---

## 📁 Project Structure

```
CreativeNexusAI/
├── app/                                 # Core FastAPI backend app
│   ├── api/                             # All API route handlers
│   │   ├── audio_generator.py
│   │   ├── blog.py
│   │   ├── chatbot.py
│   │   ├── image_generator.py
│   │   ├── meme.py
│   │   ├── music_generator.py
│   │   ├── text_generator.py
│   │   └── video_generator.py
│   │
│   ├── core/                            # Config & utilities
│   │   ├── config.py
│   │   ├── logger.py
│   │   └── db_utils.py
│   │
│   ├── static/                          # Static files
│   │   ├── assets/
│   │   │   ├── fonts/
│   │   │   │   ├── arial.ttf
│   │   │   │   └── arial_hindi.ttf
│   │   │   ├── images/
│   │   │   │   ├── blog.png
│   │   │   │   ├── logo.png
│   │   │   │   └── robot.png
│   │   │   └── audio/
│   │   │       ├── bot.mp3
│   │   │       ├── click.mp3
│   │   │       └── typing.mp3
│   │   ├── js/
│   │   │   └── script.js
│   │   └── blogs/
│   │
│   ├── templates/                       # Jinja2 HTML templates
│   │   ├── sidebar.html                 # Moved here directly
│   │   ├── home.html
│   │   ├── chat.html
│   │   ├── chatbot.html
│   │   ├── blog_generator.html
│   │   ├── image_generator.html
│   │   ├── meme_generator.html
│   │   └── video_generator.html
│   │
│   ├── logs/
│   ├── main.py
│   └── __init__.py
│
├── venv/
├── .env
├── .gitignore
├── README.md
├── requirements.txt
└── setup.py
```
---

## 👨‍💻 Contributors

- **Gaurav Kumar Chaurasiya** [GitHub](https://github.com/gauravkumarchaurasiya) | [LinkedIn](https://www.linkedin.com/in/gauravkumarchaurasiya)
- **Arnav Jain** – [GitHub](https://github.com/arnavj8) | [LinkedIn](https://linkedin.com/in/arnav-jain1)

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

## 🤝 Contributing

We welcome contributions!

1. Fork the project
2. Create a new branch (`git checkout -b feature/my-feature`)
3. Commit your changes
4. Open a Pull Request

---

> _“Transform creativity with AI — faster, smarter, and better with CreativeNexusAI.”_
