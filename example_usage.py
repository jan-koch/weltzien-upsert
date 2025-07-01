#!/usr/bin/env python3
"""
Example script showing how to interact with the Text Embedding API
"""

import requests
import json
import time

# API Configuration
API_BASE_URL = "http://localhost:8088"  # Change to your server URL
UPSERT_ENDPOINT = f"{API_BASE_URL}/upsert-text"
HEALTH_ENDPOINT = f"{API_BASE_URL}/health"

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
            "name": "Text with metadata",
            "data": {
                "text": "FastAPI is a modern, fast web framework for building APIs with Python.",
                "metadata": {
                    "category": "technology",
                    "source": "documentation",
                    "tags": ["python", "api", "web"]
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
            response = requests.post(
                UPSERT_ENDPOINT,
                json=example['data'],
                headers={"Content-Type": "application/json"},
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
    
    print("\n📚 Additional Information:")
    print(f"   - API Documentation: {API_BASE_URL}/docs")
    print(f"   - Health Check: {API_BASE_URL}/health")
    print(f"   - Root Info: {API_BASE_URL}/")

if __name__ == "__main__":
    main()