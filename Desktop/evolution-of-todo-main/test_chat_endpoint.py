#!/usr/bin/env python3
"""
Test script for Phase III AI Chatbot endpoint.
Verifies OpenRouter integration and chat functionality.
"""
import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER_ID = "4"  # Replace with actual user_id from your database
TEST_TOKEN = "your-auth-token-here"  # Replace with actual token

def test_chat_endpoint():
    """Test the chat endpoint with a simple message."""
    print("Testing Phase III AI Chatbot Endpoint")
    print("=" * 50)

    # Test data
    payload = {
        "message": "Create a task to test OpenRouter integration"
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TEST_TOKEN}"
    }

    url = f"{BASE_URL}/api/{TEST_USER_ID}/chat"

    print(f"\n1. Testing endpoint: {url}")
    print(f"   Message: {payload['message']}")

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)

        print(f"\n2. Response Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("\n3. Success! ✓")
            print(f"   Conversation ID: {data.get('conversation_id')}")
            print(f"   AI Response: {data.get('response')}")
            print(f"   Tool Calls: {len(data.get('tool_calls', []))}")

            if data.get('tool_calls'):
                print("\n4. Tool Calls:")
                for tool_call in data['tool_calls']:
                    print(f"   - {tool_call}")

            return True
        else:
            print(f"\n3. Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("\n3. Error: Request timed out (>30s)")
        print("   This might indicate an issue with OpenRouter API")
        return False
    except requests.exceptions.ConnectionError:
        print("\n3. Error: Could not connect to backend")
        print("   Make sure the backend is running on port 8000")
        return False
    except Exception as e:
        print(f"\n3. Error: {str(e)}")
        return False

def test_health_check():
    """Test if backend is running."""
    print("\nTesting Backend Health")
    print("=" * 50)

    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✓ Backend is running")
            return True
        else:
            print(f"✗ Backend returned status {response.status_code}")
            return False
    except:
        print("✗ Backend is not running")
        return False

if __name__ == "__main__":
    print("\nPhase III AI Chatbot - Integration Test")
    print("=" * 50)

    # Check if backend is running
    if not test_health_check():
        print("\nPlease start the backend first:")
        print("  cd backend")
        print("  python -m uvicorn src.main:app --reload --port 8000")
        sys.exit(1)

    # Test chat endpoint
    print("\nNote: Update TEST_USER_ID and TEST_TOKEN in this script")
    print("      with actual values from your authenticated session.")
    print()

    success = test_chat_endpoint()

    if success:
        print("\n" + "=" * 50)
        print("All tests passed! ✓")
        print("=" * 50)
        sys.exit(0)
    else:
        print("\n" + "=" * 50)
        print("Tests failed. Check the errors above.")
        print("=" * 50)
        sys.exit(1)
