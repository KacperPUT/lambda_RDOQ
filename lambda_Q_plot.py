import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
import pandas as pd

# Zakres Q od 15 do 100
Q = np.linspace(15, 100, 200)

# --- Wczytanie dopasowanych parametrów z CSV ---
fit_results = pd.read_csv("lambda_fit_results_by_qtl.csv")

# Funkcje modeli
def loglog_quad(Q, a, b, c):
    return np.exp(a * np.log(Q)**2 + b * np.log(Q) + c)

def loglog_cubic(Q, a, b, c, d):
    return np.exp(a * np.log(Q)**3 + b * np.log(Q)**2 + c * np.log(Q) + d)

channels = ["Luma", "Chroma Cb+Cr"]
qtls = ["default", "flat", "semiflat"]
colors = {"default": "blue", "flat": "green", "semiflat": "red"}
linestyles = {"default": "-", "flat": "--", "semiflat": ":"}

fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
fig.suptitle("λ(Q) dla Luma i Chroma – Q ≥ 15, wygładzone")

for i, channel in enumerate(channels):
    ax = axes[i]
    for qtl in qtls:
        row = fit_results[(fit_results["channel"] == channel) & (fit_results["qtl"] == qtl)]
        if row.empty:
            continue
        params = [float(x) for x in row.iloc[0]["params"].split(";")]
        if channel == "Luma":
            lam = loglog_quad(Q, *params)
            lam = np.clip(lam, 0, 4000)
        else:
            lam = loglog_cubic(Q, *params)
            lam = np.clip(lam, 0, 8000)
        # Wygładzanie
        if len(lam) >= 5:
            lam = savgol_filter(lam, window_length=5, polyorder=2)
        ax.plot(Q, lam, color=colors[qtl], linestyle=linestyles[qtl], linewidth=2, label=f"{qtl}")
    ax.set_ylabel("λ(Q)")
    ax.set_title(channel)
    ax.grid(True)
    ax.legend()

axes[1].set_xlabel("Q (JPEG quality)")

plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.savefig("lambda_Q_plot_two_panels.png", dpi=200)
plt.show()
