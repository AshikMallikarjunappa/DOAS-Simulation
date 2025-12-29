import streamlit as st
import numpy as np
import pandas as pd
import time
from datetime import datetime

# -------------------------------------------------
# Page Configuration
# -------------------------------------------------
st.set_page_config(page_title="DOAS Digital Twin Lab", layout="wide")

# -------------------------------------------------
# Custom CSS (Animation + Styling)
# -------------------------------------------------
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
}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# Psychrometric Functions
# -------------------------------------------------
def calculate_properties(T, RH):
    Es = 6.112 * np.exp((17.67 * T) / (T + 243.5))
    Pw = (RH / 100) * Es
    W = 0.622 * Pw / (1013.25 - Pw)
    h = 1.006 * T + W * (2501 + 1.86 * T)
    return h, W

# -------------------------------------------------
# Sidebar Controls
# -------------------------------------------------
st.sidebar.header("🕹️ DOAS Control Desk")
system_on = st.sidebar.toggle("System Master Start", value=True)

st.sidebar.subheader("Outdoor Air")
oa_t_set = st.sidebar.slider("Outdoor Temp (°C)", -5, 45, 32)
oa_rh_set = st.sidebar.slider("Outdoor Humidity (%)", 10, 100, 65)

st.sidebar.subheader("Setpoints")
sa_t_sp = st.sidebar.slider("Supply Temp Setpoint (°C)", 14, 22, 16)
airflow_cfm = st.sidebar.number_input("Airflow (CFM)", 500, 5000, 2500)

# -------------------------------------------------
# Session State (Trending)
# -------------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = pd.DataFrame(
        columns=["Time", "OA_Temp", "SA_Temp", "Cooling_Command"]
    )

# -------------------------------------------------
# Main UI
# -------------------------------------------------
st.title("🏢 DOAS Simulation Lab — Digital Twin")
st.markdown("### Real-Time Mechanical Flow & Control")

diagram_placeholder = st.empty()

c1, c2, c3, c4 = st.columns(4)
m1, m2, m3, m4 = c1.empty(), c2.empty(), c3.empty(), c4.empty()

# -------------------------------------------------
# Simulation Loop
# -------------------------------------------------
if system_on:

    for _ in range(120):

        # --- Sensor Noise ---
        oa_t = oa_t_set + np.random.normal(0, 0.15)
        oa_rh = oa_rh_set + np.random.normal(0, 0.5)

        # --- Energy Recovery Wheel ---
        ra_t = 24.0
        erv_eff = 0.70
        leaving_erv_t = oa_t - erv_eff * (oa_t - ra_t)

        # --- Cooling Coil (Dehumidification) ---
        dewpoint_target = 12.0
        clg_valve = max(0, min(100, (leaving_erv_t - dewpoint_target) * 10))
        leaving_clg_t = max(dewpoint_target, leaving_erv_t - clg_valve / 10)

        # --- Reheat Coil ---
        reheat_valve = max(0, min(100, (sa_t_sp - leaving_clg_t) * 15))
        sa_t = leaving_clg_t + reheat_valve / 15

        # --- Dynamic Colors ---
        clg_color = f"rgba(0,120,255,{clg_valve/100})" if clg_valve > 0 else "#e0e0e0"
        htg_color = f"rgba(255,60,0,{reheat_valve/100})" if reheat_valve > 0 else "#e0e0e0"

        # -------------------------------------------------
        # SVG Diagram (Rendered via Markdown)
        # -------------------------------------------------
        svg = f"""
<svg viewBox="0 0 800 240" xmlns="http://www.w3.org/2000/svg"
     style="background:#ffffff;border-radius:15px;border:1px solid #ddd;">

  <!-- Duct -->
  <rect x="50" y="80" width="700" height="80"
        fill="none" stroke="#444" stroke-width="4"/>

  <!-- ERV -->
  <circle cx="180" cy="120" r="45"
          fill="#e1f5fe" stroke="#01579b" stroke-width="3"
          stroke-dasharray="4" class="flow-line"/>
  <text x="155" y="125" font-size="12" font-weight="bold">ERV</text>

  <!-- Cooling Coil -->
  <rect x="350" y="85" width="30" height="70"
        fill="{clg_color}" stroke="#01579b"/>
  <text x="325" y="75" font-size="10">Cooling Coil</text>

  <!-- Reheat Coil -->
  <rect x="520" y="85" width="30" height="70"
        fill="{htg_color}" stroke="#b71c1c"/>
  <text x="495" y="75" font-size="10">Reheat Coil</text>

  <!-- Fan -->
  <circle cx="680" cy="120" r="30"
          fill="#cfd8dc" stroke="#37474f"/>
  <path d="M 680 90 L 680 150 M 650 120 L 710 120"
        stroke="#37474f" stroke-width="2"/>

  <!-- Airflow -->
  <path d="M 50 120 L 750 120"
        fill="none" stroke="#555" stroke-width="2"
        class="flow-line"/>

  <!-- Sensors -->
  <text x="60" y="190" font-family="monospace" font-size="14" fill="#01579b">
    OA: {oa_t:.1f}°C
  </text>
  <text x="260" y="190" font-family="monospace" font-size="14" fill="#333">
    Post-ERV: {leaving_erv_t:.1f}°C
  </text>
  <text x="610" y="190" font-family="monospace" font-size="14" fill="#b71c1c">
    SA: {sa_t:.1f}°C
  </text>

</svg>
"""
        diagram_placeholder.markdown(svg, unsafe_allow_html=True)

        # -------------------------------------------------
        # Metrics
        # -------------------------------------------------
        m1.metric("Cooling Valve", f"{clg_valve:.1f} %")
        m2.metric("Reheat Valve", f"{reheat_valve:.1f} %")
        m3.metric("Supply Air Temp", f"{sa_t:.1f} °C")
        m4.metric("ERV Effectiveness", f"{erv_eff*100:.0f} %")

        # -------------------------------------------------
        # Trending
        # -------------------------------------------------
        new_row = pd.DataFrame(
            [[datetime.now(), oa_t, sa_t, clg_valve]],
            columns=["Time", "OA_Temp", "SA_Temp", "Cooling_Command"]
        )
        st.session_state.history = (
            pd.concat([st.session_state.history, new_row])
            .tail(30)
        )

        time.sleep(0.25)

else:
    st.warning("System in STANDBY — Enable Master Start")

# -------------------------------------------------
# Trend Chart
# -------------------------------------------------
st.divider()
st.subheader("Temperature Stability Trend")

if not st.session_state.history.empty:
    st.line_chart(
        st.session_state.history.set_index("Time")[["OA_Temp", "SA_Temp"]]
    )
