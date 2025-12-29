import streamlit as st
import numpy as np
import pandas as pd
import time

# --- Page Config ---
st.set_page_config(page_title="Advanced DOAS Lab Simulator", layout="wide")

# --- Psychrometric Helper Functions ---
def get_properties(T, RH):
    """Returns Enthalpy (h) and Humidity Ratio (W)"""
    # Saturation vapor pressure (hPa)
    Es = 6.112 * np.exp((17.67 * T) / (T + 243.5))
    # Actual vapor pressure
    Pw = (RH / 100.0) * Es
    # Humidity Ratio (kg/kg)
    W = 0.622 * Pw / (1013.25 - Pw)
    # Enthalpy (kJ/kg)
    h = 1.006 * T + W * (2501 + 1.86 * T)
    return h, W

# --- Simulation Logic ---
def simulate_doas(oa_t, oa_rh, ra_t, ra_rh, cfm, sa_t_set, erv_eff):
    # 1. OA Entrance
    oa_h, oa_w = get_properties(oa_t, oa_rh)
    ra_h, ra_w = get_properties(ra_t, ra_rh)
    
    # 2. Energy Recovery Wheel (ERV)
    # Effectiveness equation: T_leaving = T_entering + eff * (T_exhaust - T_entering)
    precon_t = oa_t + erv_eff * (ra_t - oa_t)
    precon_h = oa_h + erv_eff * (ra_h - oa_h)
    
    # 3. Cooling Coil (Dehumidification)
    # Target: 12°C Dew Point for moisture removal
    cooling_target_t = 12.0 
    cooling_needed = max(0, precon_t - cooling_target_t)
    
    # Leaving Cooling Coil (Latent + Sensible)
    lat_t = min(precon_t, cooling_target_t)
    lat_rh = 95.0 # Saturated
    lat_h, lat_w = get_properties(lat_t, lat_rh)
    
    # 4. Reheat Coil (Sensible only)
    reheat_needed = max(0, sa_t_set - lat_t)
    sa_t = lat_t + reheat_needed
    sa_h, sa_w = get_properties(sa_t, 10) # RH will drop as we heat
    # Calculate final RH after reheat (W remains constant)
    sa_rh = (sa_w * 1013.25 / (0.622 + sa_w)) / (6.112 * np.exp((17.67 * sa_t) / (sa_t + 243.5))) * 100

    # 5. Load Calculation (kW)
    # Mass flow rate (approx)
    m_dot = (cfm * 1.2) / 2118 # kg/s
    cooling_kw = m_dot * (precon_h - lat_h)
    reheat_kw = m_dot * (sa_h - lat_h)
    
    return {
        "Precon T": round(precon_t, 1),
        "SA T": round(sa_t, 1),
        "SA RH": round(min(100, sa_rh), 1),
        "Cooling Load": round(cooling_kw, 2),
        "Reheat Load": round(reheat_kw, 2),
        "ERV Savings": round(m_dot * (oa_h - precon_h), 2)
    }

# --- UI Layout ---
st.title("🏢 Advanced DOAS Lab Simulator")
st.markdown("This simulator tracks **Enthalpy Wheel** recovery and **Latent/Sensible** cooling loads.")

with st.sidebar:
    st.header("🌍 Ambient Conditions")
    oa_t = st.slider("Outdoor Temp (°C)", -10, 45, 32)
    oa_rh = st.slider("Outdoor Humidity (%)", 10, 100, 70)
    
    st.header("🏠 Return Air (Internal)")
    ra_t = st.number_input("Return Temp (°C)", value=24)
    ra_rh = st.number_input("Return Humidity (%)", value=50)
    
    st.header("⚙️ Equipment Specs")
    sa_t_set = st.slider("Supply Air Setpoint (°C)", 13, 24, 18)
    cfm = st.number_input("Airflow Volume (CFM)", 500, 10000, 2000)
    erv_eff = st.slider("ERV Effectiveness", 0.0, 0.85, 0.70)

# --- Execute Simulation ---
res = simulate_doas(oa_t, oa_rh, ra_t, ra_rh, cfm, sa_t_set, erv_eff)

# --- Display Results ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("Supply Air Temp", f"{res['SA T']} °C")
m2.metric("Supply Humidity", f"{res['SA RH']} %")
m3.metric("Cooling Power", f"{res['Cooling Load']} kW")
m4.metric("Heating Power", f"{res['Reheat Load']} kW")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Process Flow Information")
    st.write(f"**ERV Discharge Temp:** {res['Precon T']} °C")
    st.info(f"The ERV is currently reclaiming **{res['ERV Savings']} kW** of energy from the exhaust stream.")
    
    # Progress bars for valve positions
    st.write("Cooling Valve")
    st.progress(min(1.0, res['Cooling Load'] / 50))
    st.write("Reheat Valve")
    st.progress(min(1.0, res['Reheat Load'] / 20))

with col2:
    st.subheader("Psychrometric Summary")
    chart_data = pd.DataFrame({
        "Stage": ["Outdoor", "After ERV", "After Cooling", "Supply"],
        "Temp": [oa_t, res['Precon T'], 12.0, res['SA T']]
    })
    st.line_chart(chart_data.set_index("Stage"))
