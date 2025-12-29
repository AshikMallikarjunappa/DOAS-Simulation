import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import time

# -----------------------------
# Psychrometric Functions
# -----------------------------
def enthalpy(T, RH):
    """
    T : Dry bulb temperature (°C)
    RH : Relative Humidity (%)
    Returns enthalpy in kJ/kg
    """
    Pw = RH / 100 * 6.112 * np.exp((17.67 * T) / (T + 243.5))
    W = 0.622 * Pw / (1013 - Pw)
    h = 1.006 * T + W * (2501 + 1.86 * T)
    return round(h, 2)

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(layout="wide")
st.title("🌬️ DOAS Unit Simulator (Fun Mode)")

st.sidebar.header("Input Conditions")

OA_T = st.sidebar.slider("Outdoor Air Temp (°C)", -10, 45, 32)
OA_RH = st.sidebar.slider("Outdoor Air RH (%)", 10, 100, 60)

SA_Setpoint = st.sidebar.slider("Supply Air Setpoint (°C)", 12, 22, 16)
Fan_Status = st.sidebar.toggle("Supply Fan", True)

# -----------------------------
# Control Logic
# -----------------------------
Cooling_Coil = OA_T > SA_Setpoint
Heating_Coil = OA_T < SA_Setpoint

if Cooling_Coil:
    SA_T = SA_Setpoint
elif Heating_Coil:
    SA_T = SA_Setpoint
else:
    SA_T = OA_T

SA_RH = max(40, OA_RH - 20)

# -----------------------------
# Enthalpy
# -----------------------------
OA_h = enthalpy(OA_T, OA_RH)
SA_h = enthalpy(SA_T, SA_RH)

# -----------------------------
# Metrics
# -----------------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("OA Temp (°C)", OA_T)
col2.metric("OA Enthalpy (kJ/kg)", OA_h)
col3.metric("SA Temp (°C)", SA_T)
col4.metric("SA Enthalpy (kJ/kg)", SA_h)

# -----------------------------
# DOAS Unit Visualization
# -----------------------------
fig, ax = plt.subplots(figsize=(10, 4))
ax.set_xlim(0, 10)
ax.set_ylim(0, 4)
ax.axis("off")

# Components
ax.add_patch(plt.Rectangle((0.2, 1.5), 1.2, 1, fill=False))
ax.text(0.25, 2.7, "OA Damper")

ax.add_patch(plt.Rectangle((1.8, 1.5), 1.5, 1, fill=False))
ax.text(1.9, 2.7, "Filter")

ax.add_patch(plt.Rectangle((3.6, 1.5), 1.5, 1, fill=False))
ax.text(3.65, 2.7, "Cooling Coil")

ax.add_patch(plt.Rectangle((5.4, 1.5), 1.5, 1, fill=False))
ax.text(5.45, 2.7, "Heating Coil")

ax.add_patch(plt.Circle((7.6, 2), 0.5, fill=False))
ax.text(7.35, 2.7, "Fan")

ax.add_patch(plt.Rectangle((8.6, 1.5), 1.2, 1, fill=False))
ax.text(8.65, 2.7, "SA")

# Airflow arrow
if Fan_Status:
    ax.arrow(0.3, 2, 8.8, 0, head_width=0.15, head_length=0.2, fc='green', ec='green')

# Coil Status
if Cooling_Coil:
    ax.text(3.7, 1.2, "❄️ Active", color="blue")
if Heating_Coil:
    ax.text(5.5, 1.2, "🔥 Active", color="red")

st.pyplot(fig)

# -----------------------------
# Animated Simulation
# -----------------------------
st.subheader("🔄 Live Simulation")

placeholder = st.empty()

for i in range(10):
    with placeholder.container():
        st.write(i)
        progress = st.progress(i * 10)
    time.sleep(0.3)

st.success("Simulation Complete 🚀")
