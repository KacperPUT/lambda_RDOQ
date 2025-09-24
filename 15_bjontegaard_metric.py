import os
import sqlite3
import csv
from xBjontegaardMetric import xBjontegaardMetric

db_path = r"C:\Users\ITM\Desktop\database\lambda_compare.db"
output_dir = r"C:\Users\ITM\Desktop\wykresy_bj"
os.makedirs(output_dir, exist_ok=True)

quant_tab_layouts = ["Default", "Flat", "SemiFlat"]

# Grupy Q
Q_L = {20, 25, 30, 35}
Q_M = {50, 55, 60, 65}
Q_H = {80, 85, 90, 95}
Q_groups = [("Q_L_20-35", Q_L), ("Q_M_50-65", Q_M), ("Q_H_80-95", Q_H)]

# Połącz z bazą
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Pobierz listę sekwencji, pomiń wewnętrzne tabele
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
sequences = [row[0] for row in cursor.fetchall()]

# Przygotowanie wyników
results = { (group_name, qtl): [] for group_name, _ in Q_groups for qtl in quant_tab_layouts }

for seq in sequences:
    for qtl in quant_tab_layouts:
        try:
            # Pobierz dane dla Lambda=0
            cursor.execute(
                f"SELECT Q, Bitrate_kib, PSNR_Y, PSNR_Cb, PSNR_Cr, EncodeTime_ms, DecodeTime_ms, TotalTime_ms FROM '{seq}' "
                f"WHERE LambdaMode=0 AND QuantTabLayout=? ORDER BY Q",
                (qtl,)
            )
            data0 = cursor.fetchall()

            # Pobierz dane dla Lambda=1
            cursor.execute(
                f"SELECT Q, Bitrate_kib, PSNR_Y, PSNR_Cb, PSNR_Cr, EncodeTime_ms, DecodeTime_ms, TotalTime_ms FROM '{seq}' "
                f"WHERE LambdaMode=1 AND QuantTabLayout=? ORDER BY Q",
                (qtl,)
            )
            data1 = cursor.fetchall()
        except sqlite3.OperationalError as e:
            print(f"Błąd w tabeli {seq} ({qtl}): {e}")
            continue

        if not data0 or not data1:
            continue

        for group_name, Q_set in Q_groups:
            filtered0 = [row for row in data0 if row[0] in Q_set]
            filtered1 = [row for row in data1 if row[0] in Q_set]

            if len(filtered0) < 2 or len(filtered1) < 2:
                continue

            # Rozpakowanie danych
            q0, bitrate0, psnrY0, psnrCb0, psnrCr0, enc0, dec0, tot0 = zip(*filtered0)
            q1, bitrate1, psnrY1, psnrCb1, psnrCr1, enc1, dec1, tot1 = zip(*filtered1)

            # ΔBitrate i ΔPSNR
            dRateY = xBjontegaardMetric.bjontegaard_drate_new(bitrate0, psnrY0, bitrate1, psnrY1) * 100
            psnrYCbCr0 = [(6*y + cb + cr)/8 for y, cb, cr in zip(psnrY0, psnrCb0, psnrCr0)]
            psnrYCbCr1 = [(6*y + cb + cr)/8 for y, cb, cr in zip(psnrY1, psnrCb1, psnrCr1)]
            dRateYCbCr = xBjontegaardMetric.bjontegaard_drate_new(bitrate0, psnrYCbCr0, bitrate1, psnrYCbCr1) * 100

            dPSNRY = xBjontegaardMetric.bjontegaard_dpsnr_new(bitrate0, psnrY0, bitrate1, psnrY1)
            dPSNRYCbCr = xBjontegaardMetric.bjontegaard_dpsnr_new(bitrate0, psnrYCbCr0, bitrate1, psnrYCbCr1)

            # ΔCzasy w %
            dEnc = [(e1 - e0)/e0*100 for e0, e1 in zip(enc0, enc1)]
            dDec = [(d1 - d0)/d0*100 for d0, d1 in zip(dec0, dec1)]
            dTot = [(t1 - t0)/t0*100 for t0, t1 in zip(tot0, tot1)]
            mean_dEnc = sum(dEnc)/len(dEnc)
            mean_dDec = sum(dDec)/len(dDec)
            mean_dTot = sum(dTot)/len(dTot)

            results[(group_name, qtl)].append((
                seq, qtl, dPSNRY, dPSNRYCbCr, dRateY, dRateYCbCr,
                mean_dEnc, mean_dDec, mean_dTot
            ))

conn.close()

# Funkcja do zapisu i wyświetlenia tabeli
def save_and_print_table(results_list, group_name, qtl):
    print(f"\nTabela {group_name} - {qtl}:")
    print("Sekwencja\tΔPSNR-Y [dB]\tΔPSNR-YCbCr [dB]\tΔBitrate-Y [%]\tΔBitrate-YCbCr [%]\tΔEncTime [%]\tΔDecTime [%]\tΔTotTime [%]")
    for row in results_list:
        print(f"{row[0]}\t{row[2]:.2f}\t{row[3]:.2f}\t{row[4]:.2f}\t{row[5]:.2f}\t{row[6]:.2f}\t{row[7]:.2f}\t{row[8]:.2f}")

    if results_list:
        avg_vals = [sum(r[i] for r in results_list)/len(results_list) for i in range(2,9)]
        print("Średnie wartości Δ dla grupy:")
        print("\t".join([f"{v:.2f}" for v in avg_vals]))
    else:
        avg_vals = [None]*7

    # Zapis CSV
    csv_file = os.path.join(output_dir, f"{group_name}_{qtl}.csv")
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Sekwencja","ΔPSNR-Y [dB]","ΔPSNR-YCbCr [dB]",
                         "ΔBitrate-Y [%]","ΔBitrate-YCbCr [%]",
                         "ΔEncTime [%]","ΔDecTime [%]","ΔTotTime [%]"])
        for row in results_list:
            writer.writerow([row[0], f"{row[2]:.2f}", f"{row[3]:.2f}", f"{row[4]:.2f}", f"{row[5]:.2f}",
                             f"{row[6]:.2f}", f"{row[7]:.2f}", f"{row[8]:.2f}"])
        if results_list:
            writer.writerow([])
            writer.writerow(["Średnie Δ", *["{:.2f}".format(v) for v in avg_vals]])

# Zapis i wyświetlenie wszystkich kombinacji grup Q i układów kwantyzacji
for (group_name, qtl), res_list in results.items():
    save_and_print_table(res_list, group_name, qtl)
