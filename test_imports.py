#!/usr/bin/env python3
"""Test imports to identify issues"""

import sys
sys.path.insert(0, 'src')

print("Testing imports...")

try:
    print("1. Importing pipeline...")
    from pcb_pipeline.pipeline import PCBPipeline
    print("   ✓ pipeline imported successfully")
except Exception as e:
    print(f"   ✗ Error importing pipeline: {e}")

try:
    print("2. Importing config...")
    from pcb_pipeline.config import PipelineConfig
    print("   ✓ config imported successfully")
except Exception as e:
    print(f"   ✗ Error importing config: {e}")

try:
    print("3. Importing fab_interface...")
    from pcb_pipeline.fab_interface import FabricationManager
    print("   ✓ fab_interface imported successfully")
except Exception as e:
    print(f"   ✗ Error importing fab_interface: {e}")

try:
    print("4. Importing web_api...")
    from pcb_pipeline.web_api import create_app
    print("   ✓ web_api imported successfully")
except Exception as e:
    print(f"   ✗ Error importing web_api: {e}")

try:
    print("5. Testing FastAPI app creation...")
    app = create_app()
    print("   ✓ FastAPI app created successfully")
except Exception as e:
    print(f"   ✗ Error creating app: {e}")

print("\nImport test complete.")