import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import time

# --------------------------------------------------
# Page Setup
# --------------------------------------------------
st.set_page_config("Practical DOAS Simulator", layout="wide")
st.title("🏢 Practical DOAS Unit – Controls Simulation")

# --------------------------------------------------
# Psychrometric Enthalpy
# --------------------------------------------------
def enthalpy(T, RH):
    Pw = RH / 100 * 6.112 * np.exp((17.67 * T) / (T + 243.5))
    W = 0.622 * Pw / (1013 - Pw)
    h = 1.006 * T + W * (2501 + 1.86 * T)
    return round(h, 1)

# --------------------------------------------------
# Sidebar Inputs (Realistic)
# --------------------------------------------------
st.sidebar.header("Outdoor Air Conditions")

OA_T = st.sidebar.slider("OA Temperature (°C)", -20, 45, 32)
OA_RH = st.sidebar.slider("OA Relative Humidity (%)", 10, 100, 65)

st.sidebar.header("Setpoints")
SA_T_SP = st.sidebar.slider("Supply Air Temp SP (°C)", 12, 22, 16)
SA_CFM = st.sidebar.slider("Airflow (CFM)", 500, 5000, 2500)

st.sidebar.header("System")
Fan_Enable = st.sidebar.toggle("Supply Fan", True)

# --------------------------------------------------
# Control Logic (Practical)
# --------------------------------------------------
OA_Damper = 100  # DOAS = 100% OA
RA_Damper = 0

Preheat_Output = max(0, (SA_T_SP - OA_T) * 4)
Cooling_Output = max(0, (OA_T - SA_T_SP) * 5)
Reheat_Output = max(0, (SA_T_SP - (OA_T - Cooling_Output / 10)) * 3)

Preheat_Output = min(Preheat_Output, 100)
Cooling_Output = min(Cooling_Output, 100)
Reheat_Output = min(Reheat_Output, 100)

Fan_Speed = 100 if Fan_Enable else 0

# Supply conditions
SA_T = SA_T_SP
SA_RH = max(45, OA_RH - Cooling_Output * 0.3)

# --------------------------------------------------
# Enthalpy
# --------------------------------------------------
OA_h = enthalpy(OA_T, OA_RH)
SA_h = enthalpy(SA_T, SA_RH)

# --------------------------------------------------
# Display Sensors
# --------------------------------------------------
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("OA Temp", f"{OA_T} °C")
c2.metric("OA Enthalpy", f"{OA_h} kJ/kg")
c3.metric("SA Temp", f"{SA_T} °C")
c4.metric("SA RH", f"{SA_RH:.1f} %")
c5.metric("SA Enthalpy", f"{SA_h} kJ/kg")

# --------------------------------------------------
# DOAS Visualization (Practical Layout)
# --------------------------------------------------
st.subheader("DOAS Unit – Practical Layout")

fig, ax = plt.subplots(figsize=(14, 4))
ax.set_xlim(0, 14)
ax.set_ylim(0, 4)
ax.axis("off")

def box(x, label):
    ax.add_patch(plt.Rectangle((x, 1.3), 1.6, 1.4))
    ax.text(x + 0.8, 3, label, ha="center", fontsize=9)

# Components
box(0.5, f"OA Damper\n{OA_Damper}%")
box(2.5, "Mixing Box")
box(4.5, "Filter")
box(6.5, f"Preheat\n{Preheat_Output:.0f}%")
box(8.5, f"Cooling\n{Cooling_Output:.0f}%")
box(10.5, f"Reheat\n{Reheat_Output:.0f}%")

# Fan
ax.add_patch(plt.Circle((12.7, 2), 0.6))
ax.text(12.7, 3, f"Fan\n{Fan_Speed}%", ha="center")

# Supply
box(13.8, "Supply Air")

# Airflow
if Fan_Enable:
    ax.arrow(0.3, 2, 13.8, 0, head_width=0.15, head_length=0.25)

# Condensate
if Cooling_Output > 0:
    ax.text(8.7, 0.7, "💧 Condensate Drain", fontsize=10)

st.pyplot(fig)

# --------------------------------------------------
# Live Operation Simulation
# --------------------------------------------------
st.subheader("Live Operation")

progress = st.progress(0)
status = st.empty()

for i in range(100):
    progress.progress(i + 1)
    status.write(
        f"Fan {Fan_Speed}% | Cooling {Cooling_Output:.0f}% | Reheat {Reheat_Output:.0f}%"
    )
    time.sleep(0.02)

status.success("DOAS Operating Normally ✅")
