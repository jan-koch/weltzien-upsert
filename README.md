# Text Embedding and Vector Upsert API

A production-ready FastAPI application that embeds text using OpenAI and upserts vectors into ChromaDB.

## Quick Start

1. **Install dependencies:**
   ```bash
   ./run_server.sh install
   ```

2. **Run the server:**
   ```bash
   # Development mode (with auto-reload)
   ./run_server.sh dev
   
   # Production mode (with multiple workers)
   ./run_server.sh prod
   ```

3. **Test the API:**
   ```bash
   ./run_server.sh test
   ```

## POST Request Structure

### Basic Request
```json
{
  "text": "Your text content to embed and store"
}
```

### Advanced Request with Metadata
```json
{
  "text": "Your text content to embed and store",
  "metadata": {
    "category": "documentation",
    "source": "user_input",
    "tags": ["important", "example"]
  },
  "id": "optional-custom-id"
}
```

### Response Format
```json
{
  "status": "success",
  "documents_upserted": 1,
  "ids": ["generated-or-custom-id"],
  "processing_time_ms": 123.45
}
```

## API Endpoints

- `POST /upsert-text` - Embed and upsert text (requires authentication)
- `GET /collection-info` - Get ChromaDB collection details (requires authentication)
- `GET /health` - Health check (no auth required)
- `GET /docs` - Interactive API documentation (auth configurable)
- `GET /` - API information (no auth required)

## Environment Setup

Create a `.env` file with:
```env
OPENAI_API_KEY=your_openai_api_key_here
CHROMA_REMOTE_URL=https://your-chroma-server.com
CHROMA_BEARER_TOKEN=your_chroma_bearer_token
CHROMA_COLLECTION_NAME=your_collection_name
API_BEARER_TOKEN=your_api_bearer_token
DOCS_REQUIRE_AUTH=true
```

**Note**: `.env.local` takes precedence over `.env` for local development overrides.

## Usage Examples

Run the example script to see different request patterns:
```bash
python example_usage.py
```

Or use curl:
```bash
# Health check
curl http://localhost:8088/health

# Basic text upsert (requires authentication)
curl -X POST http://localhost:8088/upsert-text \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -d '{"text": "Sample text to embed"}'

# Text with metadata
curl -X POST http://localhost:8088/upsert-text \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -d '{
    "text": "Sample text with metadata",
    "metadata": {"category": "example"},
    "id": "custom-123"
  }'

# Get collection info
curl -X GET http://localhost:8088/collection-info \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

## Deployment Options

### Local Development
```bash
./run_server.sh help     # Show all commands
./run_server.sh install  # Install dependencies  
./run_server.sh dev      # Development server
./run_server.sh prod     # Production server
./run_server.sh test     # Test the API
```

### Docker Deployment
Use Docker Compose for containerized deployment with Cloudflare tunnel:
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```