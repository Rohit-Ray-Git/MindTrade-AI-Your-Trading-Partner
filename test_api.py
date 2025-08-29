#!/usr/bin/env python3
"""
Simple API test script
"""

import requests
import time

def test_api():
    """Test the API endpoints"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing MindTrade AI API...")
    print("=" * 40)
    
    # Test root endpoint
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Root endpoint: {data['message']} v{data['version']}")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Root endpoint error: {e}")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health endpoint: {data['status']}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Health endpoint error: {e}")
    
    # Test API status endpoint
    try:
        response = requests.get(f"{base_url}/api/v1/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API status: {data['status']}")
        else:
            print(f"❌ API status failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ API status error: {e}")

if __name__ == "__main__":
    test_api()
