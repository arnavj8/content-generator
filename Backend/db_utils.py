from pymongo import MongoClient
from typing import Dict
import logging
import re
import os
from Backend.logger import logging
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    _instance = None
    _keys = None
    
    # Default fallback keys
    DEFAULT_KEYS = {
        "gemini_key": os.getenv("GEN_API_KEY"),
        "huggingface_key": os.getenv("HF_API_TOKEN") 
    }
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = DatabaseManager()
            # Initialize with default keys immediately so they're always available
            cls._instance._keys = cls.DEFAULT_KEYS.copy()
            logging.info("DatabaseManager initialized with default API keys")
        return cls._instance
    
    def initialize(self, mongo_uri: str):
        # Always start with default keys
        self._keys = self.DEFAULT_KEYS.copy()
        logging.info("Starting with default keys before DB connection attempt")
        
        try:
            logging.info("Attempting to initialize database connection")
            self.client = MongoClient(mongo_uri)
            self.db = self.client.ai_generator
            
            # Test connection
            self.client.server_info()
            
            # Only override defaults if DB keys exist
            keys_doc = self.db.api_keys.find_one({"_id": "keys"})
            if keys_doc and keys_doc.get("gemini_key") and keys_doc.get("huggingface_key"):
                self._keys = {
                    "gemini_key": keys_doc.get("gemini_key"),
                    "huggingface_key": keys_doc.get("huggingface_key")
                }
                logging.info("Successfully loaded API keys from database")
            else:
                logging.info("No valid keys found in database, using default keys")
            return True
        except Exception as e:
            logging.error(f"Database connection error: {e}")
            logging.info("Using default keys due to database connection error")
            # No need to set _keys here as we've already set it at the start
            return False


    def save_keys(self, gemini_key: str, huggingface_key: str):
        try:
            logging.info("Attempting to save API keys")
            self.db.api_keys.update_one(
                {"_id": "keys"},
                {"$set": {
                    "gemini_key": gemini_key,
                    "huggingface_key": huggingface_key
                }},
                upsert=True
            )
            self._keys = {
                "gemini_key": gemini_key,
                "huggingface_key": huggingface_key
            }
            logging.info("Successfully saved API keys")
            return True
        except Exception as e:
            logging.error(f"Error saving keys: {e}")
            return False

    def get_keys(self) -> Dict[str, str]:
        # Ensure we always return valid keys
        if not self._keys or not all(self._keys.values()):
            logging.warning("API keys not properly set in memory, using default keys")
            self._keys = self.DEFAULT_KEYS.copy()
        return self._keys

    def is_using_default_keys(self) -> bool:
        """Check if currently using default keys"""
        return self._keys == self.DEFAULT_KEYS
    
def get_api_keys():
    db = DatabaseManager.get_instance()
    keys = db.get_keys()
    
    if not keys:
        logging.error("API keys not found")
        raise ValueError("API keys not configured")
    
    # Set environment variables
    os.environ['HF_API_TOKEN'] = keys['huggingface_key']
    os.environ['GEN_API_KEY'] = keys['gemini_key']
    
    return keys


from Backend.logger import logging

def ensure_api_keys():
    """Ensure API keys are available and set in environment variables"""
    try:
        db = DatabaseManager.get_instance()
        keys = db.get_keys()
        
        # Always set environment variables, even with default keys
        os.environ['HF_API_TOKEN'] = keys['huggingface_key']
        os.environ['GEN_API_KEY'] = keys['gemini_key']
        
        if db.is_using_default_keys():
            logging.warning("Using default API keys - functionality may be limited")
        
        return True
    except Exception as e:
        logging.error(f"Error ensuring API keys: {str(e)}")
        # Set environment variables with default keys as last resort
        os.environ['HF_API_TOKEN'] = DatabaseManager.DEFAULT_KEYS['huggingface_key']
        os.environ['GEN_API_KEY'] = DatabaseManager.DEFAULT_KEYS['gemini_key']
        return False