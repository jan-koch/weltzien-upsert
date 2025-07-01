import os
from fastapi import FastAPI, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
from langchain.embeddings import OpenAIEmbeddings
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHROMA_REMOTE_URL = os.getenv("CHROMA_REMOTE_URL", "https://cdb.kobra-dataworks.de")
CHROMA_BEARER_TOKEN = os.getenv("CHROMA_BEARER_TOKEN")
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "weltzien_dms")

if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY environment variable is not set.")
    raise RuntimeError("OPENAI_API_KEY environment variable is required")

if not CHROMA_BEARER_TOKEN:
    logger.error("CHROMA_BEARER_TOKEN environment variable is not set.")
    raise RuntimeError("CHROMA_BEARER_TOKEN environment variable is required")

# Initialize FastAPI app
app = FastAPI()

# Initialize OpenAI embeddings
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

# Initialize Chroma client with bearer token authentication
class BearerAuthHeaders:
    def __init__(self, token: str):
        self.token = token

    def __call__(self):
        return {"Authorization": f"Bearer {self.token}"}

auth_headers = BearerAuthHeaders(CHROMA_BEARER_TOKEN)

client = chromadb.Client(
    Settings(
        chroma_api_impl="rest",
        chroma_server_host=CHROMA_REMOTE_URL.replace("https://", "").replace("http://", ""),
        chroma_server_http_port=443,
        chroma_server_ssl_enabled=True,
        chroma_api_key=None,
        chroma_headers=auth_headers(),
    )
)

# Ensure collection exists or create it
try:
    collection = client.get_collection(name=CHROMA_COLLECTION_NAME)
except chromadb.errors.NotFoundError:
    collection = client.create_collection(name=CHROMA_COLLECTION_NAME)

# Pydantic model for request body
class UpsertTextRequest(BaseModel):
    text: str
    metadata: Optional[Dict[str, Any]] = None
    id: Optional[str] = None  # Optional unique ID for the vector

@app.post("/upsert-text")
async def upsert_text(request: UpsertTextRequest):
    try:
        text = request.text
        metadata = request.metadata or {}
        vector_id = request.id

        if not text.strip():
            raise HTTPException(status_code=400, detail="Text content cannot be empty")

        # Generate embedding
        embedding_vector = embeddings.embed_query(text)

        # Prepare upsert data
        ids = [vector_id] if vector_id else [os.urandom(16).hex()]
        documents = [text]
        metadatas = [metadata]

        # Upsert into ChromaDB
        collection.upsert(
            ids=ids,
            embeddings=[embedding_vector],
            documents=documents,
            metadatas=metadatas,
        )

        logger.info(f"Upserted vector with id {ids[0]} into collection {CHROMA_COLLECTION_NAME}")

        return {"status": "success", "id": ids[0]}

    except Exception as e:
        logger.error(f"Error during upsert: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
