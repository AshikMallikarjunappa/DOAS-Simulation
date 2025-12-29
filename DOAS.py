import streamlit as st
import math
import time

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(
    page_title="DOAS Digital Twin",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------
# Helpers
# -----------------------------
def enthalpy(t_f, rh):
    """
    Approx psychrometric enthalpy
    t_f : dry bulb °F
    rh  : relative humidity %
    """
    t_c = (t_f - 32) * 5 / 9
    w = 0.62198 * (rh / 100)
    h = 1.006 * t_c + w * (2501 + 1.86 * t_c)
    return round(h, 2)

# -----------------------------
# Sidebar Controls
# -----------------------------
st.sidebar.title("⚙️ DOAS Controls")

oa_temp = st.sidebar.slider("Outdoor Air Temp (°F)", -10, 110, 85)
oa_rh = st.sidebar.slider("Outdoor Air RH (%)", 10, 100, 60)

supply_setpoint = st.sidebar.slider("Supply Air Temp Setpoint (°F)", 45, 70, 55)

oa_damper = st.sidebar.slider("OA Damper (%)", 0, 100, 80)
ra_damper = 100 - oa_damper

fan_speed = st.sidebar.slider("Supply Fan Speed (%)", 0, 100, 75)

cooling_valve = max(0, min(100, (oa_temp - supply_setpoint) * 4))
heating_valve = max(0, min(100, (supply_setpoint - oa_temp) * 4))

# -----------------------------
# Calculations
# -----------------------------
oa_enthalpy = enthalpy(oa_temp, oa_rh)
sa_temp = supply_setpoint + (oa_temp - supply_setpoint) * (100 - cooling_valve) / 100
sa_enthalpy = enthalpy(sa_temp, oa_rh)

# -----------------------------
# Header
# -----------------------------
st.title("🏢 DOAS Simulation Lab — Digital Twin")
st.caption("Real-Time Mechanical Flow & Control")

# -----------------------------
# Layout
# -----------------------------
diagram_col, data_col = st.columns([3, 1])

# -----------------------------
# SVG Diagram
# -----------------------------
fan_rotation = fan_speed * 3

svg = f"""
<svg width="100%" height="420" viewBox="0 0 1100 420"
     xmlns="http://www.w3.org/2000/svg">

  <style>
    .duct {{ fill:none; stroke:#aaa; stroke-width:6 }}
    .label {{ fill:#ddd; font-size:14px; font-family:Arial }}
    .coil {{ fill:#1976d2; opacity:0.7 }}
    .heat {{ fill:#d32f2f; opacity:0.7 }}
    .damper {{ fill:#666 }}
    .sensor {{ fill:#00e676 }}
  </style>

  <!-- OA Duct -->
  <line x1="20" y1="200" x2="220" y2="200" class="duct"/>
  <text x="20" y="180" class="label">OA</text>

  <!-- OA Damper -->
  <rect x="120" y="180" width="12" height="{oa_damper/2}" class="damper"/>

  <!-- Cooling Coil -->
  <rect x="260" y="160" width="80" height="80" class="coil"/>
  <text x="260" y="255" class="label">Cooling {cooling_valve:.0f}%</text>

  <!-- Heating Coil -->
  <rect x="360" y="160" width="80" height="80" class="heat"/>
  <text x="360" y="255" class="label">Heating {heating_valve:.0f}%</text>

  <!-- Supply Fan -->
  <g transform="translate(520 200)">
    <circle r="30" stroke="#ccc" stroke-width="4" fill="none"/>
    <g transform="rotate({fan_rotation})">
      <line x1="0" y1="-28" x2="0" y2="28" stroke="#ccc" stroke-width="4"/>
      <line x1="-28" y1="0" x2="28" y2="0" stroke="#ccc" stroke-width="4"/>
    </g>
  </g>
  <text x="480" y="255" class="label">Fan {fan_speed}%</text>

  <!-- Supply Duct -->
  <line x1="560" y1="200" x2="900" y2="200" class="duct"/>
  <text x="880" y="180" class="label">SA</text>

  <!-- Sensors -->
  <circle cx="300" cy="140" r="6" class="sensor"/>
  <text x="280" y="120" class="label">T/RH</text>

  <circle cx="700" cy="140" r="6" class="sensor"/>
  <text x="670" y="120" class="label">SA Temp</text>

</svg>
"""

with diagram_col:
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(180deg, #111, #1c1c1c);
            padding:20px;
            border-radius:18px;
            box-shadow: inset 0 0 0 1px #2a2a2a;
        ">
            {svg}
        </div>
        """,
        unsafe_allow_html=True
    )

# -----------------------------
# Data Panel
# -----------------------------
with data_col:
    st.subheader("📊 Live Data")

    st.metric("OA Temp (°F)", oa_temp)
    st.metric("OA RH (%)", oa_rh)
    st.metric("OA Enthalpy", f"{oa_enthalpy} kJ/kg")

    st.divider()

    st.metric("SA Temp (°F)", round(sa_temp, 1))
    st.metric("SA Enthalpy", f"{sa_enthalpy} kJ/kg")

    st.divider()

    st.metric("OA Damper", f"{oa_damper}%")
    st.metric("RA Damper", f"{ra_damper}%")

# -----------------------------
# Footer
# -----------------------------
st.caption("🧠 DOAS Digital Twin — Streamlit + SVG | HVAC Controls Demo")
