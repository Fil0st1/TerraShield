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

try:
    # Fetch data from backend
    response = requests.get("http://127.0.0.1:5000/sensor-data")
    data = response.json()
    df = pd.DataFrame(data)

    if 'tilt' not in df.columns:
        df['tilt'] = 0

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['time_only'] = df['timestamp'].dt.strftime('%H:%M:%S')

    # --- First Row: 3 Equal Columns ---
    col1, col2, col3 = st.columns([1, 1, 1])  # equal width

    with col1:
        with st.container():
            st.subheader("📊 Sensor Readings")
            st.dataframe(df[['moisture', 'vibration', 'tilt', 'timestamp']], use_container_width=True)

    with col2:
        with st.container():
            st.subheader("📈 Sensor Trends")
            fig = px.line(df, x='time_only', y=['moisture','vibration','tilt'])
            fig.update_layout(
                xaxis_title="Time",
                yaxis_title="Sensor Values",
                legend_title="Sensors",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

    with col3:
        with st.container():
            st.subheader("📍 Node Locations")
            # Set manual latitude & longitude for all rows
            df['latitude'] = 19.198088  # your fixed latitude
            df['longitude'] = 72.827102  # your fixed longitude
            st.map(df[['latitude','longitude']])

except Exception as e:
    st.error(f"Error fetching data: {e}")

# --- Weather + Forecast Section ---
API_KEY = "65d728ae876e82a76b4414eab00a4560"
lat, lon = 19.198088, 72.827102

col4, col5, col6 = st.columns([1, 1, 1])  # second row equal width

with col4:
    try:
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        weather_data = requests.get(weather_url).json()

        city = weather_data['name']
        temp = weather_data['main']['temp']
        desc = weather_data['weather'][0]['description'].title()
        humidity = weather_data['main']['humidity']
        wind = weather_data['wind']['speed']
        rainfall = weather_data.get('rain', {}).get('1h', 0)

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
        latest_moisture = df['moisture'].iloc[-1] if not df.empty else 0
        rainfall = weather_data.get('rain', {}).get('1h', 0) if 'weather_data' in locals() else 0

        # Decide risk level
        if rainfall > 50 and latest_moisture > 80:
            risk_level = "🚨 High Landslide Risk: Heavy Rainfall + Saturated Soil"
            bg_color = "#ffcccc"
            text_color = "#b30000"
        elif rainfall > 30 and latest_moisture > 70:
            risk_level = "⚠️ Moderate Risk: Rainfall + Moisture rising"
            bg_color = "#fff4cc"
            text_color = "#996600"
        else:
            risk_level = "✅ Low Risk: Weather conditions normal"
            bg_color = "#e6ffea"
            text_color = "#006600"

        # Unified card
        st.markdown(
            f"""
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
            """,
            unsafe_allow_html=True
        )

    except Exception as e:
        st.error(f"Risk calculation failed: {e}")



with col6:
    try:
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        forecast_data = requests.get(forecast_url).json()

        forecast_list = forecast_data.get("list", [])
        high_alert_time = None
        moderate_alert_time = None

        for entry in forecast_list:
            rainfall = entry.get("rain", {}).get("3h", 0)
            forecast_time = entry.get("dt_txt")
            if rainfall >= 50:
                high_alert_time = forecast_time
                break
            elif rainfall >= 30 and moderate_alert_time is None:
                moderate_alert_time = forecast_time

        st.subheader("🌧 Rainfall Risk Prediction")
        if high_alert_time:
            st.error(f"🚨 Heavy rainfall expected on **{high_alert_time}**")
        elif moderate_alert_time:
            st.warning(f"⚠️ Rainfall likely on **{moderate_alert_time}**")
        else:
            st.success("✅ No rainfall alerts in upcoming forecast.")
    except Exception as e:
        st.error(f"Could not load forecast data: {e}")
