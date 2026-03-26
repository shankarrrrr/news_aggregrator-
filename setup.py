#!/usr/bin/env python3
"""
NewsNexus Setup Script
Initializes database and verifies configuration
"""

import os
import sys
from pathlib import Path

def check_python_version():
    """Check if Python version is 3.10+"""
    if sys.version_info < (3, 10):
        print("❌ Python 3.10+ required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}")
    return True

def check_env_file():
    """Check if .env file exists"""
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        print("   Copy config/.env.example to .env and configure it")
        return False
    print("✓ .env file exists")
    return True

def check_dependencies():
    """Check if required packages are installed"""
    try:
        import fastapi
        import google.generativeai
        import gtts
        print("✓ Core dependencies installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e.name}")
        print("   Run: pip install -r requirements.txt")
        return False

def init_database():
    """Initialize database"""
    try:
        from src.utils.database import get_connection, init_db
        conn = get_connection()
        init_db(conn)
        conn.close()
        print("✓ Database initialized")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

def create_directories():
    """Create required directories"""
    dirs = ['output', 'audio']
    for d in dirs:
        Path(d).mkdir(exist_ok=True)
    print("✓ Directories created")
    return True

def main():
    print("=" * 60)
    print("NewsNexus Setup")
    print("=" * 60)
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("Environment File", check_env_file),
        ("Dependencies", check_dependencies),
        ("Directories", create_directories),
        ("Database", init_database),
    ]
    
    results = []
    for name, check in checks:
        print(f"Checking {name}...")
        results.append(check())
        print()
    
    print("=" * 60)
    if all(results):
        print("✓ Setup Complete!")
        print()
        print("Next steps:")
        print("1. Start backend:  python api.py")
        print("2. Start frontend: cd dashboard && npm start")
        print("3. Access dashboard: http://localhost:3000")
    else:
        print("❌ Setup incomplete. Please fix the errors above.")
        sys.exit(1)
    print("=" * 60)

if __name__ == "__main__":
    main()
