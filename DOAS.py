import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import time

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(page_title="DOAS Simulator", layout="wide")

# -----------------------------
# Psychrometric Calculation
# -----------------------------
def enthalpy(T, RH):
    """
    T  : Dry Bulb Temp (°C)
    RH : Relative Humidity (%)
    Returns Enthalpy (kJ/kg)
    """
    Pw = RH / 100 * 6.112 * np.exp((17.67 * T) / (T + 243.5))
    W = 0.622 * Pw / (1013 - Pw)
    h = 1.006 * T + W * (2501 + 1.86 * T)
    return round(h, 2)

# -----------------------------
# Sidebar Inputs
# -----------------------------
st.sidebar.title("DOAS Inputs")

OA_T = st.sidebar.slider("Outdoor Air Temp (°C)", -10, 45, 30)
OA_RH = st.sidebar.slider("Outdoor Air RH (%)", 10, 100, 60)
SA_Setpoint = st.sidebar.slider("Supply Air Setpoint (°C)", 12, 22, 16)
Fan_On = st.sidebar.checkbox("Supply Fan ON", True)

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
# Enthalpy Calculation
# -----------------------------
OA_h = enthalpy(OA_T, OA_RH)
SA_h = enthalpy(SA_T, SA_RH)

# -----------------------------
# Metrics
# -----------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("OA Temp (°C)", OA_T)
c2.metric("OA Enthalpy (kJ/kg)", OA_h)
c3.metric("SA Temp (°C)", SA_T)
c4.metric("SA Enthalpy (kJ/kg)", SA_h)

# -----------------------------
# DOAS Diagram
# -----------------------------
st.subheader("DOAS Unit Visualization")

fig, ax = plt.subplots(figsize=(10, 4))
ax.set_xlim(0, 10)
ax.set_ylim(0, 4)
ax.axis("off")

# Components
ax.add_patch(plt.Rectangle((0.3, 1.5), 1.2, 1))
ax.text(0.35, 2.7, "OA Damper")

ax.add_patch(plt.Rectangle((1.9, 1.5), 1.3, 1))
ax.text(2.0, 2.7, "Filter")

ax.add_patch(plt.Rectangle((3.6, 1.5), 1.5, 1))
ax.text(3.65, 2.7, "Cooling Coil")

ax.add_patch(plt.Rectangle((5.4, 1.5), 1.5, 1))
ax.text(5.45, 2.7, "Heating Coil")

ax.add_patch(plt.Circle((7.6, 2), 0.5))
ax.text(7.4, 2.7, "Fan")

ax.add_patch(plt.Rectangle((8.6, 1.5), 1.2, 1))
ax.text(8.65, 2.7, "Supply Air")

# Airflow Arrow
if Fan_On:
    ax.arrow(0.5, 2, 8.2, 0, head_width=0.15, head_length=0.2)

# Coil Status
if Cooling_Coil:
    ax.text(3.7, 1.2, "❄ Cooling ON", color="blue")
if Heating_Coil:
    ax.text(5.5, 1.2, "🔥 Heating ON", color="red")

st.pyplot(fig)

# -----------------------------
# Animation (NO `with` usage)
# -----------------------------
st.subheader("Live Airflow Simulation")

progress = st.progress(0)
status = st.empty()

for i in range(100):
    progress.progress(i + 1)
    status.write(f"Airflow running... {i + 1}%")
    time.sleep(0.02)

status.success("Simulation Complete 🚀")
