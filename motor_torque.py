import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import pandas as pd

# Load experimental torque curve from CSV
try:
    df_exp = pd.read_csv("ABB_torque.csv", header=None, names=["rpm", "T/Tnominal"])
    df_exp['slip'] = (1500 - df_exp['rpm']) / 1500
    df_exp['torque_Nm'] = df_exp['T/Tnominal'] * 121
    df_exp = df_exp.sort_values(by='slip')
except Exception as e:
    print(f"Error loading experimental data: {e}")
    df_exp = None

# Constants
omega_s = 2 * np.pi * 50      # Synchronous speed (rad/s)
n_ph = 3                      # Number of phases
V1 = 400                      # Line-to-line voltage (V)
j = 1j
V1_ph = V1 / np.sqrt(3)       # Line-to-neutral voltage

# Slip range
s_positive = np.linspace(0.001, 2.0, 1000)
s_negative = np.linspace(-1.0, -0.001, 500)
s = np.concatenate((s_negative, s_positive))

# Initial values
init_R1 = 0.08
init_R2 = 0.09
init_Xm = 30.0
init_X1 = 0.12
init_X2 = 0.4

# Plot setup
fig, (ax, ax_r2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True,
                                gridspec_kw={'height_ratios': [3, 1]})

# Plot lines
plt.subplots_adjust(left=0.1, bottom=0.45, hspace=0.3)
torque_line, = ax.plot([], [], label='Torque vs. Slip')
torque_line_r2s, = ax.plot([], [], label='Torque with R2(s)', color='orange', linestyle='-.')
vline_sync = ax.axvline(0.0, color='red', linestyle='--', label='Synchronous speed (s=0)')
vline_start = ax.axvline(1.0, color='blue', linestyle='--', label='Start-up torque (s=1)')

# Prepare R2(s) curve line
r2s_line, = ax_r2.plot([], [], color='orange', label='R₂(s)')
ax_r2.set_ylabel('R₂(s) (Ω)')
ax_r2.set_xlabel('Slip (s)')
ax_r2.grid(True)
ax_r2.legend()

# Dynamic peak lines and label
peak_hline = ax.axhline(0, color='green', linestyle='--')
peak_vline = ax.axvline(0, color='green', linestyle='--')
peak_label = ax.text(0.05, 0.95, '', transform=ax.transAxes, fontsize=10,
                     verticalalignment='top', bbox=dict(facecolor='white', alpha=0.6))

# Axis formatting
ax.set_xlim(2.0, -1.0)
ax.set_ylim(-150, 500)
ax.set_xlabel('Slip (s)')
ax.set_ylabel('Torque (Nm)')
ax.set_title('Induction Motor Torque vs. Slip (Interactive)')
ax.grid(True)
ax.axhline(0, color='black', linewidth=0.5)
ax.legend()

# Slider setup
slider_axes = {
    'R1': plt.axes([0.15, 0.37, 0.7, 0.025]),
    'R2': plt.axes([0.15, 0.33, 0.7, 0.025]),
    'Xm': plt.axes([0.15, 0.29, 0.7, 0.025]),
    'X1': plt.axes([0.15, 0.25, 0.7, 0.025]),
    'X2': plt.axes([0.15, 0.21, 0.7, 0.025]),
    'n': plt.axes([0.15, 0.17, 0.7, 0.025]),
    'k': plt.axes([0.15, 0.13, 0.7, 0.025]),
}

sliders = {
    'R1': Slider(slider_axes['R1'], 'R1 (Ω)', 0.01, 0.2, valinit=init_R1, valstep=0.005),
    'R2': Slider(slider_axes['R2'], 'R2 (Ω)', 0.01, 0.2, valinit=init_R2, valstep=0.005),
    'Xm': Slider(slider_axes['Xm'], 'Xm (Ω)', 5.0, 100.0, valinit=init_Xm, valstep=1.0),
    'X1': Slider(slider_axes['X1'], 'X1 (Ω)', 0.01, 1.0, valinit=init_X1, valstep=0.01),
    'X2': Slider(slider_axes['X2'], 'X2 (Ω)', 0.01, 1.0, valinit=init_X2, valstep=0.01),
    'n': Slider(slider_axes['n'], 'n (shape)', 0.5, 5.0, valinit=2.9, valstep=0.1),
    'k': Slider(slider_axes['k'], 'k (center)', 0.001, 2.0, valinit=1.42, valstep=0.01),
}

# Update function
def update(val):
    R1 = sliders['R1'].val
    R2_low = sliders['R2'].val
    Xm = sliders['Xm'].val
    X1 = sliders['X1'].val
    X2 = sliders['X2'].val
    n = sliders['n'].val
    k = sliders['k'].val

    # Thevenin equivalents
    V1_eq = V1_ph * (j * Xm) / (R1 + j * (X1 + Xm))
    Z1_eq = (j * Xm * (R1 + j * X1)) / (R1 + j * (X1 + Xm))
    R1_eq = np.real(Z1_eq)
    X1_eq = np.imag(Z1_eq)

    # --- Curve 1: Constant R2 ---
    numerator = n_ph * abs(V1_eq)**2 * (R2_low / s)
    denominator = (R1_eq + R2_low / s)**2 + (X1_eq + X2)**2
    T = (1 / omega_s) * (numerator / denominator)
    torque_line.set_data(s, T)

    # Peak markers for constant R2
    peak_idx = np.argmax(T)
    peak_s = s[peak_idx]
    peak_T = T[peak_idx]
    peak_vline.set_xdata([peak_s, peak_s])
    peak_hline.set_ydata([peak_T, peak_T])
    peak_label.set_text(f"Peak Torque ≈ {peak_T:.1f} Nm\nat Slip ≈ {peak_s:.3f}")

    # --- Curve 2: Variable R2(s) ---
    R2_high = 5 * R2_low  # or another multiplier
    R2_s = R2_low + (R2_high - R2_low) * (s**n / (s**n + k))
    numerator2 = n_ph * abs(V1_eq)**2 * (R2_s / s)
    denominator2 = (R1_eq + R2_s / s)**2 + (X1_eq + X2)**2
    T_r2s = (1 / omega_s) * (numerator2 / denominator2)
    torque_line_r2s.set_data(s, T_r2s)

    # Update R2(s) curve
    r2s_line.set_data(s, R2_s)
    ax_r2.relim()
    ax_r2.autoscale_view()

    fig.canvas.draw_idle()


# Connect sliders
for slider in sliders.values():
    slider.on_changed(update)

# Initial draw
# Plot experimental curve (once)
if df_exp is not None:
    ax.plot(df_exp['slip'], df_exp['torque_Nm'],
            color='purple', linewidth=2, linestyle='--',
            label='Experimental (ABB Datasheet)')
    ax.legend()
update(None)
plt.show()
