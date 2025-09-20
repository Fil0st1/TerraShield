from messages import translations, format_sensor_values
from flask import Flask, request, jsonify
from database import engine, SessionLocal
from models import Base, SensorData, UserPref
from alerts import check_and_alert
from twilio.rest import Client
from dotenv import load_dotenv
import os


# --- Load environment variables ---
load_dotenv()

Base.metadata.create_all(engine)

app = Flask(__name__)

# --- Twilio setup from .env ---
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
FROM_WHATSAPP = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

twilio_client = Client(account_sid, auth_token)

# ------------------ ROOT ROUTE ------------------
@app.route("/", methods=["GET"])
def home():
    return "Landslide Backend is running ✅"

# ------------------ SENSOR DATA ROUTES ------------------
@app.route('/sensor-data', methods=['POST'])
def add_data():
    data = request.json
    try:
        with SessionLocal() as session:
            sensor = SensorData(
                moisture=data['moisture'],
                vibration=data['vibration'],
                tilt=data.get('tilt', 0),
                battery=data['battery'],
                latitude=data['latitude'],
                longitude=data['longitude']
            )
            session.add(sensor)
            session.commit()

        # Call alerts after saving
        check_and_alert(
            moisture=float(data.get('moisture', 0)),
            vibration=float(data.get('vibration', 0)),
            tilt=float(data.get('tilt', 0))
        )

        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/sensor-data', methods=['GET'])
def get_data():
    try:
        with SessionLocal() as session:
            sensors = session.query(SensorData).all()
            result = [{
                "moisture": s.moisture,
                "vibration": s.vibration,
                "tilt": s.tilt,
                "battery": s.battery,
                "latitude": s.latitude,
                "longitude": s.longitude,
                "timestamp": s.timestamp
            } for s in sensors]
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ------------------ WHATSAPP WEBHOOK ------------------
@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    # normalize incoming
    incoming_raw = request.values.get("Body", "") or ""
    incoming_msg = incoming_raw.strip().lower()
    from_number = (request.values.get("From") or "").strip()

    print("Webhook received - from:", repr(from_number), "body:", repr(incoming_raw))  # debug log

    if not from_number:
        return jsonify({"status": "error", "message": "No sender number"}), 400

    # use normalized phone for DB keys (keep the 'whatsapp:' prefix if present)
    normalized_phone = from_number.lower()

    with SessionLocal() as session:
        user = session.query(UserPref).filter_by(phone=normalized_phone).first()

        # If no user exists, create one and send language menu
        if not user:
            user = UserPref(phone=normalized_phone, language=None, subscribed=True)
            session.add(user)
            session.commit()

            try:
                twilio_client.messages.create(
                    from_=FROM_WHATSAPP,
                    to=from_number,
                    body="Welcome! 🙏\nPlease enter your preferred language."
                )



            except Exception as e:
                print("Twilio send error (new user prompt):", e)
                return jsonify({"status":"error","message":str(e)}), 500

            return jsonify({"status": "asked for language"})

        # If message is a language selection (accept both numeric and word)
        if incoming_msg in ("english", "en", "hindi", "hi", "marathi", "mr"):
            
            # map to canonical keys in messages.py
            if incoming_msg in ("english", "en"):
                new_lang = "english"
            elif incoming_msg in ("hindi", "hi"):
                new_lang = "hindi"
            elif incoming_msg in ("marathi", "mr"):
                new_lang = "marathi"
            else:
                new_lang = "english"


            user.language = new_lang
            session.commit()

            try:
                lang_msg = translations["language_set"].get(new_lang, translations["language_set"]["english"])
                twilio_client.messages.create(
                    from_=FROM_WHATSAPP,
                    to=from_number,
                    body=lang_msg
                )

            except Exception as e:
                print("Twilio send error (language set):", e)
                return jsonify({"status":"error","message":str(e)}), 500

            return jsonify({"status": "language set", "language": new_lang})

        # If user requested sensor values
        if "sensor values" in incoming_msg:
            s = session.query(SensorData).order_by(SensorData.timestamp.desc()).first()
            lang = user.language or "english"
            if s:
                msg_body = format_sensor_values(s, lang=lang)
            else:
                # translate "no data" too via messages.py helper
                msg_body = translations["no_data"].get(lang, translations["no_data"]["english"])

            try:
                twilio_client.messages.create(
                    from_=FROM_WHATSAPP,
                    to=from_number,
                    body=msg_body
                )

            except Exception as e:
                print("Twilio send error (sensor values):", e)
                return jsonify({"status":"error","message":str(e)}), 500

            return jsonify({"status": "sensor values sent", "language": lang})

        # If user sends "change language" or "language" menu requests
        if "change language" in incoming_msg or incoming_msg == "language":
            try:
                twilio_client.messages.create(
                    from_=FROM_WHATSAPP,
                    to=from_number,
                    body="Please enter your preferred language (English / Hindi / Marathi)."
                )


            except Exception as e:
                print("Twilio send error (change language prompt):", e)
                return jsonify({"status":"error","message":str(e)}), 500
            return jsonify({"status":"asked to change language"})

        # fallback reply
        try:
            twilio_client.messages.create(
                from_=FROM_WHATSAPP,
                to=from_number,
                body="I didn't understand that. Send 'sensor values' or type English / Hindi / Marathi to set your language."
            )



        except Exception as e:
            print("Twilio send error (fallback):", e)
            return jsonify({"status":"error","message":str(e)}), 500

        return jsonify({"status": "default reply"})



# ------------------ MAIN ------------------
if __name__ == '__main__':
    app.run(debug=True)
