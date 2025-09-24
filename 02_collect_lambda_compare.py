# 02_collect_lambda_compare.py
import subprocess
import re
import sqlite3
from tqdm import tqdm

encoder_path = r"C:\Users\ITM\Desktop\joptenc-dev\buildW\JOptEnc\Release\JOptEnc.exe"
db_path = r"C:\Users\ITM\Desktop\database\lambda_compare.db"

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

lambda_modes = [0, 1]
q_levels = [20, 25, 30, 35, 50, 55, 60, 65, 80, 85, 90, 95]
quant_tab_layouts = ['Default', 'Flat', 'SemiFlat']
quant_tab_map = {'Default': 0, 'Flat': 1, 'SemiFlat': 2}

def run_encoder(args):
    try:
        result = subprocess.run([encoder_path] + args, capture_output=True, text=True, check=True, encoding='utf-8')
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Błąd kodera: {e}")
        return None

def parse_summary(output):
    patterns = {
        'Bitrate_kib': r'Bitrate\s*=\s*([\d\.]+)',
        'PSNR_Y': r'PSNR-Y\s*=\s*([\d\.]+)',
        'PSNR_Cb': r'PSNR-Cb\s*=\s*([\d\.]+)',
        'PSNR_Cr': r'PSNR-Cr\s*=\s*([\d\.]+)',
        'EncodeTime_ms': r'AvgTime\s+Encode\s+([\d\.]+)',
        'DecodeTime_ms': r'AvgTime\s+Decode\s+([\d\.]+)',
        'TotalTime_ms': r'TotalProcessingTime\s*=\s*([\d\.]+)',
    }
    data = {}
    for key, pat in patterns.items():
        m = re.search(pat, output)
        if m:
            val = float(m.group(1))
            if key == 'TotalTime_ms':
                val *= 1000  # sekundy → ms
            data[key] = val
        else:
            data[key] = None
    return data

def ensure_table(cursor, sequence):
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS "{sequence}" (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Q INTEGER,
            LambdaMode INTEGER,
            QuantTabLayout INTEGER,
            Bitrate_kib REAL,
            PSNR_Y REAL,
            PSNR_Cb REAL,
            PSNR_Cr REAL,
            EncodeTime_ms REAL,
            DecodeTime_ms REAL,
            TotalTime_ms REAL
        )
    ''')

def save_to_db(cursor, sequence, q, lambda_mode, quant_tab_layout, data):
    cursor.execute(f'''
        INSERT INTO "{sequence}" (
            Q, LambdaMode, QuantTabLayout,
            Bitrate_kib, PSNR_Y, PSNR_Cb, PSNR_Cr,
            EncodeTime_ms, DecodeTime_ms, TotalTime_ms
        ) VALUES (?,?,?,?,?,?,?,?,?,?)
    ''', (
        q, lambda_mode, quant_tab_map[quant_tab_layout],
        data['Bitrate_kib'], data['PSNR_Y'], data['PSNR_Cb'], data['PSNR_Cr'],
        data['EncodeTime_ms'], data['DecodeTime_ms'], data['TotalTime_ms']
    ))

# --- główna pętla ---
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

for seq_name in sequence_names:
    seq_file = rf"C:\Users\ITM\Desktop\Obrazy\{seq_name}.yuv"
    print(f"\nPrzetwarzanie sekwencji: {seq_name}")

    ensure_table(cursor, seq_name)

    for lambda_mode in lambda_modes:
        for q in tqdm(q_levels, desc=f"LambdaMode={lambda_mode} Q", unit="Q"):
            for qtl in quant_tab_layouts:
                args = [
                    '-i', seq_file,
                    '-ps', '1920x1080',
                    '-q', str(q),
                    '-v', '7',
                    '-lem', str(lambda_mode),
                    '-qtl', qtl,
                ]
                output = run_encoder(args)
                if output:
                    data = parse_summary(output)
                    save_to_db(cursor, seq_name, q, lambda_mode, qtl, data)
    conn.commit()

conn.close()
print("Zapis zakończony.")
