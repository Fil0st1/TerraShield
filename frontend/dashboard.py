import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

st.set_page_config(
    page_title="TerraShield",
    page_icon="./images/title.png",
    layout="wide"
)

st_autorefresh(interval=60000, key="datarefresh")
st.title("🌄 Landslide Dashboard")

# ------------------ SENSOR DATA ------------------
try:
    response = requests.get("http://127.0.0.1:5000/sensor-data")
    data = response.json()

    # Ensure always a list
    if isinstance(data, dict):
        data = [data]

    df = pd.DataFrame(data)

    # Add missing columns
    if "tilt" not in df.columns:
        df["tilt"] = 0
    if "timestamp" not in df.columns:
        st.warning("⚠️ Backend did not return 'timestamp'. Using index instead.")
        df["timestamp"] = pd.date_range(end=pd.Timestamp.now(), periods=len(df))

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["time_only"] = df["timestamp"].dt.strftime("%H:%M:%S")

    # --- First Row: Sensor Table, Trends, Map ---
    col1, col2, col3 = st.columns([1,1,1])

    with col1:
        st.subheader("📊 Sensor Readings")
        available_cols = [c for c in ["moisture","temperature","tilt","vibration","timestamp"] if c in df.columns]
        if available_cols:
            st.dataframe(df[available_cols], use_container_width=True)
        else:
            st.info("No sensor data available.")

    with col2:
        st.subheader("📈 Sensor Trends")
        trend_cols = [c for c in ["moisture","temperature","tilt","vibration"] if c in df.columns]
        if trend_cols:
            fig = px.line(df, x="time_only", y=trend_cols, markers=True)
            fig.update_layout(
                xaxis_title="Time",
                yaxis_title="Sensor Values",
                legend_title="Sensors",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No numeric data to plot.")

    with col3:
        st.subheader("📍 Node Locations")
        if "latitude" in df.columns and "longitude" in df.columns:
            st.map(df[["latitude","longitude"]].dropna())
        else:
            st.info("No GPS data found.")

except Exception as e:
    st.error(f"Error fetching data: {e}")

# ------------------ WEATHER + FORECAST ------------------
API_KEY = "65d728ae876e82a76b4414eab00a4560"
lat, lon = 19.198088, 72.827102
col4, col5, col6 = st.columns([1,1,1])

with col4:
    try:
        weather = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric").json()
        city = weather.get("name", "Unknown")
        temp = weather.get("main", {}).get("temp", "N/A")
        desc = weather.get("weather", [{}])[0].get("description", "N/A").title()
        humidity = weather.get("main", {}).get("humidity", "N/A")
        wind = weather.get("wind", {}).get("speed", "N/A")
        rainfall = weather.get("rain", {}).get("1h", 0)

        st.subheader("🌤 Weather Forecast")
        st.markdown(f"""
        **Location:** {city}  
        **Temperature:** {temp} °C  
        **Condition:** {desc}  
        **Humidity:** {humidity}%  
        **Wind Speed:** {wind} m/s  
        **Rainfall (1h):** {rainfall} mm  
        """)
    except Exception as e:
        st.error(f"Could not load weather data: {e}")

with col5:
    try:
        latest_moisture = df["moisture"].iloc[-1] if "moisture" in df.columns and not df.empty else 0

        if rainfall > 50 and latest_moisture > 80:
            risk_level = "🚨 High Landslide Risk: Heavy Rainfall + Saturated Soil"
            bg_color = "#ffcccc"; text_color = "#b30000"
        elif rainfall > 30 and latest_moisture > 70:
            risk_level = "⚠️ Moderate Risk: Rainfall + Moisture rising"
            bg_color = "#fff4cc"; text_color = "#996600"
        else:
            risk_level = "✅ Low Risk: Weather conditions normal"
            bg_color = "#e6ffea"; text_color = "#006600"

        st.markdown(f"""
        <div style="
            background-color:{bg_color};
            padding:25px;
            border-radius:15px;
            box-shadow:0px 4px 12px rgba(0,0,0,0.15);
            text-align:center;
        ">
            <h2 style="color:{text_color};">Real-Time Risk Warning</h2>
            <p style="font-size:20px; color:{text_color}; font-weight:bold;">{risk_level}</p>
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Risk calculation failed: {e}")

with col6:
    try:
        forecast = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units=metric").json()
        forecast_list = forecast.get("list", [])
        high_alert = None; moderate_alert = None
        for f in forecast_list:
            rain = f.get("rain", {}).get("3h", 0)
            t = f.get("dt_txt")
            if rain >= 50: high_alert = t; break
            elif rain >= 30 and moderate_alert is None: moderate_alert = t

        st.subheader("🌧 Rainfall Risk Prediction")
        if high_alert:
            st.error(f"🚨 Heavy rainfall expected on **{high_alert}**")
        elif moderate_alert:
            st.warning(f"⚠️ Rainfall likely on **{moderate_alert}**")
        else:
            st.success("✅ No rainfall alerts in upcoming forecast.")
    except Exception as e:
        st.error(f"Could not load forecast data: {e}")
