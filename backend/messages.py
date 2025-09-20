# messages.py
translations = {
    "alert": {
        "english": "ALERT 🚨\nLandslide risk detected.\nMoisture: {moisture:.1f}\nVibration: {vibration:.1f}\nTilt: {tilt:.1f}\nPlease stay alert and avoid the area.",
        "hindi":   "चेतावनी 🚨\nभूस्खलन का खतरा पाया गया।\nनमी: {moisture:.1f}\nकंपन: {vibration:.1f}\nझुकाव: {tilt:.1f}\nकृपया सावधान रहें और उस क्षेत्र से दूर रहें।",
        "marathi": "इशारा 🚨\nमातीस्खलनाचा धोका आढळला आहे.\nओलावा: {moisture:.1f}\nकंपन: {vibration:.1f}\nझुकणं: {tilt:.1f}\nकृपया सावध रहा आणि त्या भागापासून दूर राहा."
    },
    "sensor": {
        "english": "Latest Sensor Values:\nMoisture: {moisture}\nVibration: {vibration}\nTilt: {tilt}\nBattery: {battery}\nLat: {lat}, Lon: {lon}\nTime: {time}",
        "hindi":   "ताज़ा सेंसर मान:\nनमी: {moisture}\nकंपन: {vibration}\nझुकाव: {tilt}\nबैटरी: {battery}\nLat: {lat}, Lon: {lon}\nसमय: {time}",
        "marathi": "ताजे सेन्सर वाचन:\nओलावा: {moisture}\nकंपन: {vibration}\nझुकणं: {tilt}\nबॅटरी: {battery}\nLat: {lat}, Lon: {lon}\nवेळ: {time}"
    },
    "no_data": {
        "english": "No sensor data available yet.",
        "hindi":   "अभी कोई सेंसर डेटा उपलब्ध नहीं है।",
        "marathi": "सध्या कोणताही सेन्सर डेटा उपलब्ध नाही."
    },
    "language_set": {
        "english": "✅ Language set to English. Send 'sensor values' to get readings.",
        "hindi":   "✅ भाषा हिंदी पर सेट हो गई है। 'sensor values' भेजें readings पाने के लिए।",
        "marathi": "✅ भाषा मराठीवर सेट केली आहे. 'sensor values' पाठवा readings मिळवण्यासाठी."
    }
}

def format_alert(moisture, vibration, tilt, lang="english"):
    t = translations["alert"].get(lang, translations["alert"]["english"])
    return t.format(moisture=moisture, vibration=vibration, tilt=tilt)

def format_sensor_values(s, lang="english"):
    if not s:
        return translations["no_data"].get(lang, translations["no_data"]["english"])
    t = translations["sensor"].get(lang, translations["sensor"]["english"])
    return t.format(
        moisture=s.moisture,
        vibration=s.vibration,
        tilt=s.tilt,
        battery=s.battery,
        lat=s.latitude,
        lon=s.longitude,
        time=s.timestamp
    )
