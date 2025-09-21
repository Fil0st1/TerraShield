#!/usr/bin/env python3
"""
TerraShield Complete System Startup
Runs both language selector and sensor monitor
"""

import os
import sys
import time
import threading
import subprocess
from datetime import datetime

def run_language_selector():
    """Run the language selector in a separate thread"""
    print("🌍 Starting Language Selector...")
    try:
        subprocess.run([sys.executable, "language_selector.py"], check=True)
    except Exception as e:
        print(f"❌ Language selector error: {e}")

def run_sensor_monitor():
    """Run the sensor monitor in a separate thread"""
    print("📡 Starting Sensor Monitor...")
    try:
        # Wait a bit for language selector to start
        time.sleep(5)
        subprocess.run([sys.executable, "sensor_alert_monitor.py", "--continuous", "2"], check=True)
    except Exception as e:
        print(f"❌ Sensor monitor error: {e}")

def main():
    """Main startup function"""
    print("🚀 TerraShield Complete System")
    print("=" * 50)
    print("Starting both Language Selector and Sensor Monitor...")
    print("=" * 50)
    
    # Start language selector in background thread
    language_thread = threading.Thread(target=run_language_selector, daemon=True)
    language_thread.start()
    
    # Wait a moment for language selector to initialize
    time.sleep(3)
    
    # Start sensor monitor in background thread
    monitor_thread = threading.Thread(target=run_sensor_monitor, daemon=True)
    monitor_thread.start()
    
    print("\n✅ Both services started!")
    print("📱 Send 'hi' to your WhatsApp to change language")
    print("📡 Sensor monitor is running continuously")
    print("🛑 Press Ctrl+C to stop all services")
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down TerraShield system...")
        print("✅ All services stopped")

if __name__ == "__main__":
    main()
