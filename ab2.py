import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import numpy as np
from scipy.optimize import newton
import plotly.graph_objects as go
import pandas as pd

@st.cache_data
def sellmeier(w, pol):
    if pol == 'z':
        return np.sqrt(np.abs(2.12725 + (1.18431 / (w**2 - 0.0514852 ) + 0.6603 / (w**2 - 100.00507 ) - 9.68956e-3) * (w**2)))
    else:
        return np.sqrt(np.abs(2.09930 + (0.922683 / (w**2 - 0.0467695 ) - 0.0138404) * (w**2)))

@st.cache_data
def temperature_dependence(w, pol):
    if pol == "z":
        return (1e-6 * (4.1010 * w**-3 - 8.9603 * w**-2 + 9.9228 * w**-1 + 9.9587) +
                1e-8 * (3.1481 * w**-3 - 9.8136 * w**-2 + 10.459 * w**-1 - 1.1882))
    else:
        return (1e-6 * (2.6486 * w**-3 - 6.0629 * w**-2 + 6.3061 * w**-1 + 6.2897) +
                1e-8 * (1.3470 * w**-3 - 3.5770 * w**-2 + 2.2244 * w**-1 - 0.14445))

def nY_T(w, T):
    return sellmeier(w, 'y') + temperature_dependence(w, 'y') * (T - 25)

def nZ_T(w, T):
    return sellmeier(w, 'z') + temperature_dependence(w, 'z') * (T - 25)

def QPM_period_original(w1, w2, w3, T):
    return 1 / (nZ_T(w3, T) / w3 - nZ_T(w2, T) / w2 - nZ_T(w1, T) / w1)

def solve_w1_for_period_newton(target_period, w3, T):
    def equation(w1):
        w2 = 1 / (1 / w3 - 1 / w1)
        return QPM_period_original(w1, w2, w3, T) - target_period

    w1_guess = 1 / (1 / w3 - 1 / 0.9)
    return newton(equation, w1_guess)

# Streamlit Interface
def run():
    st.sidebar.header("Display Settings")
    decimals = st.sidebar.slider("Decimal places:", 0, 10, 4)

    st.sidebar.header("Simulation Parameters")
    lambda_p = st.sidebar.number_input("Pump wavelength λp (µm):", 0.1, 2.0, value=0.405, format=f"%.{decimals}f", step=0.001)

    T_min = st.sidebar.number_input("Min temperature (°C):", 25.0,35.0,value=25.0, format=f"%.{decimals}f")
    T_max = st.sidebar.number_input("Max temperature (°C):", value=75.0, format=f"%.{decimals}f")
    points = st.sidebar.slider("Resolution (# points):", 10, 200, 50)

    if T_max <= T_min:
        st.sidebar.error("Max temperature must exceed min temperature.")
        return

    st.sidebar.subheader("Operating Configuration")
    T0 = st.sidebar.number_input("Operating Temperature (°C):",25.0,value=35.0, format=f"%.{decimals}f")

    # Fixed poling period
    Λ_fixed = 3.425
    st.sidebar.success(f"Fixed Poling Period: {Λ_fixed:.{decimals}f} µm")

    # Simulation
    temps = np.linspace(T_min, T_max, points)
    idlers, signals = [], []

    for T in temps:
        try:
            w1 = solve_w1_for_period_newton(Λ_fixed, lambda_p, T)
            w2 = 1 / (1 / lambda_p - 1 / w1)
            idlers.append(w1)
            signals.append(w2)
        except:
            idlers.append(np.nan)
            signals.append(np.nan)

    # Plotting
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=temps, y=signals,
        mode='lines+markers', name='Signal (λs)',
        hovertemplate=f'T=%{{x:.2f}}°C<br>λs=%{{y:.{decimals}f}} µm<extra></extra>'
    ))
    fig.add_trace(go.Scatter(
        x=temps, y=idlers,
        mode='lines+markers', name='Idler (λi)',
        hovertemplate=f'T=%{{x:.2f}}°C<br>λi=%{{y:.{decimals}f}} µm<extra></extra>'
    ))
    fig.update_layout(
        title=f'Tuning Curve: λp={lambda_p:.{decimals}f} µm, Λ={Λ_fixed:.{decimals}f} µm',
        xaxis_title='Temperature (°C)', yaxis_title='Wavelength (µm)',
        hovermode='x unified'
    )

    st.plotly_chart(fig, use_container_width=True)

# Run app
if __name__ == "__main__":
    run()
