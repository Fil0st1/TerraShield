from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

# insert raw packet
payload = {
    "node_id": 1,
    "packet_no": 1127,
    "ax": -2216,
    "ay": 1532,
    "az": 16244,
    "gx": -135,
    "gy": 759,
    "gz": -68,
    "temperature": 47.3,
    "soil_raw": 4095,
    "moisture": 0.0,
    "latitude": 19.202766,
    "longitude": 72.823414,
    "rssi": -41,   # optional
    "snr": 13.0    # optional
}


supabase.table("sensor_readings").insert(payload).execute()

# query processed table
data = supabase.table("sensor_readings").select("*").execute()
print(data.data)
