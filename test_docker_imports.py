#!/usr/bin/env python3
"""Test script to verify module imports work correctly in Docker environment"""

import sys
import os

print("=== Docker Import Test ===")
print(f"Python Path: {sys.path}")
print(f"Working Directory: {os.getcwd()}")
print(f"Directory Contents: {os.listdir('.')}")

if os.path.exists('src'):
    print(f"src/ contents: {os.listdir('src')}")
    if os.path.exists('src/pcb_pipeline'):
        print(f"src/pcb_pipeline/ contents: {os.listdir('src/pcb_pipeline')}")

print("\nTesting imports...")

try:
    # Test direct import
    print("1. Testing: from pcb_pipeline.web_api import create_app")
    from pcb_pipeline.web_api import create_app
    print("   ✓ Success!")
except ImportError as e:
    print(f"   ✗ Failed: {e}")
    
    # Try with src prefix
    try:
        print("2. Testing: from src.pcb_pipeline.web_api import create_app")
        from src.pcb_pipeline.web_api import create_app
        print("   ✓ Success!")
    except ImportError as e2:
        print(f"   ✗ Failed: {e2}")

try:
    print("3. Testing pipeline import...")
    from pcb_pipeline.pipeline import PCBPipeline
    print("   ✓ Pipeline import successful")
except ImportError as e:
    print(f"   ✗ Pipeline import failed: {e}")

print("\n=== Test Complete ===")