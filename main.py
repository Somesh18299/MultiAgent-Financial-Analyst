#!/usr/bin/env python3
"""
Financial Analysis AI System Launcher

This script starts both the FastAPI backend and Streamlit frontend
to create a complete financial analysis system.

Usage:
    python main.py

Requirements:
    - All dependencies installed (see requirements below)
    - GROQ_API_KEY and TAVILY_API_KEY environment variables set
"""

import os
import sys
import subprocess
import time
import threading
import signal
import webbrowser
from pathlib import Path

# Load environment variables FIRST
try:
    from dotenv import load_dotenv
    load_dotenv()  # This loads the .env file
    print("✅ Environment file loaded")
except ImportError:
    print("⚠️ python-dotenv not installed, relying on system environment variables")
except Exception as e:
    print(f"⚠️ Error loading .env file: {e}")

# Configuration
BACKEND_HOST = "localhost"
BACKEND_PORT = 8000
FRONTEND_PORT = 8501
STARTUP_DELAY = 3  # seconds to wait for backend to start

def check_requirements():
    """Check if required environment variables are set"""
    required_vars = ["GROQ_API_KEY", "TAVILY_API_KEY"]
    missing_vars = []
    
    print("🔍 Checking environment variables...")
    for var in required_vars:
        value = os.environ.get(var)
        if not value:
            missing_vars.append(var)
        else:
            # Show first few characters for confirmation
            masked_value = value[:8] + "..." if len(value) > 8 else value
            print(f"   ✅ {var}: {masked_value}")
    
    if missing_vars:
        print("\n❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        
        print("\n🔧 Troubleshooting steps:")
        print("1. Check if you have a .env file in the current directory")
        print("2. Verify the .env file contains:")
        print("   GROQ_API_KEY=your_groq_api_key_here")
        print("   TAVILY_API_KEY=your_tavily_api_key_here")
        print("3. Make sure there are no spaces around the = sign")
        print("4. Ensure the .env file is in the same directory as this script")
        
        # Check for .env file
        env_file = Path(".env")
        if env_file.exists():
            print(f"   ✅ .env file found at: {env_file.absolute()}")
            try:
                with open(env_file, 'r') as f:
                    content = f.read()
                    if "GROQ_API_KEY" in content or "TAVILY_API_KEY" in content:
                        print("   ✅ API keys found in .env file")
                        print("   ⚠️  Try running the script again, or check for typos in variable names")
                    else:
                        print("   ❌ API keys not found in .env file")
            except Exception as e:
                print(f"   ❌ Error reading .env file: {e}")
        else:
            print("   ❌ .env file not found")
            print("   💡 Create a .env file with your API keys")
        
        return False
    
    print("✅ All environment variables are set")
    return True

def check_dependencies():
    """Check if required Python packages are installed"""
    # Map package names to their import names
    package_mappings = {
        "fastapi": "fastapi",
        "uvicorn": "uvicorn",
        "streamlit": "streamlit",
        "requests": "requests",
        "langchain-groq": "langchain_groq",
        "langchain-tavily": "langchain_tavily",
        "langgraph": "langgraph",
        "python-dotenv": "dotenv",
        "pydantic": "pydantic"
    }
    
    missing_packages = []
    
    print("🔍 Checking Python packages...")
    for package_name, import_name in package_mappings.items():
        try:
            # Handle nested imports
            if "." in import_name:
                module_parts = import_name.split(".")
                module = __import__(module_parts[0])
                for part in module_parts[1:]:
                    module = getattr(module, part)
            else:
                __import__(import_name)
            print(f"   ✅ {package_name}")
        except (ImportError, AttributeError):
            missing_packages.append(package_name)
            print(f"   ❌ {package_name}")
    
    if missing_packages:
        print("\n❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nInstall missing packages with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ All dependencies are installed")
    return True

def start_backend():
    """Start the FastAPI backend server"""
    print(f"🚀 Starting backend server on http://{BACKEND_HOST}:{BACKEND_PORT}")
    
    try:
        # Start uvicorn server
        cmd = [
            sys.executable, "-m", "uvicorn",
            "backend:app",
            "--host", BACKEND_HOST,
            "--port", str(BACKEND_PORT),
            "--reload"
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        return process
        
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None

def start_frontend():
    """Start the Streamlit frontend"""
    print(f"🎨 Starting frontend on http://{BACKEND_HOST}:{FRONTEND_PORT}")
    
    try:
        # Start streamlit with browser launch disabled
        cmd = [
            sys.executable, "-m", "streamlit",
            "run", "frontend.py",
            "--server.port", str(FRONTEND_PORT),
            "--server.address", BACKEND_HOST,
            "--browser.gatherUsageStats", "false",
            "--server.headless", "true"  # Prevent Streamlit from opening browser
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        return process
        
    except Exception as e:
        print(f"❌ Failed to start frontend: {e}")
        return None

def wait_for_backend():
    """Wait for backend to be ready"""
    import requests
    
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"http://{BACKEND_HOST}:{BACKEND_PORT}/health", timeout=1)
            if response.status_code == 200:
                print("✅ Backend is ready!")
                return True
        except:
            pass
        
        time.sleep(1)
        if attempt % 5 == 0:
            print(f"⏳ Waiting for backend... ({attempt + 1}/{max_attempts})")
    
    print("❌ Backend failed to start within expected time")
    return False

def wait_for_frontend():
    """Wait for frontend to be ready"""
    import requests
    
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"http://{BACKEND_HOST}:{FRONTEND_PORT}", timeout=1)
            if response.status_code == 200:
                print("✅ Frontend is ready!")
                return True
        except:
            pass
        
        time.sleep(1)
        if attempt % 5 == 0:
            print(f"⏳ Waiting for frontend... ({attempt + 1}/{max_attempts})")
    
    print("❌ Frontend failed to start within expected time")
    return False

def open_browser():
    """Open the application in the default browser"""
    try:
        url = f"http://{BACKEND_HOST}:{FRONTEND_PORT}"
        print(f"🌐 Opening browser: {url}")
        webbrowser.open(url)
    except Exception as e:
        print(f"⚠️ Could not open browser automatically: {e}")
        print(f"Please open http://{BACKEND_HOST}:{FRONTEND_PORT} manually")

def cleanup_processes(backend_process, frontend_process):
    """Clean up processes on exit"""
    print("\n🧹 Cleaning up processes...")
    
    if backend_process and backend_process.poll() is None:
        print("Stopping backend...")
        backend_process.terminate()
        backend_process.wait()
    
    if frontend_process and frontend_process.poll() is None:
        print("Stopping frontend...")
        frontend_process.terminate()
        frontend_process.wait()
    
    print("✅ Cleanup complete")

def print_banner():
    """Print application banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                   Financial Analysis AI                      ║
║                                                              ║
║  🤖 AI-Powered Financial Analysis with Web Search           ║
║  📊 Intelligent Retry Mechanisms                            ║
║  🔍 Multi-Source Data Aggregation                           ║
║                                                              ║
║  Built with: FastAPI + LangGraph + Streamlit                ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)

def print_urls():
    """Print access URLs"""
    print("\n📡 Service URLs:")
    print(f"   Frontend (Streamlit): http://{BACKEND_HOST}:{FRONTEND_PORT}")
    print(f"   Backend API:          http://{BACKEND_HOST}:{BACKEND_PORT}")
    print(f"   API Documentation:    http://{BACKEND_HOST}:{BACKEND_PORT}/docs")

def test_env_loading():
    """Test if environment loading works properly"""
    print("\n🔬 Testing environment loading...")
    
    # Try to load environment again to be sure
    try:
        from dotenv import load_dotenv
        result = load_dotenv(override=True)  # Override existing vars
        print(f"   load_dotenv() result: {result}")
    except Exception as e:
        print(f"   Error in load_dotenv(): {e}")
    
    # Check current working directory
    print(f"   Current directory: {os.getcwd()}")
    
    # List files in current directory
    env_files = [f for f in os.listdir('.') if f.startswith('.env')]
    print(f"   Environment files found: {env_files}")
    
    # Check all environment variables starting with GROQ or TAVILY
    relevant_vars = {k: v[:10] + "..." if len(v) > 10 else v 
                    for k, v in os.environ.items() 
                    if k.startswith(('GROQ', 'TAVILY'))}
    print(f"   Relevant env vars: {relevant_vars}")

def main():
    """Main application launcher"""
    print_banner()
    
    # Test environment loading first
    test_env_loading()
    
    # Check requirements
    if not check_requirements():
        print("\n💡 If you're sure your .env file is correct, try:")
        print("1. export GROQ_API_KEY='your_key_here'")
        print("2. export TAVILY_API_KEY='your_key_here'")
        print("3. python main.py")
        sys.exit(1)
    
    if not check_dependencies():
        sys.exit(1)
    
    # Check if required files exist
    required_files = ["backend.py", "frontend.py"]
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Required files not found: {missing_files}")
        print("Make sure you're in the correct directory with all project files")
        sys.exit(1)
    
    print("✅ All requirements satisfied")
    
    backend_process = None
    frontend_process = None
    
    try:
        # Start backend
        backend_process = start_backend()
        if not backend_process:
            sys.exit(1)
        
        # Wait for backend to be ready
        if not wait_for_backend():
            cleanup_processes(backend_process, None)
            sys.exit(1)
        
        # Start frontend
        frontend_process = start_frontend()
        if not frontend_process:
            cleanup_processes(backend_process, None)
            sys.exit(1)
        
        # Wait for frontend to be ready
        if not wait_for_frontend():
            cleanup_processes(backend_process, frontend_process)
            sys.exit(1)
        
        print("✅ Both services started successfully!")
        print_urls()
        
        # Open browser only once, after both services are ready
        open_browser()
        
        print("\n🎉 Financial Analysis AI is now running!")
        print("Press Ctrl+C to stop all services")
        
        # Keep the main process running
        try:
            while True:
                # Check if processes are still running
                if backend_process.poll() is not None:
                    print("❌ Backend process stopped unexpectedly")
                    break
                if frontend_process.poll() is not None:
                    print("❌ Frontend process stopped unexpectedly")
                    break
                
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Shutdown requested by user")
        
    except Exception as e:
        print(f"❌ Error starting application: {e}")
    
    finally:
        cleanup_processes(backend_process, frontend_process)

if __name__ == "__main__":
    # Handle Ctrl+C gracefully
    def signal_handler(signum, frame):
        print("\n🛑 Interrupt received, shutting down...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    main()