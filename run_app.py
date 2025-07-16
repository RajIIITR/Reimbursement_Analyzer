import subprocess
import time
import threading
import sys

def run_fastapi():
    """Run FastAPI backend"""
    print("Starting FastAPI backend...")
    subprocess.run([sys.executable, "app.py"])

def run_streamlit():
    """Run Streamlit frontend"""
    print("Starting Streamlit frontend...")
    time.sleep(3)  # Wait for FastAPI to start
    subprocess.run(["streamlit", "run", "frontend.py"])

if __name__ == "__main__":
    print("🚀 Starting Invoice Analysis System...")
    
    # Start FastAPI in background
    fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
    fastapi_thread.start()
    
    # Start Streamlit in main thread
    try:
        run_streamlit()
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")