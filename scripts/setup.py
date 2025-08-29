#!/usr/bin/env python3
"""
Setup script for MindTrade AI
Initializes the project and verifies the environment
"""

import os
import sys
import subprocess
import requests
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def check_docker():
    """Check if Docker is available"""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker detected")
            return True
    except FileNotFoundError:
        pass
    print("❌ Docker not found - please install Docker")
    return False

def check_docker_compose():
    """Check if Docker Compose is available"""
    try:
        result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Docker Compose detected")
            return True
    except FileNotFoundError:
        pass
    print("❌ Docker Compose not found - please install Docker Compose")
    return False

def create_env_file():
    """Create .env file from example if it doesn't exist"""
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if not env_file.exists() and env_example.exists():
        print("📝 Creating .env file from template...")
        with open(env_example, 'r') as f:
            content = f.read()
        with open(env_file, 'w') as f:
            f.write(content)
        print("✅ .env file created - please configure your settings")
    elif env_file.exists():
        print("✅ .env file already exists")
    else:
        print("❌ env.example not found")

def create_logs_directory():
    """Create logs directory"""
    logs_dir = Path("logs")
    if not logs_dir.exists():
        logs_dir.mkdir()
        print("✅ Created logs directory")
    else:
        print("✅ Logs directory exists")

def test_api_connection():
    """Test API connection"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is running")
            return True
    except requests.exceptions.RequestException:
        pass
    print("ℹ️  API not running - start with: docker-compose up api")
    return False

def main():
    """Main setup function"""
    print("🚀 MindTrade AI Setup")
    print("=" * 50)
    
    # Check prerequisites
    print("\n📋 Checking prerequisites...")
    python_ok = check_python_version()
    docker_ok = check_docker()
    docker_compose_ok = check_docker_compose()
    
    if not all([python_ok, docker_ok, docker_compose_ok]):
        print("\n❌ Prerequisites not met. Please install missing components.")
        return False
    
    # Create necessary files and directories
    print("\n📁 Setting up project structure...")
    create_env_file()
    create_logs_directory()
    
    # Test API if running
    print("\n🔍 Testing services...")
    test_api_connection()
    
    print("\n✅ Setup complete!")
    print("\n📖 Next steps:")
    print("1. Configure your .env file with API keys")
    print("2. Run: docker-compose up -d")
    print("3. Access dashboard at: http://localhost:8501")
    print("4. Access API docs at: http://localhost:8000/docs")
    
    return True

if __name__ == "__main__":
    main()
