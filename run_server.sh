#!/bin/bash

# Text Embedding API Server Runner
# This script helps you run the FastAPI server in different modes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Text Embedding API Server Runner${NC}"
echo "=================================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: .env file not found!${NC}"
    echo "Please create a .env file with the following variables:"
    echo "  OPENAI_API_KEY=your_openai_api_key"
    echo "  CHROMA_REMOTE_URL=https://your-chroma-server.com"
    echo "  CHROMA_BEARER_TOKEN=your_chroma_token"
    echo "  CHROMA_COLLECTION_NAME=your_collection_name"
    exit 1
fi

# Check if virtual environment should be activated
if [ -d "venv" ] || [ -d ".venv" ]; then
    if [ -z "$VIRTUAL_ENV" ]; then
        echo -e "${YELLOW}📦 Virtual environment found but not activated.${NC}"
        echo "To activate it manually, run:"
        if [ -d "venv" ]; then
            echo "  source venv/bin/activate"
        else
            echo "  source .venv/bin/activate"
        fi
        echo ""
    fi
fi

# Function to install dependencies
install_deps() {
    echo -e "${BLUE}📦 Installing dependencies...${NC}"
    pip install fastapi uvicorn langchain openai chromadb python-dotenv
    echo -e "${GREEN}✅ Dependencies installed successfully!${NC}"
}

# Function to run development server
run_dev() {
    echo -e "${BLUE}🔧 Starting development server...${NC}"
    echo "Server will be available at: http://localhost:8088"
    echo "API docs will be available at: http://localhost:8088/docs"
    echo "Press Ctrl+C to stop the server"
    echo ""
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8088
}

# Function to run production server
run_prod() {
    echo -e "${BLUE}🚀 Starting production server...${NC}"
    echo "Server will be available at: http://0.0.0.0:8088"
    echo "Press Ctrl+C to stop the server"
    echo ""
    uvicorn app.main:app --host 0.0.0.0 --port 8088 --workers 4
}

# Function to test the API
test_api() {
    echo -e "${BLUE}🧪 Testing API...${NC}"
    if command -v python3 &> /dev/null; then
        python3 example_usage.py
    else
        python example_usage.py
    fi
}

# Parse command line arguments
case "${1:-dev}" in
    "install")
        install_deps
        ;;
    "dev")
        echo -e "${GREEN}🔧 Running in development mode${NC}"
        run_dev
        ;;
    "prod")
        echo -e "${GREEN}🚀 Running in production mode${NC}"
        run_prod
        ;;
    "test")
        test_api
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  install    Install required dependencies"
        echo "  dev        Run development server (default)"
        echo "  prod       Run production server with multiple workers"
        echo "  test       Test the API with example requests"
        echo "  help       Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0           # Run development server"
        echo "  $0 dev       # Run development server"
        echo "  $0 prod      # Run production server"
        echo "  $0 install   # Install dependencies"
        echo "  $0 test      # Test the API"
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        echo "Run '$0 help' for usage information"
        exit 1
        ;;
esac