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

os.makedirs("lambda_aggregate_by_qtl", exist_ok=True)

# --- wczytanie parametrów estymacji ---
fit_dict = {}
with open(params_csv, newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        seq = row['sequence']
        ch = row['channel']
        qtl = row.get('qtl', 'default')
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

# --- agregacja, wygładzanie i dopasowanie osobno dla każdej tabeli ---
def model(Q, alpha, beta):
    return alpha * (101-Q)**beta

fit_results = {}
for ch in ['Luma','Chroma Cb+Cr']:
    fit_results[ch] = {}
    for qtl in qtl_list:
        data = lambda_per_qtl[ch][qtl]
        Qs_sorted = sorted(data.keys())
        if not Qs_sorted:
            continue
        lam_mean = np.array([np.median(data[Q]) for Q in Qs_sorted])
        # wygładzenie
        if len(lam_mean) >= 7:
            lam_mean_smooth = savgol_filter(lam_mean, window_length=5, polyorder=2)
        else:
            lam_mean_smooth = lam_mean.copy()
        Q_fit = np.array(Qs_sorted)
        weights = 1 / (1 + np.abs(lam_mean_smooth - np.median(lam_mean_smooth)))
        try:
            popt,_ = curve_fit(model, Q_fit, lam_mean_smooth, p0=[1000,1.0], sigma=weights, maxfev=200000)
            alpha,beta = popt
            lam_pred = model(Q_fit, alpha, beta)
            r = pearsonr(lam_mean_smooth, lam_pred)[0]
            rmse = np.sqrt(np.mean((lam_mean_smooth - lam_pred)**2))
            fit_results[ch][qtl] = {'alpha':alpha,'beta':beta,'r':r,'rmse':rmse,'Q':Q_fit,'lam':lam_mean_smooth,'lam_pred':lam_pred}
            print(f"{ch} [{qtl}]: lambda(Q) = {alpha:.6g}*(101-Q)^{beta:.6g}, |r|={abs(r):.4f}, RMSE={rmse:.4f}")
        except Exception as e:
            print(f"{ch} [{qtl}] dopasowanie nieudane: {e}")

# --- wykresy ---
for ch in ['Luma','Chroma Cb+Cr']:
    plt.figure(figsize=(8,5))
    for qtl in qtl_list:
        if qtl not in fit_results[ch]:
            continue
        info = fit_results[ch][qtl]
        plt.plot(info['Q'], info['lam'], 'o', label=f"{qtl} median")
        Qplot = np.linspace(min(info['Q']), max(info['Q']),200)
        plt.plot(Qplot, model(Qplot, info['alpha'], info['beta']), '-', label=f"{qtl} fit")
    plt.xlabel("Q")
    plt.ylabel("lambda")
    plt.title(f"Lambda(Q) - {ch} osobno dla tabel")
    plt.grid(True)
    plt.legend()
    plt.savefig(f"lambda_aggregate_by_qtl/{ch.replace(' ','_')}_by_qtl.png")
    plt.close()

print("Gotowe: dopasowania osobno dla każdej tabeli kwantyzacji zapisane w lambda_aggregate_by_qtl/")
