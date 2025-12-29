import streamlit as st
import numpy as np
import pandas as pd
import time
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(page_title="DOAS Digital Twin Lab", layout="wide")

# --- Custom CSS for Animation & Styling ---
st.markdown("""
<style>
    @keyframes flow {
        0% { stroke-dashoffset: 24; }
        100% { stroke-dashoffset: 0; }
    }
    .flow-line {
        stroke-dasharray: 6;
        animation: flow 0.8s linear infinite;
    }
    .stMetric {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# --- Psychrometric Engine ---
def calculate_properties(T, RH):
    """Calculates Enthalpy (kJ/kg) and Humidity Ratio (kg/kg)"""
    # Saturation vapor pressure
    Es = 6.112 * np.exp((17.67 * T) / (T + 243.5))
    Pw = (RH / 100.0) * Es
    # Humidity Ratio
    W = 0.622 * Pw / (1013.25 - Pw)
    # Enthalpy
    h = 1.006 * T + W * (2501 + 1.86 * T)
    return h, W

# --- Sidebar: Control Panel ---
st.sidebar.header("🕹️ DOAS Control Desk")
system_on = st.sidebar.toggle("System Master Start", value=True)

st.sidebar.subheader("External Conditions")
oa_t_set = st.sidebar.slider("Outdoor Temp (°C)", -5, 45, 32)
oa_rh_set = st.sidebar.slider("Outdoor Humidity (%)", 10, 100, 65)

st.sidebar.subheader("Setpoints")
sa_t_sp = st.sidebar.slider("Supply Temp Setpoint (°C)", 14, 22, 16)
airflow_cfm = st.sidebar.number_input("Airflow (CFM)", 500, 5000, 2500)

# --- Initialization of Session State for Trending ---
if 'history' not in st.session_state:
    st.session_state.history = pd.DataFrame(columns=['Time', 'OA_Temp', 'SA_Temp', 'Cooling_Load'])

# --- Main Lab Layout ---
st.title("🏢 DOAS Simulation Lab: Sequence of Operations")
st.markdown("### Real-time Mechanical Flow")

# Placeholder for the Animated SVG
diagram_placeholder = st.empty()

# Columns for Live Data
c1, c2, c3, c4 = st.columns(4)
m1 = c1.empty()
m2 = c2.empty()
m3 = c3.empty()
m4 = c4.empty()

# --- Simulation Loop ---
if system_on:
    # Run a continuous loop
    for _ in range(100):
        # 1. Add Realistic Sensor Jitter
        oa_t = oa_t_set + np.random.normal(0, 0.1)
        oa_rh = oa_rh_set + np.random.normal(0, 0.5)
        
        # 2. Physics Logic
        # Energy Recovery Wheel (ERV) - Reduces OA temp towards RA (assume 24°C)
        ra_t = 24.0
        erv_eff = 0.70
        leaving_erv_t = oa_t - (erv_eff * (oa_t - ra_t))
        
        # Cooling Coil (Latent Dehumidification)
        # In a DOAS, we typically cool to a 12°C Dewpoint to strip moisture
        dewpoint_target = 12.0
        clg_valve = max(0, min(100, (leaving_erv_t - dewpoint_target) * 10))
        leaving_clg_t = max(dewpoint_target, leaving_erv_t - (clg_valve / 10))
        
        # Reheat Coil (Sensible Heating to Setpoint)
        reheat_valve = max(0, min(100, (sa_t_sp - leaving_clg_t) * 15))
        sa_t = leaving_clg_t + (reheat_valve / 15)
        
        # 3. Component Colors (Dynamic based on Valve Position)
        clg_color = f"rgba(0, 120, 255, {clg_valve/100})" if clg_valve > 0 else "#eee"
        htg_color = f"rgba(255, 50, 0, {reheat_valve/100})" if reheat_valve > 0 else "#eee"

        # 4. Generate Animated SVG Diagram
        svg_html = f"""
        <svg viewBox="0 0 800 240" xmlns="http://www.w3.org/2000/svg" style="background-color: #ffffff; border-radius: 15px; border: 1px solid #ddd;">
            <rect x="50" y="80" width="700" height="80" fill="none" stroke="#444" stroke-width="4" />
            
            <circle cx="180" cy="120" r="45" fill="#e1f5fe" stroke="#01579b" stroke-width="3" stroke-dasharray="4" class="flow-line" />
            <text x="165" y="125" font-family="sans-serif" font-size="12" font-weight="bold">ERV</text>
            
            <rect x="350" y="85" width="30" height="70" fill="{clg_color}" stroke="#01579b" />
            <text x="335" y="75" font-family="sans-serif" font-size="10">Cooling Coil</text>
            
            <rect x="520" y="85" width="30" height="70" fill="{htg_color}" stroke="#b71c1c" />
            <text x="505" y="75" font-family="sans-serif" font-size="10">Reheat Coil</text>
            
            <circle cx="680" cy="120" r="30" fill="#cfd8dc" stroke="#37474f" />
            <path d="M 680 90 L 680 150 M 650 120 L 710 120" stroke="#37474f" stroke-width="2" />
            
            <path d="M 50 120 L 750 120" fill="none" stroke="#555" stroke-width="2" class="flow-line" />
            
            <text x="60" y="180" font-family="monospace" font-size="14" fill="#01579b">OA: {oa_t:.1f}°C</text>
            <text x="240" y="180" font-family="monospace" font-size="14" fill="#333">Pre-Clg: {leaving_erv_t:.1f}°C</text>
            <text x="630" y="180" font-family="monospace" font-size="14" fill="#b71c1c">SA: {sa_t:.1f}°C</text>
        </svg>
        """
        diagram_placeholder.write(svg_html, unsafe_allow_html=True)

        # 5. Update Metrics
        m1.metric("Cooling Command", f"{clg_valve:.1f} %")
        m2.metric("Reheat Command", f"{reheat_valve:.1f} %")
        m3.metric("Supply Air Temp", f"{sa_t:.1f} °C")
        m4.metric("ERV Efficiency", f"{erv_eff*100}%")

        # 6. Trending Data
        new_data = pd.DataFrame([[datetime.now(), oa_t, sa_t, clg_valve]], 
                                columns=['Time', 'OA_Temp', 'SA_Temp', 'Cooling_Load'])
        st.session_state.history = pd.concat([st.session_state.history, new_data]).tail(20)

        time.sleep(0.3)

else:
    st.info("System is currently in STANDBY. Toggle 'System Master Start' to begin simulation.")
    diagram_placeholder.image("https://via.placeholder.com/800x240.png?text=System+Offline+-+Waiting+for+Fan+Start")

# --- Performance Trend Chart ---
st.divider()
st.subheader("System Stability Trends")
if not st.session_state.history.empty:
    st.line_chart(st.session_state.history.set_index('Time')[['OA_Temp', 'SA_Temp']])
