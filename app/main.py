import os
import time
import hashlib
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
import logging
from langchain_openai import OpenAIEmbeddings
import chromadb
from chromadb.errors import ChromaError
from dotenv import load_dotenv

load_dotenv()

# Configure structured logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHROMA_REMOTE_URL = os.getenv("CHROMA_REMOTE_URL", "https://cdb.kobra-dataworks.de")
CHROMA_BEARER_TOKEN = os.getenv("CHROMA_BEARER_TOKEN")
CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "weltzien_dms")
API_BEARER_TOKEN = os.getenv("API_BEARER_TOKEN")

if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY environment variable is not set.")
    raise RuntimeError("OPENAI_API_KEY environment variable is required")

if not CHROMA_BEARER_TOKEN:
    logger.error("CHROMA_BEARER_TOKEN environment variable is not set.")
    raise RuntimeError("CHROMA_BEARER_TOKEN environment variable is required")

if not API_BEARER_TOKEN:
    logger.error("API_BEARER_TOKEN environment variable is not set.")
    raise RuntimeError("API_BEARER_TOKEN environment variable is required")

# Global variables for client and collection
client = None
collection = None
embeddings = None

# Security setup
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify the Bearer token"""
    if credentials.credentials != API_BEARER_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

def sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize metadata to ensure all values are ChromaDB-compatible types.
    ChromaDB only accepts str, int, float, bool, or None values.
    """
    if not metadata:
        return metadata
    
    sanitized = {}
    conversions = []
    
    for key, value in metadata.items():
        if value is None or isinstance(value, (str, int, float, bool)):
            # Already valid ChromaDB types
            sanitized[key] = value
        elif isinstance(value, list):
            # Convert lists to comma-separated strings
            try:
                sanitized[key] = ", ".join(str(item) for item in value)
                conversions.append(f"'{key}': list -> comma-separated string")
            except Exception:
                sanitized[key] = str(value)
                conversions.append(f"'{key}': list -> string representation")
        elif isinstance(value, dict):
            # Convert dicts to JSON strings
            try:
                import json
                sanitized[key] = json.dumps(value)
                conversions.append(f"'{key}': dict -> JSON string")
            except Exception:
                sanitized[key] = str(value)
                conversions.append(f"'{key}': dict -> string representation")
        else:
            # Convert any other type to string
            sanitized[key] = str(value)
            conversions.append(f"'{key}': {type(value).__name__} -> string")
    
    if conversions:
        logger.info(f"Metadata conversions applied: {', '.join(conversions)}")
        # Add a note about conversions to the metadata
        sanitized["_metadata_conversions"] = f"Applied conversions: {'; '.join(conversions)}"
    
    return sanitized


async def initialize_services():
    """Initialize ChromaDB client and OpenAI embeddings"""
    global client, collection, embeddings
    
    try:
        # Initialize OpenAI embeddings
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        
        # Initialize Chroma client
        auth_headers = {"Authorization": f"Bearer {CHROMA_BEARER_TOKEN}"}
        client = chromadb.HttpClient(
            host=CHROMA_REMOTE_URL.replace("https://", "").replace("http://", ""),
            port=443,
            ssl=True,
            headers=auth_headers
        )
        
        # Test connection and get/create collection
        try:
            collection = client.get_collection(name=CHROMA_COLLECTION_NAME)
            logger.info(f"Connected to existing collection: {CHROMA_COLLECTION_NAME}")
        except chromadb.errors.NotFoundError:
            collection = client.create_collection(name=CHROMA_COLLECTION_NAME)
            logger.info(f"Created new collection: {CHROMA_COLLECTION_NAME}")
            
        logger.info("Successfully initialized all services")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise RuntimeError(f"Service initialization failed: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await initialize_services()
    yield
    # Shutdown - cleanup if needed
    logger.info("Application shutting down")

# Initialize FastAPI app with lifespan management
app = FastAPI(
    title="Text Embedding and Vector Upsert API",
    description="API for embedding text using OpenAI and upserting vectors to ChromaDB",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Pydantic models
class UpsertTextRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50000, description="Text content to embed")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata to store with the vector")
    id: Optional[str] = Field(default=None, description="Optional unique ID for the vector")
    
    @validator('text')
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError('Text content cannot be empty or whitespace only')
        return v.strip()

class UpsertResponse(BaseModel):
    status: str = Field(..., description="Operation status")
    documents_upserted: int = Field(..., description="Number of documents successfully upserted")
    ids: List[str] = Field(..., description="List of document IDs that were upserted")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    services: Dict[str, str]

class CollectionInfoResponse(BaseModel):
    collection_name: str = Field(..., description="Name of the ChromaDB collection")
    document_count: int = Field(..., description="Total number of documents in the collection")
    sample_documents: List[Dict[str, Any]] = Field(..., description="Sample documents from the collection")
    timestamp: str = Field(..., description="Timestamp when the info was retrieved")

@app.post("/upsert-text", response_model=UpsertResponse)
async def upsert_text(request: UpsertTextRequest, token: str = Depends(verify_token)):
    start_time = time.time()
    
    try:
        # Validate services are initialized
        if not all([client, collection, embeddings]):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Services not properly initialized"
            )

        text = request.text
        metadata = request.metadata or {}
        vector_id = request.id

        # Generate unique ID if not provided
        if not vector_id:
            text_hash = hashlib.md5(text.encode()).hexdigest()
            timestamp = str(int(time.time() * 1000))
            vector_id = f"{text_hash}_{timestamp}"

        # Add timestamp to metadata
        metadata.update({
            "upserted_at": time.time(),
            "text_length": len(text)
        })

        # Sanitize metadata to ensure ChromaDB compatibility
        metadata = sanitize_metadata(metadata)

        # Generate embedding
        try:
            embedding_vector = embeddings.embed_query(text)
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to generate embedding"
            )

        # Prepare upsert data
        ids = [vector_id]
        documents = [text]
        metadatas = [metadata]

        # Upsert into ChromaDB
        try:
            collection.upsert(
                ids=ids,
                embeddings=[embedding_vector],
                documents=documents,
                metadatas=metadatas,
            )
        except ChromaError as e:
            logger.error(f"ChromaDB error: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to upsert to vector database"
            )

        processing_time = (time.time() - start_time) * 1000
        
        logger.info(
            f"Successfully upserted vector - ID: {vector_id}, "
            f"Collection: {CHROMA_COLLECTION_NAME}, "
            f"Processing time: {processing_time:.2f}ms"
        )

        return UpsertResponse(
            status="success",
            documents_upserted=1,
            ids=ids,
            processing_time_ms=round(processing_time, 2)
        )

    except HTTPException:
        raise
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(
            f"Unexpected error during upsert: {e}, "
            f"Processing time: {processing_time:.2f}ms", 
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring"""
    services_status = {
        "openai_embeddings": "healthy" if embeddings else "unhealthy",
        "chromadb_client": "healthy" if client else "unhealthy",
        "chromadb_collection": "healthy" if collection else "unhealthy"
    }
    
    overall_status = "healthy" if all(status == "healthy" for status in services_status.values()) else "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        services=services_status
    )

@app.get("/collection-info", response_model=CollectionInfoResponse)
async def get_collection_info(token: str = Depends(verify_token)):
    """Get ChromaDB collection information and sample documents"""
    try:
        # Validate services are initialized
        if not all([client, collection]):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="ChromaDB services not properly initialized"
            )

        # Get collection count
        try:
            document_count = collection.count()
        except Exception as e:
            logger.error(f"Failed to get collection count: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to retrieve collection count"
            )

        # Get sample documents (peek)
        sample_documents = []
        try:
            # Peek at up to 5 documents
            peek_result = collection.peek(limit=5)
            
            if peek_result and 'ids' in peek_result:
                for i, doc_id in enumerate(peek_result['ids']):
                    sample_doc = {
                        "id": doc_id,
                        "document": peek_result.get('documents', [None])[i] if i < len(peek_result.get('documents', [])) else None,
                        "metadata": peek_result.get('metadatas', [None])[i] if i < len(peek_result.get('metadatas', [])) else None
                    }
                    # Truncate long documents for readability
                    if sample_doc["document"] and len(sample_doc["document"]) > 200:
                        sample_doc["document"] = sample_doc["document"][:200] + "..."
                    sample_documents.append(sample_doc)
        except Exception as e:
            logger.warning(f"Failed to peek at collection documents: {e}")
            # Continue without sample documents rather than failing

        logger.info(f"Retrieved collection info - Name: {CHROMA_COLLECTION_NAME}, Count: {document_count}")

        return CollectionInfoResponse(
            collection_name=CHROMA_COLLECTION_NAME,
            document_count=document_count,
            sample_documents=sample_documents,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting collection info: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Text Embedding and Vector Upsert API",
        "version": "1.0.0",
        "endpoints": {
            "POST /upsert-text": "Embed text and upsert to ChromaDB",
            "GET /collection-info": "Get collection details and sample documents",
            "GET /health": "Health check",
            "GET /docs": "API documentation"
        }
    }