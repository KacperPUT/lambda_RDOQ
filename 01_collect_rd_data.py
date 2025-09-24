# 01_collect_rd_data.py
import subprocess
import re
import sqlite3
from tqdm import tqdm

def run_encoder_and_get_output(path, args):
    try:
        process = subprocess.run([path] + args, capture_output=True, text=True, check=True, encoding='utf-8')
        return process.stdout
    except subprocess.CalledProcessError as e:
        print(f"Błąd podczas uruchamiania kodera: {e}")
        return None

def safe_float_convert(s):
    if s and s.lower() == '-nan':
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None

def parse_encoder_output(output):
    frames_data = []
    frame_blocks = re.split(r'\n(?=Frame\s+\d+)', output)

    patterns = {
        'QuantMain': r'QuantMain EstNumBits=(\d+)\s+(\d+)\s+(\d+)\s+Distortion=(\d+)\s+(\d+)\s+(\d+)',
        'QuantAuxD': r'QuantAuxD EstNumBits=(\d+)\s+(\d+)\s+(\d+)\s+Distortion=(\d+)\s+(\d+)\s+(\d+)',
        'QuantAuxI': r'QuantAuxI EstNumBits=(\d+)\s+(\d+)\s+(\d+)\s+Distortion=(\d+)\s+(\d+)\s+(\d+)',
        'LambdaD':   r'LambdaD\s*=\s*(-?[\d\.]+|-nan)\s+(-?[\d\.]+|-nan)\s+(-?[\d\.]+|-nan)',
        'LambdaI':   r'LambdaI\s*=\s*(-?[\d\.]+|-nan)\s+(-?[\d\.]+|-nan)\s+(-?[\d\.]+|-nan)',
        'Lambda':    r'Lambda\s*=\s*(-?[\d\.]+|-nan)\s+(-?[\d\.]+|-nan)\s+(-?[\d\.]+|-nan)',
    }

    for block in frame_blocks:
        frame_data = {}
        frame_match = re.search(r'Frame\s+(\d+)', block)
        if not frame_match:
            continue
        frame_data['frame_number'] = int(frame_match.group(1))

        for key, pattern in patterns.items():
            match = re.search(pattern, block)
            if match:
                frame_data[key] = [safe_float_convert(val) for val in match.groups()]
            else:
                frame_data[key] = [None, None, None] if 'Lambda' in key else [None]*6

        frames_data.append(frame_data)

    return frames_data

def save_to_database(conn, data, table_name, sequence_name, q_level):
    cursor = conn.cursor()
    values = (
        sequence_name, q_level, data['frame_number'],
        data['QuantMain'][0], data['QuantMain'][1], data['QuantMain'][2],
        data['QuantMain'][3], data['QuantMain'][4], data['QuantMain'][5],
        data['QuantAuxD'][0], data['QuantAuxD'][1], data['QuantAuxD'][2],
        data['QuantAuxD'][3], data['QuantAuxD'][4], data['QuantAuxD'][5],
        data['QuantAuxI'][0], data['QuantAuxI'][1], data['QuantAuxI'][2],
        data['QuantAuxI'][3], data['QuantAuxI'][4], data['QuantAuxI'][5],
        data['LambdaD'][0], data['LambdaD'][1], data['LambdaD'][2],
        data['LambdaI'][0], data['LambdaI'][1], data['LambdaI'][2],
        data['Lambda'][0],   data['Lambda'][1],   data['Lambda'][2]
    )

    cursor.execute(f'''
        INSERT INTO "{table_name}" (
            sequence_name, q_level, frame_number,
            quant_main_bits_y, quant_main_bits_cb, quant_main_bits_cr,
            quant_main_dist_y, quant_main_dist_cb, quant_main_dist_cr,
            quant_auxd_bits_y, quant_auxd_bits_cb, quant_auxd_bits_cr,
            quant_auxd_dist_y, quant_auxd_dist_cb, quant_auxd_dist_cr,
            quant_auxi_bits_y, quant_auxi_bits_cb, quant_auxi_bits_cr,
            quant_auxi_dist_y, quant_auxi_dist_cb, quant_auxi_dist_cr,
            lambda_d_y, lambda_d_cb, lambda_d_cr,
            lambda_i_y, lambda_i_cb, lambda_i_cr,
            lambda_y, lambda_cb, lambda_cr
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    ''', values)

# --- Główna pętla ---

encoder_path = r'C:\Users\ITM\Desktop\joptenc-dev\buildW\JOptEnc\Release\JOptEnc.exe'
db_path = r'C:\Users\ITM\Desktop\database\jpegRD.db'

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

quant_layouts = {
    'default': "",
    'flat': "_flat",
    'semiflat': "_semiflat"
}

# Połączenie z bazą
conn = sqlite3.connect(db_path)

for seq_name in sequence_names:
    sequence_file = f'C:\\Users\\ITM\\Desktop\\Obrazy\\{seq_name}.yuv'
    print(f"\nSekwencja: {seq_name}")

    for qtl, suffix in quant_layouts.items():
        table_name = seq_name + suffix
        print(f"Layout kwantyzacji: {qtl} -> tabela: {table_name}")

        for q_level in tqdm(range(0, 101), desc=f"Q levels dla {seq_name} ({qtl})", unit="q"):
            encoder_args = [
                '-i', sequence_file,
                '-ps', '1920x1080',
                '-q', str(q_level),
                '-v', '7',
                '-qtl', qtl
            ]
            encoder_output = run_encoder_and_get_output(encoder_path, encoder_args)

            if encoder_output:
                frames_data = parse_encoder_output(encoder_output)
                if frames_data:
                    for frame_data in frames_data:
                        save_to_database(conn, frame_data, table_name, seq_name, q_level)
        conn.commit()

conn.close()
print("Zapis zakończony.")
