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

The application requires these environment variables (configured in `.env`):
- `OPENAI_API_KEY`: OpenAI API key for embeddings
- `CHROMA_REMOTE_URL`: ChromaDB server URL (default: https://cdb.kobra-dataworks.de)
- `CHROMA_BEARER_TOKEN`: Authentication token for ChromaDB
- `CHROMA_COLLECTION_NAME`: Collection name in ChromaDB (default: weltzien_dms)

## Running the Application

```bash
# Install dependencies (infer from imports in main.py)
pip install fastapi uvicorn langchain openai chromadb python-dotenv

# Run the development server
uvicorn app.main:app --reload

# For production
uvicorn app.main:app --host 0.0.0.0 --port 8088
```

## API Endpoints

- `POST /upsert-text`: Embeds text using OpenAI and upserts vector into ChromaDB
  - Request body: `{"text": "string", "metadata": {}, "id": "optional_id"}`
  - Returns: `{"status": "success", "documents_upserted": 1, "ids": ["vector_id"], "processing_time_ms": 123.45}`
- `GET /health`: Health check endpoint for monitoring service status
- `GET /`: Root endpoint with API information
- `GET /docs`: Auto-generated API documentation (FastAPI)

## Authentication & Security

- ChromaDB connection uses bearer token authentication via custom `BearerAuthHeaders` class
- SSL enabled for ChromaDB connection
- Environment variables are validated at startup