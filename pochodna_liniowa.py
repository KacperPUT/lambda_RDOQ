# plik: fit_and_derivative.py
import sqlite3
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import pearsonr
import os
import csv

# ---- konfiguracja ----
db_path = r"C:\Users\ITM\Desktop\database\jpegRD.db"

sequence_names = [
    'BasketballDrive_1920x1080_50',
    'blue_sky_1920x1080',
    'BQTerrace_1920x1080_60',
    'Cactus_1920x1080_50',
    'Kimono1_1920x1080_24',
    'ParkScene_1920x1080_24',
    'pedestrian_area_1920x1080',
    'riverbed_1920x1080',
    'rush_hour_1920x1080',
    'station2_1920x1080',
    'sunflower_1920x1080',
    'tennis_1920x1080_24',
    'toys_and_calendar_1920x1080',
    'tractor_1920x1080',
    'vintage_car_1920x1080',
    'walking_couple_1920x1080'
]

# zakres Q do analizy
Q_MIN = 4
Q_MAX = 100

os.makedirs("plots/RD/Luma", exist_ok=True)
os.makedirs("plots/RD/Chroma", exist_ok=True)
os.makedirs("plots/Lambda/Luma", exist_ok=True)
os.makedirs("plots/Lambda/Chroma", exist_ok=True)

# ---- modele (znormalizowane) ----
def single_power_norm(R_norm, a, b):
    R_norm = np.maximum(R_norm, 1e-12)
    return a * R_norm**b

def double_power_norm(R_norm, a1, b1, a2, b2):
    R_norm = np.maximum(R_norm, 1e-12)
    return a1 * R_norm**b1 + a2 * R_norm**b2

# ---- przekształcenia do skali oryginalnej ----
def norm_to_raw_single(a_norm, b, D_max, R_max):
    a_raw = a_norm * D_max * (R_max ** (-b))
    return a_raw, b

def norm_to_raw_double(a1_norm, b1, a2_norm, b2, D_max, R_max):
    c1 = a1_norm * D_max * (R_max ** (-b1))
    c2 = a2_norm * D_max * (R_max ** (-b2))
    return c1, b1, c2, b2

# ---- pochodne / lambda ----
def lambda_from_single(R, a, b):
    return - a * b * (R ** (b - 1))

def lambda_from_double(R, c1, b1, c2, b2):
    return - (c1 * b1 * (R ** (b1 - 1)) + c2 * b2 * (R ** (b2 - 1)))

# ---- pobieranie danych z bazy ----
def fetch_data(table_name):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(f'''
        SELECT q_level,
               SUM(quant_main_bits_y), SUM(quant_main_dist_y),
               SUM(quant_main_bits_cb), SUM(quant_main_dist_cb),
               SUM(quant_main_bits_cr), SUM(quant_main_dist_cr)
        FROM "{table_name}"
        GROUP BY q_level
        ORDER BY q_level
    ''')
    rows = cur.fetchall()
    conn.close()
    return rows

# ---- główna pętla ----
results = []

quant_layouts = {
    "": "default",
    "_flat": "flat",
    "_semiflat": "semiflat"
}

for seq in sequence_names:
    for suffix, layout_name in quant_layouts.items():
        table_name = seq + suffix
        print(f"\n[{seq}] Analiza dla layoutu: {layout_name}")

        rows = fetch_data(table_name)
        if not rows:
            print(f"[{table_name}] Brak danych w bazie - pomijam.")
            continue

        # budujemy tablice
        Q = np.array([r[0] for r in rows], dtype=float)
        R_y = np.array([r[1] for r in rows], dtype=float)
        D_y = np.array([r[2] for r in rows], dtype=float)
        R_cb = np.array([r[3] for r in rows], dtype=float)
        D_cb = np.array([r[4] for r in rows], dtype=float)
        R_cr = np.array([r[5] for r in rows], dtype=float)
        D_cr = np.array([r[6] for r in rows], dtype=float)

        # ---- LUMA: jednoskładnikowy model ----
        mask = (
            (R_y > 0) & (D_y > 0) &
            np.isfinite(R_y) & np.isfinite(D_y) &
            (Q >= Q_MIN) & (Q <= Q_MAX)
        )
        if np.sum(mask) < 3:
            print(f"[{table_name}] Luma: za mało punktów ({np.sum(mask)}) - pomijam.")
        else:
            R_sel = R_y[mask]
            D_sel = D_y[mask]
            R_max = np.max(R_sel)
            D_max = np.max(D_sel)

            Rn = R_sel / R_max
            Dn = D_sel / D_max

            try:
                popt, _ = curve_fit(single_power_norm, Rn, Dn, p0=[1.0, -1.0],
                                    bounds=([0, -15], [10, 15]), maxfev=200000)
                a_norm, b = popt
                a_raw, b_raw = norm_to_raw_single(a_norm, b, D_max, R_max)

                D_hat = a_raw * (R_sel ** b_raw)
                r_val = pearsonr(D_sel, D_hat)[0]

                print(f"[{table_name}] Luma: dopasowanie OK, |r|={abs(r_val):.4f}")

                # wykresy
                R_plot = np.linspace(np.min(R_sel), np.max(R_sel), 300)
                D_plot = a_raw * (R_plot ** b_raw)
                lam_plot = lambda_from_single(R_plot, a_raw, b_raw)

                plt.figure(figsize=(8,5))
                plt.scatter(R_sel, D_sel, s=20, label="dane (Luma)")
                plt.plot(R_plot, D_plot, '-', label="fit: D=a R^b")
                plt.xlabel("R (bits)")
                plt.ylabel("D (dist)")
                plt.title(f"Luma - {seq} ({layout_name})")
                plt.grid(True)
                plt.legend()
                plt.savefig(f"plots/RD/Luma/{seq}_{layout_name}_luma_RD.png")
                plt.close()

                plt.figure(figsize=(8,5))
                plt.plot(R_plot, lam_plot, '-', label="λ(R)")
                plt.xlabel("R (bits)")
                plt.ylabel("λ(R)")
                plt.title(f"Lambda(R) - Luma - {seq} ({layout_name})")
                plt.grid(True)
                plt.legend()
                plt.savefig(f"plots/Lambda/Luma/{seq}_{layout_name}_luma_lambda.png")
                plt.close()

                results.append({
                    "seq": seq,
                    "layout": layout_name,
                    "channel": "Luma",
                    "fit_type": "single",
                    "params": (a_raw, b_raw),
                    "pearson": float(r_val)
                })

            except Exception as e:
                print(f"[{table_name}] Luma: błąd dopasowania: {e}")

        # ---- CHROMA: Cb+Cr, model dwuskładnikowy ----
        R_chroma = (R_cb + R_cr)
        D_chroma = (D_cb + D_cr)
        mask_c = (
            (R_chroma > 0) & (D_chroma > 0) &
            np.isfinite(R_chroma) & np.isfinite(D_chroma) &
            (Q >= Q_MIN) & (Q <= Q_MAX)
        )
        if np.sum(mask_c) < 4:
            print(f"[{table_name}] Chroma: za mało punktów ({np.sum(mask_c)}) - pomijam.")
        else:
            R_sel = R_chroma[mask_c]
            D_sel = D_chroma[mask_c]
            R_max = np.max(R_sel)
            D_max = np.max(D_sel)

            Rn = R_sel / R_max
            Dn = D_sel / D_max

            try:
                p0 = [0.6, -1.0, 0.4, -0.1]
                lower = [0, -15, 0, -15]
                upper = [10, 15, 10, 15]
                popt, _ = curve_fit(double_power_norm, Rn, Dn, p0=p0,
                                    bounds=(lower, upper), maxfev=300000)
                a1n, b1, a2n, b2 = popt
                c1, b1_raw, c2, b2_raw = norm_to_raw_double(a1n, b1, a2n, b2, D_max, R_max)

                D_hat = c1 * (R_sel ** b1_raw) + c2 * (R_sel ** b2_raw)
                r_val = pearsonr(D_sel, D_hat)[0]

                print(f"[{table_name}] Chroma: dopasowanie OK, |r|={abs(r_val):.4f}")

                # wykresy
                R_plot = np.linspace(np.min(R_sel), np.max(R_sel), 400)
                D_plot = c1 * (R_plot ** b1_raw) + c2 * (R_plot ** b2_raw)
                lam_plot = lambda_from_double(R_plot, c1, b1_raw, c2, b2_raw)

                plt.figure(figsize=(8,5))
                plt.scatter(R_sel, D_sel, s=20, label="dane (Cb+Cr)")
                plt.plot(R_plot, D_plot, '-', label="fit (Cb+Cr)")
                plt.xlabel("R (bits)")
                plt.ylabel("D (dist sum)")
                plt.title(f"Chroma (Cb+Cr) - {seq} ({layout_name})")
                plt.grid(True)
                plt.legend()
                plt.savefig(f"plots/RD/Chroma/{seq}_{layout_name}_chroma_RD.png")
                plt.close()

                plt.figure(figsize=(8,5))
                plt.plot(R_plot, lam_plot, '-', label="λ(R)")
                plt.xlabel("R (bits)")
                plt.ylabel("λ(R)")
                plt.title(f"Lambda(R) - Chroma - {seq} ({layout_name})")
                plt.grid(True)
                plt.legend()
                plt.savefig(f"plots/Lambda/Chroma/{seq}_{layout_name}_chroma_lambda.png")
                plt.close()

                results.append({
                    "seq": seq,
                    "layout": layout_name,
                    "channel": "Chroma Cb+Cr",
                    "fit_type": "double",
                    "params": (c1, b1_raw, c2, b2_raw),
                    "pearson": float(r_val)
                })

            except Exception as e:
                print(f"[{table_name}] Chroma: błąd dopasowania: {e}")

# ---- zapis CSV ----
csv_path = "fit_params.csv"
with open(csv_path, "w", newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["sequence", "layout", "channel", "fit_type", "params", "pearson"])
    for r in results:
        writer.writerow([
            r["seq"], r["layout"], r["channel"], r["fit_type"],
            ";".join([f"{x:.6e}" for x in r["params"]]),
            f"{r['pearson']:.6f}"]
        )

print(f"\nZapisano parametry do {csv_path}")
print("Wykresy RD i Lambda zapisane w katalogu plots/ ...")
