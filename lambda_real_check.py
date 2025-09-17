import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
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

# Folder na wykresy
os.makedirs("lambda_validation_plots", exist_ok=True)

# Wczytaj dopasowane parametry z test_lambda_Q (osobno dla każdej tabeli)
fit_results = pd.read_csv("lambda_fit_results_by_qtl.csv")

# Modele
def loglog_quad(Q, a, b, c):
    return np.exp(a * np.log(Q) ** 2 + b * np.log(Q) + c)

def loglog_cubic(Q, a, b, c, d):
    return np.exp(a * np.log(Q) ** 3 + b * np.log(Q) ** 2 + c * np.log(Q) + d)

results_list = []

conn = sqlite3.connect(db_path)

# iterujemy przez wszystkie sekwencje i tabele kwantyzacji
for seq in sequence_names:
    for qtl in ["default", "flat", "semiflat"]:
        table_name = seq if qtl == "default" else f"{seq}_{qtl}"

        try:
            df_seq = pd.read_sql_query(
                f"SELECT * FROM '{table_name}' WHERE q_level >= 6 AND q_level <= 100",
                conn
            )

            for channel in ["Luma", "Chroma Cb+Cr"]:
                row = fit_results[(fit_results["channel"] == channel) & (fit_results["qtl"] == qtl)]
                if row.empty:
                    continue

                params = [float(x) for x in row.iloc[0]["params"].split(";")]
                model_name = row.iloc[0]["model"]

                if channel == "Luma":
                    func = loglog_quad
                    lambda_real = df_seq["lambda_y"].values
                    lambda_pred = func(df_seq["q_level"].values, *params)
                    lambda_pred = np.clip(lambda_pred, 0, 4000)
                else:
                    func = loglog_cubic
                    lambda_real = df_seq["lambda_cb"].fillna(0).values + df_seq["lambda_cr"].fillna(0).values
                    lambda_pred = func(df_seq["q_level"].values, *params)
                    lambda_pred = np.clip(lambda_pred, 0, 8000)

                mask = lambda_real > 0
                q_vals = df_seq["q_level"].values[mask]
                lambda_real = lambda_real[mask]
                lambda_pred = lambda_pred[mask]

                if len(lambda_real) == 0:
                    continue

                rel_error = np.abs(lambda_pred - lambda_real) / lambda_real
                mean_rel_error = np.mean(rel_error)
                max_rel_error = np.max(rel_error)

                results_list.append({
                    "sequence": seq,
                    "qtl": qtl,
                    "channel": channel,
                    "mean_rel_error": mean_rel_error,
                    "max_rel_error": max_rel_error
                })

                # wykres
                plt.figure()
                plt.plot(q_vals, lambda_real, 'o', label="real λ")
                plt.plot(q_vals, lambda_pred, '-', label="predicted λ")
                plt.xlabel("q_level")
                plt.ylabel("λ")
                plt.title(f"{seq} [{qtl}] - {channel}")
                plt.legend()
                plt.grid(True)
                plt.savefig(f"lambda_validation_plots/{seq}_{qtl}_{channel}.png")
                plt.close()

        except Exception as e:
            print(f"Błąd dla tabeli {table_name}: {e}")

conn.close()

# zapis wyników szczegółowych
results_df = pd.DataFrame(results_list)
results_df.to_csv("lambda_validation_summary.csv", index=False)
print("=== Szczegółowe wyniki zapisane w lambda_validation_summary.csv ===")
print(results_df)

# --- PODSUMOWANIE ---
summary = results_df.groupby(["qtl", "channel"]).agg({
    "mean_rel_error": "mean",
    "max_rel_error": "mean"
}).reset_index()

summary.to_csv("lambda_validation_summary_mean.csv", index=False)

print("\n=== Średnie błędy względne (po wszystkich sekwencjach) ===")
print(summary)
