#!/usr/bin/env python3
"""Test health endpoint locally"""

import sys
sys.path.insert(0, 'src')

from pcb_pipeline.web_api import create_app
from fastapi.testclient import TestClient

app = create_app()
client = TestClient(app)

# Test health endpoint
response = client.get("/health")
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")

# Test root endpoint
response = client.get("/api")
print(f"\nAPI Status Code: {response.status_code}")
print(f"API Response: {response.json()}")

if response.status_code == 200:
    print("\n✅ Health check working!")
else:
    print("\n❌ Health check failed!")
    sys.exit(1)