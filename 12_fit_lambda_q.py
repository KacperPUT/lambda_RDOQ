import pandas as pd
import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import os
import glob
from scipy.signal import savgol_filter

# Folder na wykresy
os.makedirs("lambda_fit_plots", exist_ok=True)

# Modele do dopasowania
def loglog_quad(Q, a, b, c):
    return np.exp(a * np.log(Q)**2 + b * np.log(Q) + c)

def loglog_cubic(Q, a, b, c, d):
    return np.exp(a * np.log(Q)**3 + b * np.log(Q)**2 + c * np.log(Q) + d)

models = {
    "Luma": loglog_quad,
    "Chroma Cb+Cr": loglog_cubic
}

results_list = []

# Wyszukaj wszystkie pliki *_agg.csv w lambda_aggregate
csv_files = glob.glob("lambda_aggregate/*_agg.csv")

for csv_file in csv_files:
    fname = os.path.basename(csv_file)
    base = fname.replace("_agg.csv", "")

    # Rozpoznawanie kanału i QTL
    if base.startswith("Luma"):
        ch_name = "Luma"
        qtl = base[len("Luma_"):] if "_" in base else "default"
    elif base.startswith("Chroma"):
        ch_name = "Chroma Cb+Cr"
        qtl = base[len("Chroma_Cb+Cr_"):] if "_" in base else "default"
    else:
        continue  # pomijamy nieznane pliki

    df = pd.read_csv(csv_file)

    if "lambda_mean" not in df.columns:
        print(f"Plik {csv_file} nie zawiera kolumny 'lambda_mean', pomijam")
        continue

    # filtrujemy Q >= 15
    mask = df["Q"] >= 15
    df = df[mask]
    Q = df["Q"].values
    lambda_mean = df["lambda_mean"].values

    if len(Q) == 0:
        continue

    # Wygładzanie Savitzky-Golay (jeśli >=5 punktów)
    if len(lambda_mean) >= 5:
        lambda_smooth = savgol_filter(lambda_mean, window_length=5, polyorder=2)
    else:
        lambda_smooth = lambda_mean

    # Przycinanie wartości λ
    if ch_name == "Luma":
        lambda_smooth = np.clip(lambda_smooth, 0, 4000)
    else:
        lambda_smooth = np.clip(lambda_smooth, 0, 8000)

    func = models[ch_name]

    # ustawienia początkowe
    if ch_name == "Luma":
        p0 = [0.0, -1.0, np.log(max(lambda_smooth[0], 1e-6))]
    else:
        p0 = [0.0, 0.0, 0.0, np.log(max(lambda_smooth[0], 1e-6))]

    try:
        popt, _ = curve_fit(func, Q, lambda_smooth, p0=p0, maxfev=200000)

        # przewidziane λ i przycięcie
        lambda_fit = func(Q, *popt)
        if ch_name == "Luma":
            lambda_fit = np.clip(lambda_fit, 0, 4000)
        else:
            lambda_fit = np.clip(lambda_fit, 0, 8000)

        # R^2
        ss_res = np.sum((lambda_smooth - lambda_fit) ** 2)
        ss_tot = np.sum((lambda_smooth - np.mean(lambda_smooth)) ** 2)
        r2 = 1 - ss_res / ss_tot

        results_list.append({
            "channel": ch_name,
            "qtl": qtl,
            "model": func.__name__,
            "params": ";".join([f"{x:.6g}" for x in popt]),
            "R2": r2
        })

        # wykres
        plt.figure()
        plt.plot(Q, lambda_mean, 'o', label="Dane (mean λ)")
        plt.plot(Q, lambda_fit, '-', label=f"{func.__name__} fit")
        plt.xlabel("Q")
        plt.ylabel("lambda_mean")
        plt.title(f"{ch_name} - {qtl} - {func.__name__}")
        plt.legend()
        plt.grid(True)
        plt.savefig(f"lambda_fit_plots/{ch_name}_{qtl}_{func.__name__}.png")
        plt.close()

        print(f"{ch_name} [{qtl}] - dopasowanie OK, R2={r2:.4f}, params={popt}")

    except Exception as e:
        print(f"{ch_name} [{qtl}] - dopasowanie nieudane: {e}")

# zapis wyników do CSV
results_df = pd.DataFrame(results_list)
results_df.to_csv("lambda_fit_results_by_qtl.csv", index=False)
print("Zapisano wyniki do lambda_fit_results_by_qtl.csv i wykresy do lambda_fit_plots/")
