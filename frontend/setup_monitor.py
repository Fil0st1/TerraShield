#!/usr/bin/env python3
"""
Setup script for TerraShield Sensor Alert Monitor
Helps users configure the monitor quickly
"""

import os
import sys
import shutil

def create_env_file():
    """Create .env file from template if it doesn't exist"""
    if os.path.exists('.env'):
        print("✅ .env file already exists")
        return True
    
    if os.path.exists('config_template.env'):
        shutil.copy('config_template.env', '.env')
        print("✅ Created .env file from template")
        print("📝 Please edit .env file with your actual credentials")
        return True
    else:
        print("❌ config_template.env not found")
        return False

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    try:
        import subprocess
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'sensor_monitor_requirements.txt'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Dependencies installed successfully")
            return True
        else:
            print(f"❌ Failed to install dependencies: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def check_credentials():
    """Check if credentials are configured"""
    print("🔍 Checking credentials...")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_KEY", 
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.startswith('your_'):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Please configure these variables in .env: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ All credentials appear to be configured")
        return True

def main():
    """Main setup function"""
    print("🚀 TerraShield Sensor Monitor Setup")
    print("=" * 40)
    
    # Step 1: Create .env file
    print("\n1. Setting up configuration...")
    if not create_env_file():
        return 1
    
    # Step 2: Install dependencies
    print("\n2. Installing dependencies...")
    if not install_dependencies():
        return 1
    
    # Step 3: Check credentials
    print("\n3. Checking credentials...")
    credentials_ok = check_credentials()
    
    print("\n" + "=" * 40)
    if credentials_ok:
        print("🎉 Setup complete! You can now run the monitor:")
        print("   python sensor_alert_monitor.py --once")
        print("   python sensor_alert_monitor.py --continuous")
    else:
        print("⚠️  Setup incomplete. Please configure your credentials in .env file")
        print("   Then run: python test_sensor_monitor.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
