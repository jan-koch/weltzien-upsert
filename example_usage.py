#!/usr/bin/env python3
"""
Example script showing how to interact with the Text Embedding API
"""

import requests
import json
import time
import os

# API Configuration
API_BASE_URL = "http://localhost:8088"  # Change to your server URL
UPSERT_ENDPOINT = f"{API_BASE_URL}/upsert-text"
HEALTH_ENDPOINT = f"{API_BASE_URL}/health"
COLLECTION_INFO_ENDPOINT = f"{API_BASE_URL}/collection-info"

# Authentication - Set your API token here or use environment variable
API_TOKEN = os.getenv("API_BEARER_TOKEN", "your_api_bearer_token_here")
AUTH_HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}

def check_api_health():
    """Check if the API is healthy and ready"""
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ API Health Status: {health_data['status']}")
            print(f"   Timestamp: {health_data['timestamp']}")
            print("   Services:")
            for service, status in health_data['services'].items():
                print(f"     - {service}: {status}")
            return health_data['status'] == 'healthy'
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to API: {e}")
        return False

def example_upsert_requests():
    """Show different examples of POST requests to /upsert-text"""
    
    examples = [
        {
            "name": "Basic text upsert",
            "data": {
                "text": "This is a sample document about machine learning and artificial intelligence."
            }
        },
        {
            "name": "Text with valid metadata",
            "data": {
                "text": "FastAPI is a modern, fast web framework for building APIs with Python.",
                "metadata": {
                    "category": "technology",
                    "source": "documentation",
                    "tags": "python, api, web",
                    "priority": 1,
                    "published": True
                }
            }
        },
        {
            "name": "Text with auto-converted metadata (list)",
            "data": {
                "text": "ChromaDB supports various data types but converts complex ones automatically.",
                "metadata": {
                    "category": "database",
                    "keywords": ["vector", "database", "ai"],
                    "config": {"enabled": True, "version": "1.0"}
                }
            }
        },
        {
            "name": "Text with custom ID",
            "data": {
                "text": "ChromaDB is an open-source vector database designed for AI applications.",
                "id": "custom-doc-001",
                "metadata": {
                    "category": "database",
                    "importance": "high"
                }
            }
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n📝 Example {i}: {example['name']}")
        print("Request structure:")
        print(json.dumps(example['data'], indent=2))
        
        try:
            headers = {"Content-Type": "application/json"}
            headers.update(AUTH_HEADERS)
            response = requests.post(
                UPSERT_ENDPOINT,
                json=example['data'],
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Success! Response:")
                print(json.dumps(result, indent=2))
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        
        print("-" * 50)

def get_collection_info():
    """Get collection information and sample documents"""
    print("\n📊 Collection Information")
    
    try:
        response = requests.get(
            COLLECTION_INFO_ENDPOINT,
            headers=AUTH_HEADERS,
            timeout=10
        )
        
        if response.status_code == 200:
            info = response.json()
            print("✅ Collection Info Retrieved:")
            print(f"   Collection Name: {info['collection_name']}")
            print(f"   Document Count: {info['document_count']}")
            print(f"   Timestamp: {info['timestamp']}")
            
            if info['sample_documents']:
                print("\n📄 Sample Documents:")
                for i, doc in enumerate(info['sample_documents'][:3], 1):  # Show first 3
                    print(f"   Document {i}:")
                    print(f"     ID: {doc['id']}")
                    if doc['document']:
                        print(f"     Text: {doc['document'][:100]}...")
                    if doc['metadata']:
                        print(f"     Metadata: {doc['metadata']}")
                    print()
            else:
                print("   No sample documents available")
                
        elif response.status_code == 401:
            print("❌ Authentication failed. Check your API_BEARER_TOKEN.")
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

def main():
    print("🚀 Text Embedding API - Example Usage\n")
    
    # Check API health first
    if not check_api_health():
        print("\n⚠️  API is not healthy. Make sure the server is running.")
        return
    
    print("\n" + "="*60)
    print("📋 POST REQUEST EXAMPLES")
    print("="*60)
    
    example_upsert_requests()
    
    print("\n" + "="*60)
    print("📊 COLLECTION MONITORING")
    print("="*60)
    
    get_collection_info()
    
    print("\n📚 Additional Information:")
    print(f"   - API Documentation: {API_BASE_URL}/docs")
    print(f"   - Health Check: {API_BASE_URL}/health")
    print(f"   - Collection Info: {API_BASE_URL}/collection-info")
    print(f"   - Root Info: {API_BASE_URL}/")

if __name__ == "__main__":
    main()