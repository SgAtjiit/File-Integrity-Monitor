import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app import app

def test_add_directory():
    client = app.test_client()
    
    # Test adding a valid directory
    # We'll try to add the 'server' directory itself
    test_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Attempting to add directory: {test_dir}")
    
    response = client.post('/api/directories', json={'path': test_dir})
    print(f"Response status: {response.status_code}")
    if response.status_code != 200:
        print(f"Response text: {response.text}")
    else:
        print(f"Response data: {response.get_json()}")
    
    # Verify it's in the list
    response = client.get('/api/directories')
    print(f"Current directories: {response.get_json()}")

if __name__ == "__main__":
    test_add_directory()
