import os
import tempfile
import shutil
from pathlib import Path
import requests
import zipfile
import io
import numpy as np
import faiss
import google.generativeai as genai
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import logging
from Backend.logger import logging
from dotenv import load_dotenv
load_dotenv()
GEMINI_API_KEY = os.getenv("GEN_API_KEY")
GITHUB_REPO_URL = os.getenv("GITHUB_REPO_URL")
if not GEMINI_API_KEY or not GITHUB_REPO_URL:
    raise ValueError("Required environment variables are not set")

class KnowledgeBase:
    def __init__(self):
        self.initialized = False
        self.repo_path = None
        self.embeddings = None
        self.index = None
        self.metadata = []

    def initialize(self):
        """Initialize the knowledge base"""
        temp_dir = None
        try:
            logging.info("Starting initialization...")
            if not GITHUB_REPO_URL:
                raise ValueError("GITHUB_REPO_URL not set in environment variables")
            if not GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY not set in environment variables")
            genai.configure(api_key=GEMINI_API_KEY)

            # Set up embeddings
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model="models/embedding-001",
                google_api_key=GEMINI_API_KEY
            )

            # Create temp directory for repo
            temp_dir = tempfile.mkdtemp()
            self.repo_path = os.path.join(temp_dir, "repo")
            os.makedirs(self.repo_path, exist_ok=True)

            # Download repository
            self._download_repo()

            # Process files
            self._process_files()

            self.initialized = True
            print("Initialization complete!")
            return True

        except Exception as e:
            print(f"Error during initialization: {str(e)}")
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            return False

    def _download_repo(self):
        """Download the GitHub repository"""
        repo_parts = GITHUB_REPO_URL.rstrip('/').split('/')
        repo_name = repo_parts[-1]
        repo_owner = repo_parts[-2]

        # Try main branch first, then master
        for branch in ['main', 'master']:
            zip_url = f"https://github.com/{repo_owner}/{repo_name}/archive/refs/heads/{branch}.zip"
            print(f"Trying to download from {zip_url}")

            response = requests.get(zip_url)
            if response.status_code == 200:
                with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                    z.extractall(self.repo_path)
                print(f"Downloaded and extracted {branch} branch")

                # Update repo_path to point to extracted directory
                extracted_dirs = [d for d in os.listdir(self.repo_path)
                                if os.path.isdir(os.path.join(self.repo_path, d))]
                if extracted_dirs:
                    self.repo_path = os.path.join(self.repo_path, extracted_dirs[0])
                return

        raise Exception("Failed to download repository")

    def _process_files(self):
        """Process and index repository files"""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=200
        )

        all_embeddings = []
        doc_id = 0

        # Process files
        for file_path in Path(self.repo_path).glob("**/*"):
            if file_path.is_file() and self._should_process_file(file_path):
                try:
                    relative_path = file_path.relative_to(self.repo_path)
                    content = file_path.read_text(errors='ignore')

                    chunks = text_splitter.split_text(content)
                    print(f"Processing {relative_path}: {len(chunks)} chunks")

                    for i, chunk in enumerate(chunks):
                        try:
                            embedding = self.embeddings.embed_documents([chunk])[0]
                            if embedding:  # Check if embedding is not None
                                all_embeddings.append(embedding)
                                self.metadata.append({
                                    "source": str(relative_path),
                                    "chunk": i,
                                    "total_chunks": len(chunks),
                                    "text": chunk
                                })
                                doc_id += 1
                        except Exception as e:
                            print(f"Error embedding chunk {i} from {relative_path}: {str(e)}")
                            continue
                except Exception as e:
                    print(f"Error processing {file_path}: {str(e)}")
                    continue

        # Create FAISS index
        if all_embeddings:
            dimension = len(all_embeddings[0])
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(np.array(all_embeddings).astype('float32'))
            print(f"Processed {doc_id} documents")
        else:
            raise Exception("No embeddings were generated")

    def _should_process_file(self, file_path):
        """Determine if a file should be processed"""
        if any(part.startswith('.') for part in file_path.parts):
            return False

        ignored_extensions = {
            '.exe', '.bin', '.jpg', '.jpeg', '.png', '.gif', '.mp4',
            '.mp3', '.zip', '.tar', '.gz', '.pdf', '.pyc'
        }

        if file_path.suffix.lower() in ignored_extensions:
            return False

        if file_path.stat().st_size > 1024 * 1024:  # Skip files > 1MB
            return False

        return True

    def query(self, user_query: str) -> str:
        """Query the knowledge base"""
        if not self.initialized:
            return "Knowledge base not initialized"

        try:
            # Search for relevant content
            query_embedding = self.embeddings.embed_query(user_query)
            query_embedding = np.array(query_embedding).astype('float32').reshape(1, -1)
            distances, indices = self.index.search(query_embedding, 5)

            # Prepare context
            context = "\n\n".join([
                f"[From {self.metadata[idx]['source']}, chunk {self.metadata[idx]['chunk']+1}/{self.metadata[idx]['total_chunks']}]\n{self.metadata[idx]['text']}"
                for idx in indices[0]
            ])

            # Generate response with Gemini
            model = genai.GenerativeModel('gemini-1.5-pro')

            prompt = f"""You are a helpful AI assistant for this project. Answer all queries to user based to the project context in confidence. You should:
                1. If the user's message is a greeting (like "hello", "hi", "hey"), respond with a friendly greeting and offer to help with questions about the code.
                2. For other questions, use ONLY the context provided below to answer.
                3. If you don't know or the information isn't in the context, say so honestly.

                CONTEXT:
                {context}

                QUESTION: {user_query}

                Remember:
                - For greetings, be friendly and welcoming
                - For technical questions, use ONLY the information from the context
                - Be clear when information is not available in the context"""

            response = model.generate_content(prompt)
            return response.text if response else "Could not generate response"

        except Exception as e:
            return f"Error: {str(e)}"
        
        
    def cleanup(self):
        """Cleanup resources"""
        try:
            if self.repo_path and os.path.exists(self.repo_path):
                parent_dir = os.path.dirname(self.repo_path)
                if os.path.exists(parent_dir):
                    shutil.rmtree(parent_dir)
            self.initialized = False
            self.index = None
            self.metadata = []
        except Exception as e:
            logging.error(f"Error during cleanup: {str(e)}")

