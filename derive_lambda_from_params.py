import sqlite3
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.stats import pearsonr
from scipy.signal import savgol_filter
import csv
import os

db_path = r"C:\Users\ITM\Desktop\database\jpegRD.db"
params_csv = "fit_params.csv"

os.makedirs("lambda_aggregate", exist_ok=True)
os.makedirs("lambda_aggregate_by_qtl", exist_ok=True)

# --- wczytanie parametrów estymacji ---
fit_dict = {}
with open(params_csv, newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        seq = row['sequence']
        ch = row['channel']
        qtl = row.get('qtl', 'default')  # jeśli brak kolumny, default
        params = row['params']
        p_list = [float(x) for x in params.split(';') if x.strip() != '']
        fit_dict[(seq, ch, qtl)] = p_list

# --- pobranie danych z bazy ---
def fetch_rows(seq_name):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(f'''
        SELECT q_level,
               SUM(quant_main_bits_y), SUM(quant_main_dist_y),
               SUM(quant_main_bits_cb), SUM(quant_main_dist_cb),
               SUM(quant_main_bits_cr), SUM(quant_main_dist_cr)
        FROM "{seq_name}"
        GROUP BY q_level
        ORDER BY q_level
    ''')
    rows = cur.fetchall()
    conn.close()
    return rows

# --- funkcje lambda ---
def lambda_luma(R, a, b):
    return -a * b * (R ** (b-1))

def lambda_chroma(R, c1, b1, c2, b2):
    return - (c1*b1*(R**(b1-1)) + c2*b2*(R**(b2-1)))

# --- przygotowanie pojemnika na dane per qtl ---
qtl_list = ['default','flat','semiflat']
lambda_per_qtl = {'Luma': {q: {} for q in qtl_list},
                  'Chroma Cb+Cr': {q: {} for q in qtl_list}}

sequences = sorted(set([k[0] for k in fit_dict.keys()]))
for seq in sequences:
    rows = fetch_rows(seq)
    if not rows:
        continue
    Qs = [r[0] for r in rows]
    R_y = np.array([r[1] for r in rows], dtype=float)
    R_cb = np.array([r[3] for r in rows], dtype=float)
    R_cr = np.array([r[5] for r in rows], dtype=float)
    R_chroma_sum = R_cb + R_cr

    for qtl in qtl_list:
        # Luma
        key = (seq,'Luma',qtl)
        if key in fit_dict:
            a,b = fit_dict[key]
            for Q,R in zip(Qs,R_y):
                lam = lambda_luma(R,a,b)
                if np.isfinite(lam):
                    lambda_per_qtl['Luma'][qtl].setdefault(Q, []).append(lam)
        # Chroma
        keyc = (seq,'Chroma Cb+Cr',qtl)
        if keyc in fit_dict:
            c1,b1,c2,b2 = fit_dict[keyc]
            for Q,R in zip(Qs,R_chroma_sum):
                lam = lambda_chroma(R,c1,b1,c2,b2)
                if np.isfinite(lam):
                    lambda_per_qtl['Chroma Cb+Cr'][qtl].setdefault(Q, []).append(lam)

# --- agregacja i zapis CSV dla każdego QTL ---
for ch in ['Luma','Chroma Cb+Cr']:
    for qtl in qtl_list:
        data = lambda_per_qtl[ch][qtl]
        if not data:
            continue
        Qs_sorted = sorted(data.keys())
        lam_mean = [np.median(data[Q]) for Q in Qs_sorted]
        lam_std = [np.std(data[Q]) for Q in Qs_sorted]

        csv_path = os.path.join("lambda_aggregate", f"{ch}_{qtl}_agg.csv")
        with open(csv_path, "w", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Q","lambda_mean","lambda_std"])
            for q,lm,ls in zip(Qs_sorted, lam_mean, lam_std):
                writer.writerow([q,lm,ls])
        print(f"Zapisano: {csv_path}")

        # wykres λ(Q)
        lam_smooth = savgol_filter(lam_mean, window_length=5 if len(lam_mean)>=5 else len(lam_mean), polyorder=2)
        plt.figure(figsize=(8,5))
        plt.plot(Qs_sorted, lam_mean, 'o', label="mediana λ")
        plt.plot(Qs_sorted, lam_smooth, '-', label="wygładzenie")
        plt.xlabel("Q")
        plt.ylabel("lambda")
        plt.title(f"{ch} - {qtl}")
        plt.grid(True)
        plt.legend()
        plt.savefig(f"lambda_aggregate_by_qtl/{ch.replace(' ','_')}_{qtl}_lambda.png")
        plt.close()

print("Gotowe: dopasowania i CSV dla wszystkich QTL zapisane w lambda_aggregate/ i wykresy w lambda_aggregate_by_qtl/")
