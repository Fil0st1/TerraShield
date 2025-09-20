# app.py
from flask import Flask, request, jsonify
from supabase import create_client
from dotenv import load_dotenv
import os
from messages import translations, format_sensor_values
from alerts import check_and_alert
from twilio.rest import Client
import math

# --- Load environment variables ---
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
FROM_WHATSAPP = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

# --- Supabase & Twilio setup ---
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
twilio_client = Client(TWILIO_SID, TWILIO_TOKEN)

app = Flask(__name__)

# ------------------ ROOT ROUTE ------------------
@app.route("/sensor-data", methods=["GET"])
def get_sensor_data():
    try:
        response = (
            supabase.table("sensor_readings")
            .select("ax, ay, az, gx, gy, gz, moisture, temperature, created_at")
            .order("created_at", desc=True)
            .limit(50)
            .execute()
        )
        print("DEBUG Supabase rows:", response.data)

        rows = response.data or []
        processed = []

        for row in rows:
            gx, gy, gz = row.get("gx", 0), row.get("gy", 0), row.get("gz", 0)

            # ✅ Always positive magnitude
            vibration = math.sqrt(gx**2 + gy**2 + gz**2)

            # ✅ Tilt angle (from accelerometer)
            ax, ay, az = row.get("ax", 0), row.get("ay", 0), row.get("az", 0)
            try:
                tilt = math.degrees(math.atan2(
                    math.sqrt(ax**2 + ay**2), az
                ))
            except Exception:
                tilt = 0

            processed.append({
                "moisture": row.get("moisture", 0),
                "vibration": round(vibration, 2),   # keep it clean
                "tilt": round(tilt, 2),
                "temperature": row.get("temperature", 0),
                "timestamp": row.get("created_at"),
            })

        return jsonify(processed)

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500



# ------------------ WHATSAPP WEBHOOK ------------------
@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    incoming_raw = request.values.get("Body", "") or ""
    incoming_msg = incoming_raw.strip().lower()
    from_number = (request.values.get("From") or "").strip()

    if not from_number:
        return jsonify({"status": "error", "message": "No sender number"}), 400

    normalized_phone = from_number.lower()

    # Check if user exists
    user_resp = supabase.table("user_prefs").select("*").eq("phone", normalized_phone).execute()
    user = user_resp.data[0] if user_resp.data else None

    # New user
    if not user:
        supabase.table("user_prefs").insert({"phone": normalized_phone, "language": None, "subscribed": True}).execute()
        try:
            twilio_client.messages.create(
                from_=FROM_WHATSAPP,
                to=from_number,
                body="Welcome! 🙏\nPlease enter your preferred language (English / Hindi / Marathi)."
            )
        except Exception as e:
            print("Twilio send error (new user):", e)
            return jsonify({"status": "error", "message": str(e)}), 500
        return jsonify({"status": "asked for language"})

    # Language selection
    if incoming_msg in ("english", "en", "hindi", "hi", "marathi", "mr"):
        if incoming_msg in ("english", "en"):
            new_lang = "english"
        elif incoming_msg in ("hindi", "hi"):
            new_lang = "hindi"
        else:
            new_lang = "marathi"

        supabase.table("user_prefs").update({"language": new_lang}).eq("phone", normalized_phone).execute()

        try:
            lang_msg = translations["language_set"].get(new_lang, translations["language_set"]["english"])
            twilio_client.messages.create(
                from_=FROM_WHATSAPP,
                to=from_number,
                body=lang_msg
            )
        except Exception as e:
            print("Twilio send error (language set):", e)
            return jsonify({"status": "error", "message": str(e)}), 500

        return jsonify({"status": "language set", "language": new_lang})

    # Sensor values request
    if "sensor values" in incoming_msg:
        latest = supabase.table("sensor_readings").select(
            "node_id, packet_no, moisture, gx, latitude, longitude, created_at"
        ).order("created_at", {"ascending": False}).limit(1).execute()

        lang = user["language"] or "english"
        if latest.data:
            msg_body = format_sensor_values(latest.data[0], lang=lang)
        else:
            msg_body = translations["no_data"].get(lang, translations["no_data"]["english"])

        try:
            twilio_client.messages.create(
                from_=FROM_WHATSAPP,
                to=from_number,
                body=msg_body
            )
        except Exception as e:
            print("Twilio send error (sensor values):", e)
            return jsonify({"status": "error", "message": str(e)}), 500

        return jsonify({"status": "sensor values sent", "language": lang})

    # Change language request
    if "change language" in incoming_msg or incoming_msg == "language":
        try:
            twilio_client.messages.create(
                from_=FROM_WHATSAPP,
                to=from_number,
                body="Please enter your preferred language (English / Hindi / Marathi)."
            )
        except Exception as e:
            print("Twilio send error (change language):", e)
            return jsonify({"status": "error", "message": str(e)}), 500
        return jsonify({"status": "asked to change language"})

    # Fallback
    try:
        twilio_client.messages.create(
            from_=FROM_WHATSAPP,
            to=from_number,
            body="I didn't understand that. Send 'sensor values' or type English / Hindi / Marathi to set your language."
        )
    except Exception as e:
        print("Twilio send error (fallback):", e)
        return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({"status": "default reply"})

# ------------------ MAIN ------------------
if __name__ == "__main__":
    app.run(debug=True)
