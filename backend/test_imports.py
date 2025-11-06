#!/usr/bin/env python3
"""Simple test to verify imports work"""

import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

try:
    from main import app
    print("✓ Successfully imported app")
    
    from core.database import get_db, Base
    print("✓ Successfully imported database")
    
    from services.auth import get_current_user
    print("✓ Successfully imported auth service")
    
    from models import User
    print("✓ Successfully imported models")
    
    print("\n✅ All imports successful!")
    
except Exception as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)