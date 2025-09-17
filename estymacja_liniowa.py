# plik: estymacja_liniowa.py
import sqlite3
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import pearsonr
import os

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

os.makedirs("plots_final/Luma", exist_ok=True)
os.makedirs("plots_final/Chroma", exist_ok=True)

# różne layouty
quant_layouts = {
    "": "default",
    "_flat": "flat",
    "_semiflat": "semiflat"
}

def fetch_data(table_name):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f'''
        SELECT q_level,
               SUM(quant_main_bits_y), SUM(quant_main_dist_y),
               SUM(quant_main_bits_cb), SUM(quant_main_dist_cb),
               SUM(quant_main_bits_cr), SUM(quant_main_dist_cr)
        FROM "{table_name}"
        GROUP BY q_level
        ORDER BY q_level
    ''')
    rows = cursor.fetchall()
    conn.close()
    return rows

# --- modele ---
def single_power(R, a, b):
    R = np.maximum(R, 1e-10)
    return a * R**b

def double_power(R, a1, b1, a2, b2):
    R = np.maximum(R, 1e-10)
    return a1*R**b1 + a2*R**b2

# --- wyniki Pearsona ---
srednie_r = {}

for seq in sequence_names:
    for suffix, layout_name in quant_layouts.items():
        table_name = seq + suffix
        print(f"\n[{seq}] Layout: {layout_name}")

        rows = fetch_data(table_name)
        if not rows:
            print(f"Brak danych dla {table_name}")
            continue

        # filtracja Q do zakresu [Q_MIN, Q_MAX]
        rows = [(q, b_y, d_y, b_cb, d_cb, b_cr, d_cr) 
                for (q, b_y, d_y, b_cb, d_cb, b_cr, d_cr) in rows
                if q >= Q_MIN and q <= Q_MAX]
        if not rows:
            print(f"[{table_name}] brak danych w zakresie Q={Q_MIN}..{Q_MAX}")
            continue

        bits_y = np.array([r[1] for r in rows], dtype=float)
        dist_y = np.array([r[2] for r in rows], dtype=float)
        bits_cb = np.array([r[3] for r in rows], dtype=float)
        dist_cb = np.array([r[4] for r in rows], dtype=float)
        bits_cr = np.array([r[5] for r in rows], dtype=float)
        dist_cr = np.array([r[6] for r in rows], dtype=float)

        if layout_name not in srednie_r:
            srednie_r[layout_name] = {"Luma": [], "Chroma Cb": [], "Chroma Cr": [], "Chroma Cb+Cr": []}

        chrom_labels = ["Chroma Cb", "Chroma Cr", "Chroma Cb+Cr"]
        bits_chroma = [bits_cb, bits_cr, bits_cb + bits_cr]
        dist_chroma = [dist_cb, dist_cr, dist_cb + dist_cr]

        # --- Luma: single power ---
        mask = (bits_y > 0) & (dist_y > 0)
        if np.sum(mask) >= 2:
            R_sel = bits_y[mask]
            D_sel = dist_y[mask]

            R_max = np.max(R_sel)
            D_max = np.max(D_sel)
            R_norm = R_sel / R_max
            D_norm = D_sel / D_max

            try:
                popt, _ = curve_fit(single_power, R_norm, D_norm, p0=[1.0, -1.0],
                                    bounds=([0, -15], [5, 15]), maxfev=200000)
                D_hat = single_power(R_norm, *popt) * D_max
                r = pearsonr(D_sel, D_hat)[0]
                srednie_r[layout_name]["Luma"].append(abs(r))

                print(f"[{table_name}] Luma: |r|={abs(r):.4f}, a={popt[0]:.3f}, b={popt[1]:.3f}")

                # wykres
                R_plot = np.linspace(np.min(R_sel), np.max(R_sel), 200)
                R_plot_norm = R_plot / R_max
                plt.figure(figsize=(8,5))
                plt.plot(R_sel, D_sel, 'o', label="Dane")
                plt.plot(R_plot, single_power(R_plot_norm, *popt)*D_max, '-', label="Dopasowanie")
                plt.xlabel("R (bits)")
                plt.ylabel("D")
                plt.title(f"Luma - {seq} ({layout_name})")
                plt.grid(True)
                plt.legend()
                plt.savefig(f"plots_final/Luma/{seq}_{layout_name}_Luma.png")
                plt.close()

            except Exception as e:
                print(f"[{table_name}] Luma dopasowanie błąd: {e}")

        # --- Chroma: double power ---
        for idx in range(3):
            bits_ch = bits_chroma[idx]
            dist_ch = dist_chroma[idx]
            mask = (bits_ch > 0) & (dist_ch > 0)
            if np.sum(mask) < 2:
                continue

            R_sel = bits_ch[mask]
            D_sel = dist_ch[mask]

            R_max = np.max(R_sel)
            D_max = np.max(D_sel)
            R_norm = R_sel / R_max
            D_norm = D_sel / D_max

            try:
                popt, _ = curve_fit(double_power, R_norm, D_norm,
                                    p0=[1.0, -1.0, 0.5, -0.5],
                                    bounds=([0, -15, 0, -15], [5, 15, 5, 15]),
                                    maxfev=200000)
                D_hat = double_power(R_norm, *popt) * D_max
                r = pearsonr(D_sel, D_hat)[0]
                srednie_r[layout_name][chrom_labels[idx]].append(abs(r))

                print(f"[{table_name}] {chrom_labels[idx]}: |r|={abs(r):.4f}, param={popt}")

                # wykres
                R_plot = np.linspace(np.min(R_sel), np.max(R_sel), 200)
                R_plot_norm = R_plot / R_max
                plt.figure(figsize=(8,5))
                plt.plot(R_sel, D_sel, 'o', label="Dane")
                plt.plot(R_plot, double_power(R_plot_norm, *popt)*D_max, '-', label="Dopasowanie")
                plt.xlabel("R (bits)")
                plt.ylabel("D")
                plt.title(f"{chrom_labels[idx]} - {seq} ({layout_name})")
                plt.grid(True)
                plt.legend()
                plt.savefig(f"plots_final/Chroma/{seq}_{layout_name}_{chrom_labels[idx]}.png")
                plt.close()

            except Exception as e:
                print(f"[{table_name}] {chrom_labels[idx]} dopasowanie błąd: {e}")

# --- Średnie wyniki ---
print("\n=== Średnie |r| po wszystkich sekwencjach i layoutach ===")
for layout_name, channels in srednie_r.items():
    print(f"\nLayout: {layout_name}")
    for ch_name, r_list in channels.items():
        if r_list:
            print(f"  {ch_name}: średnie |r|={np.mean(r_list):.4f}")
