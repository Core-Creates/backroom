#!/usr/bin/env python3
"""
Setup script for the Retail Data Query System
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required")
        return False
    print(f"✅ Python {version.major}.{version.minor} detected")
    return True

def install_basic_deps():
    """Install basic dependencies needed for the demo."""
    basic_deps = ["duckdb", "pandas"]
    
    for dep in basic_deps:
        if not run_command(f"pip install {dep}", f"Installing {dep}"):
            return False
    return True

def install_all_deps():
    """Install all dependencies from requirements.txt."""
    return run_command("pip install -r requirements.txt", "Installing all dependencies")

def setup_env_file():
    """Set up environment file."""
    env_path = Path(".env")
    env_example_path = Path(".env.example")
    
    if not env_path.exists() and env_example_path.exists():
        print("🔄 Creating .env file...")
        with open(env_example_path) as f:
            content = f.read()
        with open(env_path, 'w') as f:
            f.write(content)
        print("✅ .env file created")
        print("💡 Don't forget to add your OpenAI API key to .env file")
    elif env_path.exists():
        print("✅ .env file already exists")
    else:
        print("⚠️  .env.example not found, skipping .env creation")

def test_basic_functionality():
    """Test basic functionality."""
    print("🧪 Testing basic functionality...")
    
    try:
        # Test imports
        import duckdb
        import pandas as pd
        print("✅ Basic imports work")
        
        # Test database connection
        sys.path.insert(0, str(Path.cwd()))
        from database_manager import DatabaseManager
        
        db = DatabaseManager()
        tables = db.get_all_tables()
        print(f"✅ Database connection works - found {len(tables)} tables")
        return True
        
    except Exception as e:
        print(f"❌ Basic test failed: {e}")
        return False

def main():
    """Main setup function."""
    print("🚀 Retail Data Query System Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    print("\nChoose installation type:")
    print("1. Basic setup (for demo only - no LLM features)")
    print("2. Full setup (includes LangGraph and LLM features)")
    
    while True:
        choice = input("\nEnter choice (1 or 2): ").strip()
        if choice in ['1', '2']:
            break
        print("Please enter 1 or 2")
    
    print(f"\n{'='*50}")
    
    if choice == '1':
        print("🔧 Setting up basic installation...")
        if not install_basic_deps():
            return False
    else:
        print("🔧 Setting up full installation...")
        if not install_all_deps():
            print("⚠️  Full installation failed, trying basic installation...")
            if not install_basic_deps():
                return False
    
    # Set up environment file
    setup_env_file()
    
    # Test functionality
    if not test_basic_functionality():
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed successfully!")
    
    if choice == '1':
        print("\n🎮 You can now run:")
        print("  python simple_demo.py    # Interactive demo")
        print("  python test_system.py    # Run tests")
    else:
        print("\n🎮 You can now run:")
        print("  python main.py           # Full CLI interface")
        print("  python simple_demo.py    # Simple demo")
        print("  python test_system.py    # Run tests")
        print("  streamlit run streamlit_app.py  # Web interface")
        print("\n💡 Don't forget to add your OpenAI API key to .env file for LLM features")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)