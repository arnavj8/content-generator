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
import threading
from Backend.logger import logging
from dotenv import load_dotenv
from Backend.db_utils import ensure_api_keys
try:
    # Ensure API keys are available
    ensure_api_keys()
    
    # Use the keys
    # HF_API_TOKEN = os.getenv('HF_API_TOKEN')
    GEMINI_API_KEY = os.getenv('GEN_API_KEY')
    

    
except Exception as e:
    logging.error(f"Error: {str(e)}")
load_dotenv()
# GEMINI_API_KEY = os.getenv("GEN_API_KEY")
GITHUB_REPO_URL = os.getenv("GITHUB_REPO_URL")

class KnowledgeBase:
    def __init__(self):
        self.initialized = False
        self.repo_path = None
        self.embeddings = None
        self.index = None
        self.metadata = []
        self._initialization_lock = threading.Lock()
        self._initialization_in_progress = False

    def initialize(self):
        """Initialize the knowledge base"""
        temp_dir = None
        
        with self._initialization_lock:
            if self.initialized:
                logging.info("Knowledge base already initialized")
                return True
            
            if self._initialization_in_progress:
                logging.info("Initialization already in progress")
                return False
            
            self._initialization_in_progress = True
        
        try:
            logging.info("Starting initialization...")
            
            # Validate environment variables
            if not GITHUB_REPO_URL:
                raise ValueError("GITHUB_REPO_URL not set in environment variables")
            if not GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY not set in environment variables")
            
            # Configure Gemini
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

            # Mark as initialized
            with self._initialization_lock:
                self.initialized = True
                self._initialization_in_progress = False
            
            logging.info("Initialization complete!")
            return True
        
        except Exception as e:
            logging.error(f"Initialization failed: {str(e)}")
            
            # Cleanup temp directory if it exists
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            
            # Reset initialization state
            with self._initialization_lock:
                self.initialized = False
                self._initialization_in_progress = False
            
            return False

    # Rest of the methods remain the same as in your previous implementation

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
            '.mp3', '.zip', '.tar', '.gz', '.pdf', '.pyc', '.ttf', '.html','.js',
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

            prompt = f"""You are a specialized AI assistant focused on explaining this specific codebase and project. Your primary role is to provide accurate, technical, and helpful information about the project's implementation, architecture, and functionality.

                Guidelines for responding:

                1. Greeting Handling:
                - If the user sends a greeting (hello, hi, hey), respond warmly and offer assistance
                - Mention that you're an AI assistant for this project's code repository only on greetings

                2. Question Answering:
                - Use ONLY the provided context to formulate your responses
                - Be precise and directly address the user's query
                - If the information is not in the context, clearly state that you don't have enough information

                3. Technical Explanation:
                - When explaining code, provide detailed technical breakdowns
                - Include relevant code snippets from context if available
                - Explain the implementation logic and design patterns

                4. Architecture Discussion:
                - When discussing project structure, explain the relationships between components
                - Highlight the system design decisions and their implications
                - Focus on how different parts interact

                5. Error Handling:
                - For debugging questions, analyze potential issues systematically
                - Suggest troubleshooting steps based on the codebase
                - Reference specific error handling patterns in the code

                6. Response Style:
                - Be friendly and professional
                - Provide clear and concise answers
                - If uncertain, admit the limitation honestly

                CONTEXT:
                {context}

                CURRENT QUERY: {user_query}

                Additional Instructions:
                - First identify the most relevant guideline category for this query
                - Follow those guidelines while maintaining natural conversation flow
                - Prioritize accuracy over speculation and tried to answer in short max 150 workds
                - If asked about your creation, mention you're an AI assistant for the project
                - Focus on helping users understand the project's code and functionality"""
                
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


