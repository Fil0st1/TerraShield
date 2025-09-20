#!/usr/bin/env python3
"""
Test script for TerraShield Sensor Alert Monitor
Tests the monitor without sending actual alerts
"""

import os
import sys
from dotenv import load_dotenv

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from messages import translations, format_alert

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        from sensor_alert_monitor import SensorAlertMonitor
        print("✅ SensorAlertMonitor imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import SensorAlertMonitor: {e}")
        return False
    
    try:
        print("✅ Messages module imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import messages: {e}")
        return False
    
    return True

def test_environment():
    """Test if environment variables are set"""
    print("\nTesting environment variables...")
    
    load_dotenv()
    
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_KEY", 
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file")
        return False
    else:
        print("✅ All required environment variables are set")
        return True

def test_calculations():
    """Test sensor value calculations"""
    print("\nTesting sensor calculations...")
    
    try:
        from sensor_alert_monitor import SensorAlertMonitor
        monitor = SensorAlertMonitor()
        
        # Test vibration calculation
        vibration = monitor.calculate_vibration(1, 2, 3)
        expected_vibration = (1**2 + 2**2 + 3**2)**0.5
        if abs(vibration - expected_vibration) < 0.01:
            print("✅ Vibration calculation working correctly")
        else:
            print(f"❌ Vibration calculation error: got {vibration}, expected {expected_vibration}")
            return False
        
        # Test tilt calculation
        tilt = monitor.calculate_tilt(0, 0, 1)  # Should be 0 degrees
        if abs(tilt) < 0.01:
            print("✅ Tilt calculation working correctly")
        else:
            print(f"❌ Tilt calculation error: got {tilt}, expected ~0")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing calculations: {e}")
        return False

def test_alert_logic():
    """Test alert condition logic"""
    print("\nTesting alert logic...")
    
    try:
        from sensor_alert_monitor import SensorAlertMonitor
        monitor = SensorAlertMonitor()
        
        # Test case 1: No alert (all values below threshold)
        sensor_data = {
            "moisture": 50,
            "vibration": 5,
            "tilt": 5
        }
        alert_info = monitor.check_alert_conditions(sensor_data)
        if not alert_info["should_alert"]:
            print("✅ Alert logic: Correctly no alert for low values")
        else:
            print("❌ Alert logic: Should not alert for low values")
            return False
        
        # Test case 2: Alert (2+ thresholds exceeded)
        sensor_data = {
            "moisture": 85,  # Above threshold
            "vibration": 12, # Above threshold
            "tilt": 5        # Below threshold
        }
        alert_info = monitor.check_alert_conditions(sensor_data)
        if alert_info["should_alert"] and alert_info["exceeded_count"] == 2:
            print("✅ Alert logic: Correctly triggers alert for 2+ exceeded thresholds")
        else:
            print("❌ Alert logic: Should alert for 2+ exceeded thresholds")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing alert logic: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 TerraShield Sensor Monitor Test Suite")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_environment,
        test_calculations,
        test_alert_logic
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The sensor monitor should work correctly.")
        print("\nTo run the monitor:")
        print("  python sensor_alert_monitor.py --once")
        print("  python sensor_alert_monitor.py --continuous")
    else:
        print("❌ Some tests failed. Please fix the issues before running the monitor.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
