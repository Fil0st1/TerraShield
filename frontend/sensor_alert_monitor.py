#!/usr/bin/env python3
"""
TerraShield Sensor Alert Monitor
Fetches latest sensor values and sends WhatsApp alerts based on thresholds
"""

import os
import sys
import math
import time
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client
from twilio.rest import Client

# Add backend directory to path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from messages import translations, format_alert

class SensorAlertMonitor:
    def __init__(self):
        """Initialize the sensor alert monitor with environment variables"""
        load_dotenv()
        
        # Supabase configuration
        self.SUPABASE_URL = os.getenv("SUPABASE_URL")
        self.SUPABASE_KEY = os.getenv("SUPABASE_KEY")
        
        if not self.SUPABASE_URL or not self.SUPABASE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        
        # Twilio configuration
        self.TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
        self.TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
        self.FROM_WHATSAPP = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
        
        if not self.TWILIO_SID or not self.TWILIO_TOKEN:
            raise ValueError("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set in environment variables")
        
        # Alert thresholds
        self.MOISTURE_THRESHOLD = int(os.getenv("MOISTURE_THRESHOLD", "80"))
        self.VIBRATION_THRESHOLD = int(os.getenv("VIBRATION_THRESHOLD", "10"))
        self.TILT_THRESHOLD = int(os.getenv("TILT_THRESHOLD", "10"))
        
        # Initialize clients
        self.supabase = create_client(self.SUPABASE_URL, self.SUPABASE_KEY)
        self.twilio_client = Client(self.TWILIO_SID, self.TWILIO_TOKEN)
        
        print("✅ Sensor Alert Monitor initialized successfully")
        print(f"📊 Thresholds - Moisture: {self.MOISTURE_THRESHOLD}%, Vibration: {self.VIBRATION_THRESHOLD}g, Tilt: {self.TILT_THRESHOLD}°")
    
    def calculate_vibration(self, gx, gy, gz):
        """Calculate vibration magnitude from gyroscope data"""
        return math.sqrt(gx**2 + gy**2 + gz**2)
    
    def calculate_tilt(self, ax, ay, az):
        """Calculate tilt angle from accelerometer data"""
        try:
            tilt = math.degrees(math.atan2(math.sqrt(ax**2 + ay**2), az))
            return tilt
        except Exception:
            return 0
    
    def fetch_latest_sensor_data(self):
        """Fetch the latest sensor data from Supabase"""
        try:
            response = (
                self.supabase.table("sensor_readings")
                .select("ax, ay, az, gx, gy, gz, moisture, temperature, created_at, node_id, packet_no, latitude, longitude")
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            
            if not response.data:
                print("⚠️ No sensor data found in database")
                return None
            
            row = response.data[0]
            print(f"📡 Fetched latest sensor data from node {row.get('node_id', 'unknown')}")
            
            # Calculate derived values
            gx, gy, gz = row.get("gx", 0), row.get("gy", 0), row.get("gz", 0)
            vibration = self.calculate_vibration(gx, gy, gz)
            
            ax, ay, az = row.get("ax", 0), row.get("ay", 0), row.get("az", 0)
            tilt = self.calculate_tilt(ax, ay, az)
            
            sensor_data = {
                "moisture": row.get("moisture", 0),
                "vibration": round(vibration, 2),
                "tilt": round(tilt, 2),
                "temperature": row.get("temperature", 0),
                "node_id": row.get("node_id", "unknown"),
                "packet_no": row.get("packet_no", 0),
                "latitude": row.get("latitude", 0),
                "longitude": row.get("longitude", 0),
                "timestamp": row.get("created_at"),
                "raw_data": {
                    "ax": ax, "ay": ay, "az": az,
                    "gx": gx, "gy": gy, "gz": gz
                }
            }
            
            return sensor_data
            
        except Exception as e:
            print(f"❌ Error fetching sensor data: {e}")
            return None
    
    def check_alert_conditions(self, sensor_data):
        """Check if alert conditions are met based on sensor thresholds"""
        moisture = sensor_data["moisture"]
        vibration = sensor_data["vibration"]
        tilt = sensor_data["tilt"]
        
        # Count how many thresholds are exceeded
        exceeded_count = sum([
            moisture > self.MOISTURE_THRESHOLD,
            vibration > self.VIBRATION_THRESHOLD,
            tilt > self.TILT_THRESHOLD
        ])
        
        # Alert if 2 or more thresholds are exceeded
        should_alert = exceeded_count >= 2
        
        alert_info = {
            "should_alert": should_alert,
            "exceeded_count": exceeded_count,
            "moisture_exceeded": moisture > self.MOISTURE_THRESHOLD,
            "vibration_exceeded": vibration > self.VIBRATION_THRESHOLD,
            "tilt_exceeded": tilt > self.TILT_THRESHOLD,
            "moisture_value": moisture,
            "vibration_value": vibration,
            "tilt_value": tilt
        }
        
        return alert_info
    
    def get_subscribed_users(self):
        """Get list of subscribed users - using hardcoded number with current language"""
        # Get current language from language selector
        current_language = self.get_current_language()
        
        # Hardcoded phone number for alerts
        users = [
            {"phone": "+918767840869", "language": current_language}
        ]
        print(f"👥 Sending alerts to: {users[0]['phone']} in {current_language}")
        return users
    
    def get_current_language(self):
        """Get current language from file"""
        try:
            if os.path.exists("current_language.txt"):
                with open("current_language.txt", "r") as f:
                    language = f.read().strip()
                    if language in ["english", "hindi", "marathi"]:
                        return language
        except Exception as e:
            print(f"⚠️ Could not read language file: {e}")
        return "english"  # Default fallback
    
    def send_whatsapp_alert(self, phone, language, sensor_data, alert_info):
        """Send WhatsApp alert to a specific user"""
        try:
            # Format alert message based on language
            msg = format_alert(
                sensor_data["moisture"],
                sensor_data["vibration"],
                sensor_data["tilt"],
                language
            )
            
            # Add additional context with safe formatting
            lat = sensor_data.get('latitude', 0) or 0
            lon = sensor_data.get('longitude', 0) or 0
            node_id = sensor_data.get('node_id', 'unknown') or 'unknown'
            packet_no = sensor_data.get('packet_no', 0) or 0
            
            context_msg = f"\n\n🕐 Time: {sensor_data['timestamp']}"
            
            full_msg = msg + context_msg
            
            # Send WhatsApp message
            message = self.twilio_client.messages.create(
                from_=self.FROM_WHATSAPP,
                to=f"whatsapp:{phone}",
                body=full_msg
            )
            
            print(f"✅ WhatsApp alert sent to {phone} (SID: {message.sid})")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send WhatsApp alert to {phone}: {e}")
            return False
    
    def send_alerts(self, sensor_data, alert_info):
        """Send alerts to all subscribed users"""
        users = self.get_subscribed_users()
        
        if not users:
            print("⚠️ No subscribed users found")
            return
        
        success_count = 0
        for user in users:
            phone = user["phone"]
            language = user.get("language", "english")
            
            if self.send_whatsapp_alert(phone, language, sensor_data, alert_info):
                success_count += 1
        
        print(f"📤 Alerts sent: {success_count}/{len(users)} successful")
    
    def print_sensor_status(self, sensor_data, alert_info):
        """Print current sensor status to console"""
        print("\n" + "="*60)
        print("🌄 TERRASHIELD SENSOR STATUS")
        print("="*60)
        print(f"🕐 Timestamp: {sensor_data['timestamp']}")
        
        # Safe location formatting
        lat = sensor_data.get('latitude', 0) or 0
        lon = sensor_data.get('longitude', 0) or 0
        print(f"📍 Location: {lat:.6f}, {lon:.6f}")
        
        # Safe node info formatting
        node_id = sensor_data.get('node_id', 'unknown') or 'unknown'
        packet_no = sensor_data.get('packet_no', 0) or 0
        print(f"📡 Node ID: {node_id} (Packet #{packet_no})")
        
        print("-"*60)
        print("📊 SENSOR READINGS:")
        
        # Safe sensor value formatting
        moisture = sensor_data.get('moisture', 0) or 0
        vibration = sensor_data.get('vibration', 0) or 0
        tilt = sensor_data.get('tilt', 0) or 0
        temperature = sensor_data.get('temperature', 0) or 0
        
        print(f"  💧 Moisture: {moisture:.1f}% {'🚨' if alert_info['moisture_exceeded'] else '✅'}")
        print(f"  📳 Vibration: {vibration:.1f}g {'🚨' if alert_info['vibration_exceeded'] else '✅'}")
        print(f"  📐 Tilt: {tilt:.1f}° {'🚨' if alert_info['tilt_exceeded'] else '✅'}")
        print(f"  🌡️ Temperature: {temperature:.1f}°C")
        
        print("-"*60)
        print("🚨 ALERT STATUS:")
        if alert_info['should_alert']:
            print(f"  🚨 ALERT TRIGGERED! ({alert_info['exceeded_count']}/3 thresholds exceeded)")
            print("  📤 Sending alerts to subscribed users...")
        else:
            print("  ✅ All sensors within normal range")
        print("="*60)
    
    def run_monitoring_cycle(self):
        """Run one complete monitoring cycle"""
        print(f"\n🔄 Starting monitoring cycle at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Fetch latest sensor data
        sensor_data = self.fetch_latest_sensor_data()
        if not sensor_data:
            print("❌ No sensor data available, skipping cycle")
            return
        
        # Check alert conditions
        alert_info = self.check_alert_conditions(sensor_data)
        
        # Print status
        self.print_sensor_status(sensor_data, alert_info)
        
        # Send alerts if needed
        if alert_info['should_alert']:
            self.send_alerts(sensor_data, alert_info)
        else:
            print("✅ No alerts needed - all sensors within normal range")
    
    def run_continuous_monitoring(self, interval_seconds=60):
        """Run continuous monitoring with specified interval"""
        print(f"🚀 Starting continuous monitoring (interval: {interval_seconds}s)")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                self.run_monitoring_cycle()
                print(f"⏰ Waiting {interval_seconds} seconds until next check...")
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
        except Exception as e:
            print(f"❌ Monitoring error: {e}")

def main():
    """Main function to run the sensor alert monitor"""
    try:
        # Initialize monitor
        monitor = SensorAlertMonitor()
        
        # Check command line arguments
        if len(sys.argv) > 1:
            if sys.argv[1] == "--once":
                # Run once
                monitor.run_monitoring_cycle()
            elif sys.argv[1] == "--continuous":
                # Run continuously
                interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
                monitor.run_continuous_monitoring(interval)
            else:
                print("Usage: python sensor_alert_monitor.py [--once|--continuous] [interval_seconds]")
                sys.exit(1)
        else:
            # Default: run once
            monitor.run_monitoring_cycle()
            
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
