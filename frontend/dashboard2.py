import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
from streamlit_folium import st_folium
import folium

st_autorefresh(interval=10000, key="datarefresh")

st.set_page_config(
    page_title="TerraShield",
    page_icon="./images/title.png",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .main-header h1 {
        color: white;
        text-align: center;
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .main-header p {
        color: #e8f4fd;
        text-align: center;
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-left: 5px solid #2a5298;
        margin-bottom: 1rem;
    }
    .alert-panel {
        border-radius: 15px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border: 2px solid;
    }
    .chart-container {
        background: white;
        padding: 1rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    .stSelectbox > div > div {
        background-color: white;
        border-radius: 10px;
    }
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .chart-container {
        animation: fadeIn 0.6s ease-out;
    }
    .metric-card {
        transition: transform 0.2s ease-in-out;
    }
    .metric-card:hover {
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)


# Enhanced Header
st.markdown("""
<div class="main-header">
    <h1>🌄 TerraShield Dashboard</h1>
    <p>Real-time Landslide Monitoring & Early Warning System</p>
</div>
""", unsafe_allow_html=True)


# ------------------ SENSOR DATA ------------------
try:
    # Add cache busting to ensure fresh data
    import time
    response = requests.get(f"http://127.0.0.1:5000/sensor-data?t={int(time.time())}")
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
    # Sort by timestamp to ensure latest data is first for metrics, but chronological for charts
    df_latest = df.sort_values("timestamp", ascending=False).reset_index(drop=True)
    df_charts = df.sort_values("timestamp", ascending=True).reset_index(drop=True)
    df_latest["time_only"] = df_latest["timestamp"].dt.strftime("%H:%M:%S")
    df_charts["time_only"] = df_charts["timestamp"].dt.strftime("%H:%M:%S")
    
    # Debug: Show data info
    st.sidebar.write(f"📊 Data Points: {len(df)}")
    if not df.empty:
        st.sidebar.write(f"🕐 Latest: {df_latest['timestamp'].iloc[0] if 'timestamp' in df_latest.columns else 'N/A'}")

    # --- Main Layout: Left Panel (30%) + Map (70%) ---
    left_col, right_col = st.columns([3, 7])

    with left_col:
        # Real-time Alert Panel
        st.markdown("### 🚨 Real-Time Alerts")
        try:
            latest_moisture = df_latest["moisture"].iloc[0] if "moisture" in df_latest.columns and not df_latest.empty else 0
            latest_tilt = df_latest["tilt"].iloc[0] if "tilt" in df_latest.columns and not df_latest.empty else 0
            latest_vibration = df_latest["vibration"].iloc[0] if "vibration" in df_latest.columns and not df_latest.empty else 0
            
            # Risk assessment based on sensor data
            if latest_moisture > 80 and latest_tilt > 15:
                risk_level = "CRITICAL"
                risk_desc = "High moisture + tilt detected"
                bg_color = "#ff4757"; text_color = "#ffffff"; border_color = "#ff3742"
                icon = "🚨"
            elif latest_moisture > 70 or latest_tilt > 10:
                risk_level = "WARNING"
                risk_desc = "Elevated sensor readings"
                bg_color = "#ffa502"; text_color = "#ffffff"; border_color = "#ff9500"
                icon = "⚠️"
            elif latest_vibration > 1000:
                risk_level = "WARNING"
                risk_desc = "High vibration detected"
                bg_color = "#ffa502"; text_color = "#ffffff"; border_color = "#ff9500"
                icon = "⚠️"
            else:
                risk_level = "NORMAL"
                risk_desc = "All sensors within safe range"
                bg_color = "#2ed573"; text_color = "#ffffff"; border_color = "#26d367"
                icon = "✅"

            st.markdown(f"""
            <div class="alert-panel" style="
                background: linear-gradient(135deg, {bg_color}80 0%, {border_color}80 100%);
                border-color: {border_color};
                text-align: center;
                animation: pulse 2s infinite;
            ">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">{icon}</div>
                <h2 style="color: {text_color}; margin: 0; font-size: 1.8rem; font-weight: bold;">{risk_level}</h2>
                <p style="color: {text_color}; margin: 0.5rem 0 0 0; font-size: 1.2rem; opacity: 0.9;">{risk_desc}</p>
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Real-time alert calculation failed: {e}")

        # Prediction Alert Panel
        st.markdown("### 🔮 Prediction Alerts")
        try:
            # Get weather data for prediction
            API_KEY = "65d728ae876e82a76b4414eab00a4560"
            lat, lon = 19.198088, 72.827102
            forecast = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units=metric").json()
            forecast_list = forecast.get("list", [])
            
            high_alert = None; moderate_alert = None
            for f in forecast_list:
                rain = f.get("rain", {}).get("3h", 0)
                t = f.get("dt_txt")
                if rain >= 50: 
                    high_alert = t
                    break
                elif rain >= 30 and moderate_alert is None: 
                    moderate_alert = t

            if high_alert:
                st.markdown(f"""
                <div class="alert-panel" style="
                    background: linear-gradient(135deg, #ff475780 0%, #ff374280 100%);
                    border-color: #ff3742;
                    text-align: center;
                ">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">🚨</div>
                    <h4 style="color: white; margin: 0; font-size: 1.5rem;">Heavy rainfall expected</h4>
                    <p style="color: white; margin: 5px 0 0 0; opacity: 0.9; font-size: 1.1rem;">{high_alert}</p>
                </div>
                """, unsafe_allow_html=True)
            elif moderate_alert:
                st.markdown(f"""
                <div class="alert-panel" style="
                    background: linear-gradient(135deg, #ffa50280 0%, #ff950080 100%);
                    border-color: #ff9500;
                    text-align: center;
                ">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">⚠️</div>
                    <h4 style="color: white; margin: 0; font-size: 1.5rem;">Rainfall likely</h4>
                    <p style="color: white; margin: 5px 0 0 0; opacity: 0.9; font-size: 1.1rem;">{moderate_alert}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="alert-panel" style="
                    background: linear-gradient(135deg, #2ed57380 0%, #26d36780 100%);
                    border-color: #26d367;
                    text-align: center;
                ">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">✅</div>
                    <h4 style="color: white; margin: 0; font-size: 1.5rem;">No rainfall alerts</h4>
                    <p style="color: white; margin: 5px 0 0 0; opacity: 0.9; font-size: 1.1rem;">Next 5 days clear</p>
                </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Prediction alert calculation failed: {e}")

        # Weather Forecast Panel
        st.markdown("### 🌤 Weather Forecast")
        try:
            API_KEY = "65d728ae876e82a76b4414eab00a4560"
            lat, lon = 19.198088, 72.827102
            weather = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric").json()
            city = weather.get("name", "Unknown")
            temp = weather.get("main", {}).get("temp", "N/A")
            desc = weather.get("weather", [{}])[0].get("description", "N/A").title()
            humidity = weather.get("main", {}).get("humidity", "N/A")
            wind = weather.get("wind", {}).get("speed", "N/A")
            rainfall = weather.get("rain", {}).get("1h", 0)

            st.markdown(f"""
            <div class="metric-card" style="
                background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
                color: white;
                border-left: 5px solid #0984e3;
            ">
                <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                    <span style="font-size: 2rem; margin-right: 0.5rem;">🌤️</span>
                    <h4 style="margin: 0; color: white;">{city}</h4>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;">
                    <div><strong>🌡️ Temp:</strong> {temp}°C</div>
                    <div><strong>💧 Humidity:</strong> {humidity}%</div>
                    <div><strong>🌬️ Wind:</strong> {wind} m/s</div>
                    <div><strong>🌧️ Rain:</strong> {rainfall} mm</div>
                </div>
                <div style="margin-top: 0.5rem; font-style: italic; opacity: 0.9;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Could not load weather data: {e}")

    with right_col:
        # Key Metrics Cards
        st.markdown("### 📊 Key Metrics")
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        
        with metric_col1:
            latest_moisture = df_latest["moisture"].iloc[0] if "moisture" in df_latest.columns and not df_latest.empty else 0
            st.metric("💧 Moisture", f"{latest_moisture:.1f}%", "Normal" if latest_moisture < 50 else "High")
        
        with metric_col2:
            latest_temp = df_latest["temperature"].iloc[0] if "temperature" in df_latest.columns and not df_latest.empty else 0
            st.metric("🌡️ Temperature", f"{latest_temp:.1f}°C", "Normal")
        
        with metric_col3:
            latest_tilt = df_latest["tilt"].iloc[0] if "tilt" in df_latest.columns and not df_latest.empty else 0
            st.metric("📐 Tilt", f"{latest_tilt:.1f}°", "Normal" if latest_tilt < 10 else "High")
        
        with metric_col4:
            latest_vibration = df_latest["vibration"].iloc[0] if "vibration" in df_latest.columns and not df_latest.empty else 0
            st.metric("📳 Vibration", f"{latest_vibration:.1f}g", "Normal" if latest_vibration < 5 else "High")

        st.markdown("### 📍 Node Location")

        # Hardcoded single node coordinates
        node_lat = 19.198088
        node_lon = 72.827102

        # Create base map without default tiles
        m = folium.Map(location=[node_lat, node_lon], zoom_start=15, control_scale=True, tiles=None)

        # --- Base Layers ---
        # Street Map (OpenStreetMap)
        folium.TileLayer(
            tiles="OpenStreetMap",
            name="Street Map",
            attr="© OpenStreetMap contributors"
        ).add_to(m)

        # Satellite
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            name="Satellite",
            attr="Tiles © Esri — Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community"
        ).add_to(m)

        # Add marker with enhanced styling
        latest_moisture = df_latest["moisture"].iloc[0] if "moisture" in df_latest.columns and not df_latest.empty else 0
        latest_temp = df_latest["temperature"].iloc[0] if "temperature" in df_latest.columns and not df_latest.empty else 0
        latest_tilt = df_latest["tilt"].iloc[0] if "tilt" in df_latest.columns and not df_latest.empty else 0
        latest_vibration = df_latest["vibration"].iloc[0] if "vibration" in df_latest.columns and not df_latest.empty else 0
        
        popup_text = f"""
        <div style="font-family: Arial, sans-serif; width: 200px;">
            <h3 style="color: #2a5298; margin: 0 0 10px 0;">🌄 TerraShield Node</h3>
            <p style="margin: 5px 0;"><strong>📍 Location:</strong> {node_lat}, {node_lon}</p>
            <p style="margin: 5px 0;"><strong>💧 Moisture:</strong> {latest_moisture:.1f}%</p>
            <p style="margin: 5px 0;"><strong>🌡️ Temperature:</strong> {latest_temp:.1f}°C</p>
            <p style="margin: 5px 0;"><strong>📐 Tilt:</strong> {latest_tilt:.1f}°</p>
            <p style="margin: 5px 0;"><strong>📳 Vibration:</strong> {latest_vibration:.1f}g</p>
        </div>
        """
        folium.Marker(
            [node_lat, node_lon],
            popup=folium.Popup(popup_text, max_width=250),
            icon=folium.Icon(color="red", icon="info-sign", prefix="fa")
        ).add_to(m)

        # Layer control
        folium.LayerControl(position="topright", collapsed=False).add_to(m)

        # Render map in Streamlit with enhanced container
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st_folium(m, width="stretch", height=500)
        st.markdown('</div>', unsafe_allow_html=True)


except Exception as e:
    st.error(f"Error fetching data: {e}")

# ------------------ ENHANCED SENSOR CHARTS SECTION ------------------
st.markdown("---")
st.markdown("""
<div style="text-align: center; margin: 2rem 0;">
    <h2 style="color: #2a5298; font-size: 2rem; margin: 0;">📊 Sensor Analytics</h2>
    <p style="color: #666; font-size: 1.1rem; margin: 0.5rem 0;">Real-time sensor data visualization</p>
</div>
""", unsafe_allow_html=True)

# Create separate charts for each sensor in a single row
sensor_col1, sensor_col2, sensor_col3, sensor_col4 = st.columns([1, 1, 1, 1])

# Moisture Chart
with sensor_col1:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown("### 💧 Moisture")
    if "moisture" in df_charts.columns:
        fig_moisture = px.line(df_charts, x="time_only", y="moisture", markers=True, 
                              color_discrete_sequence=['#1f77b4'])
        fig_moisture.update_layout(
            xaxis_title="Time",
            yaxis_title="Moisture (%)",
            height=300,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(size=12)
        )
        st.plotly_chart(fig_moisture, use_container_width=True)
    else:
        st.info("No moisture data")
    st.markdown('</div>', unsafe_allow_html=True)

# Temperature Chart
with sensor_col2:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown("### 🌡️ Temperature")
    if "temperature" in df_charts.columns:
        fig_temp = px.line(df_charts, x="time_only", y="temperature", markers=True, 
                          color_discrete_sequence=['#ff7f0e'])
        fig_temp.update_layout(
            xaxis_title="Time",
            yaxis_title="Temperature (°C)",
            height=300,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(size=12)
        )
        st.plotly_chart(fig_temp, use_container_width=True)
    else:
        st.info("No temperature data")
    st.markdown('</div>', unsafe_allow_html=True)

# Tilt Chart
with sensor_col3:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown("### 📐 Tilt")
    if "tilt" in df_charts.columns:
        fig_tilt = px.line(df_charts, x="time_only", y="tilt", markers=True, 
                          color_discrete_sequence=['#2ca02c'])
        fig_tilt.update_layout(
            xaxis_title="Time",
            yaxis_title="Tilt (degrees)",
            height=300,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(size=12)
        )
        st.plotly_chart(fig_tilt, use_container_width=True)
    else:
        st.info("No tilt data")
    st.markdown('</div>', unsafe_allow_html=True)

# Vibration Chart
with sensor_col4:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown("### 📳 Vibration")
    if "vibration" in df_charts.columns:
        fig_vibration = px.line(df_charts, x="time_only", y="vibration", markers=True, 
                               color_discrete_sequence=['#d62728'])
        fig_vibration.update_layout(
            xaxis_title="Time",
            yaxis_title="Vibration (g)",
            height=300,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(size=12)
        )
        st.plotly_chart(fig_vibration, use_container_width=True)
    else:
        st.info("No vibration data")
    st.markdown('</div>', unsafe_allow_html=True)

# Enhanced Sensor Readings Table
st.markdown("---")
st.markdown("""
<div style="text-align: center; margin: 2rem 0;">
    <h2 style="color: #2a5298; font-size: 1.8rem; margin: 0;">📋 Sensor Data Table</h2>
    <p style="color: #666; font-size: 1rem; margin: 0.5rem 0;">Detailed sensor readings over time</p>
        </div>
        """, unsafe_allow_html=True)

available_cols = [c for c in ["moisture","temperature","tilt","vibration","timestamp"] if c in df_charts.columns]
if available_cols:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.dataframe(df_charts[available_cols], width="stretch", height=400)
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("No sensor data available.")
