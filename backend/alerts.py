# alerts.py
import os
from twilio.rest import Client
from database import SessionLocal
from models import UserPref
from messages import format_alert
from dotenv import load_dotenv
from messages import translations

load_dotenv()

# load creds from env (don't hardcode)
account_sid = os.getenv("TWILIO_SID")
auth_token = os.getenv("TWILIO_TOKEN")
twilio_client = Client(account_sid, auth_token)

FROM_SMS = os.getenv("FROM_SMS")              # +1419...
FROM_WHATSAPP = os.getenv("FROM_WHATSAPP")    # whatsapp:+1415...
MOISTURE_THRESHOLD = int(os.getenv("MOISTURE_THRESHOLD", "80"))
VIBRATION_THRESHOLD = int(os.getenv("VIBRATION_THRESHOLD", "10"))
TILT_THRESHOLD = int(os.getenv("TILT_THRESHOLD", "10"))

def check_and_alert(moisture, vibration, tilt):
    exceeded_count = sum([
        moisture > MOISTURE_THRESHOLD,
        vibration > VIBRATION_THRESHOLD,
        tilt > TILT_THRESHOLD
    ])
    if exceeded_count < 2:
        return

    # craft per-language messages and send
    with SessionLocal() as session:
        users = session.query(UserPref).filter(UserPref.subscribed==True).all()
        for u in users:
            lang = u.language or "english"
            msg = format_alert(moisture, vibration, tilt, lang)

            # WhatsApp
            try:
                twilio_client.messages.create(
                    from_=FROM_WHATSAPP,
                    to=f"whatsapp:{u.phone}",
                    body=msg
                )
            except Exception as e:
                print("WhatsApp send failed for", u.phone, e)

            # SMS fallback (optional) - if you want SMS copies too
            try:
                twilio_client.messages.create(
                    body=msg,
                    from_=FROM_SMS,
                    to=u.phone
                )
            except Exception as e:
                print("SMS send failed for", u.phone, e)

    print("✅ Alerts sent to subscribed users")
