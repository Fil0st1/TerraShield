#!/usr/bin/env python3
"""
TerraShield Dashboard Startup Script
Runs both Flask backend API and Streamlit frontend dashboard
"""

import os
import sys
import time
import threading
import subprocess
import webbrowser
from datetime import datetime

def run_flask_backend():
    """Run the Flask backend API in a separate thread"""
    print("🔧 Starting Flask Backend API...")
    try:
        # Change to backend directory
        backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
        os.chdir(backend_dir)
        
        # Run Flask app
        subprocess.run([sys.executable, "app.py"], check=True)
    except Exception as e:
        print(f"❌ Flask backend error: {e}")

def run_streamlit_dashboard():
    """Run the Streamlit dashboard in a separate thread"""
    print("📊 Starting Streamlit Dashboard...")
    try:
        # Wait for Flask backend to start
        time.sleep(3)
        
        # Change to frontend directory
        frontend_dir = os.path.join(os.path.dirname(__file__), 'frontend')
        os.chdir(frontend_dir)
        
        # Run Streamlit dashboard
        subprocess.run([sys.executable, "-m", "streamlit", "run", "dashboard2.py", "--server.port=8501"], check=True)
    except Exception as e:
        print(f"❌ Streamlit dashboard error: {e}")

def main():
    """Main startup function"""
    print("🚀 TerraShield Dashboard System")
    print("=" * 50)
    print("Starting Flask Backend API and Streamlit Dashboard...")
    print("=" * 50)
    
    # Start Flask backend in background thread
    flask_thread = threading.Thread(target=run_flask_backend, daemon=True)
    flask_thread.start()
    
    # Wait a moment for Flask to initialize
    time.sleep(2)
    
    # Start Streamlit dashboard in background thread
    dashboard_thread = threading.Thread(target=run_streamlit_dashboard, daemon=True)
    dashboard_thread.start()
    
    # Wait for Streamlit to start
    time.sleep(5)
    
    print("\n✅ Both services started!")
    print("🔧 Flask Backend API: http://127.0.0.1:5000")
    print("📊 Streamlit Dashboard: http://localhost:8501")
    print("📡 Sensor Data API: http://127.0.0.1:5000/sensor-data")
    print("🛑 Press Ctrl+C to stop all services")
    
    # Open dashboard in browser
    try:
        webbrowser.open("http://localhost:8501")
        print("🌐 Dashboard opened in your default browser")
    except Exception as e:
        print(f"⚠️ Could not open browser automatically: {e}")
        print("Please manually open: http://localhost:8501")
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down TerraShield Dashboard system...")
        print("✅ All services stopped")

if __name__ == "__main__":
    main()
