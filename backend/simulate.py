# simulate.py
import requests
import random
import time
from datetime import datetime

# URL of your backend endpoint
URL = "http://127.0.0.1:5000/sensor-data"

while True:
    # Generate random readings
    data = {
        "moisture": random.uniform(0, 100),
        "vibration": random.uniform(0, 10),
        "tilt": random.uniform(0, 30),
        "battery": random.uniform(70, 100),
        "latitude": 28.6139,   # fixed location
        "longitude": 77.2090,
        "timestamp": datetime.now().isoformat()
    }

    try:
        resp = requests.post(URL, json=data)
        if resp.status_code == 200:
            print("✅ Simulated data sent successfully:", data)
        else:
            print("⚠️ Error sending data:", resp.status_code, resp.text)
    except Exception as e:
        print("❌ Exception while sending data:", e)

    # Wait 30 seconds before sending next data
    time.sleep(30)
