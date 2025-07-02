# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Application Overview

This is a FastAPI application that provides a REST API for embedding text using OpenAI and upserting vectors into a remote ChromaDB instance. The main application is in `app/main.py`.

## Architecture

- **FastAPI Application**: Single-file application providing text embedding and vector storage
- **OpenAI Integration**: Uses LangChain's OpenAIEmbeddings for text-to-vector conversion
- **ChromaDB Client**: Connects to remote ChromaDB instance with bearer token authentication
- **Environment Configuration**: Uses .env file for API keys and service URLs

## Required Environment Variables

The application requires these environment variables (configured in `.env` or `.env.local`):
- `OPENAI_API_KEY`: OpenAI API key for embeddings
- `CHROMA_REMOTE_URL`: ChromaDB server URL (default: https://cdb.kobra-dataworks.de)
- `CHROMA_BEARER_TOKEN`: Authentication token for ChromaDB
- `CHROMA_COLLECTION_NAME`: Collection name in ChromaDB (default: weltzien_dms)
- `API_BEARER_TOKEN`: Bearer token for API authentication (protects endpoints from abuse)
- `DOCS_REQUIRE_AUTH`: Whether docs endpoint requires authentication (default: true)

**Note**: `.env.local` takes precedence over `.env` if both files exist, allowing for local development overrides.

## Running the Application

```bash
# Install dependencies (infer from imports in main.py)
pip install fastapi uvicorn langchain openai chromadb python-dotenv

# Run the development server
uvicorn app.main:app --reload

# For production (localhost only for security)
uvicorn app.main:app --host 127.0.0.1 --port 8088
```

## API Endpoints

- `POST /upsert-text`: Embeds text using OpenAI and upserts vector into ChromaDB
  - **Authentication**: Requires Bearer token in Authorization header
  - Request body: `{"text": "string", "metadata": {}, "id": "optional_id"}`
  - **Metadata types**: Supports str, int, float, bool, None. Lists/dicts are auto-converted to strings
  - Returns: `{"status": "success", "documents_upserted": 1, "ids": ["vector_id"], "processing_time_ms": 123.45}`
- `GET /collection-info`: Get ChromaDB collection details and sample documents
  - **Authentication**: Requires Bearer token in Authorization header
  - Returns: `{"collection_name": "string", "document_count": 123, "sample_documents": [...], "timestamp": "..."}`
- `GET /health`: Health check endpoint for monitoring service status (no auth required)
- `GET /`: Root endpoint with API information (no auth required)
- `GET /docs`: Auto-generated API documentation (auth required by default, configurable via DOCS_REQUIRE_AUTH)

## Authentication & Security

- **API Authentication**: All protected endpoints require Bearer token authentication
  - Include `Authorization: Bearer <your_token>` header in requests
  - Token configured via `API_BEARER_TOKEN` environment variable
- **ChromaDB connection**: Uses bearer token authentication for remote ChromaDB access
- **SSL enabled**: ChromaDB connection uses SSL for secure communication
- **Network security**: Server only listens on localhost (127.0.0.1) for additional security
- **Documentation security**: `/docs` endpoint requires authentication by default (set `DOCS_REQUIRE_AUTH=false` to disable)
- **Environment variables**: All required tokens and keys are validated at startup

## Metadata Handling

The API automatically handles metadata type conversion to ensure ChromaDB compatibility:

### **Supported Types** (stored as-is):
- `string`: Text values
- `int`: Integer numbers  
- `float`: Decimal numbers
- `bool`: True/False values
- `None`: Null values

### **Auto-Converted Types**:
- **Lists**: `["python", "api", "web"]` → `"python, api, web"` (comma-separated string)
- **Dictionaries**: `{"key": "value"}` → `'{"key": "value"}'` (JSON string)
- **Other types**: Converted to string representation

### **Conversion Logging**:
- Conversions are logged for debugging
- A `_metadata_conversions` field is added to track applied conversions
- Original data structure is preserved when possible