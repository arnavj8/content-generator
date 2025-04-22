import os
import sys
from pathlib import Path

# Resolve the full path to the Backend directory
BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "Backend"

# Change the current working directory to Backend
os.chdir(BACKEND_DIR)

# Optional: Add Backend to Python path (if using relative imports)
sys.path.insert(0, str(BACKEND_DIR))

# Import FastAPI app from Backend/main.py
from main import app as application

# Uvicorn server entry
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))  # Render auto-sets this
    uvicorn.run("main:app", host="0.0.0.0", port=port)
