# 00_init_database.py
import sqlite3

db_path = r"C:\Users\ITM\Desktop\database\jpegRD.db"
sequences = [
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

# Połączenie z bazą
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Definicja struktury tabeli
table_schema = '''
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sequence_name TEXT,
    q_level INTEGER,
    frame_number INTEGER,

    quant_main_bits_y INTEGER,
    quant_main_bits_cb INTEGER,
    quant_main_bits_cr INTEGER,
    quant_main_dist_y INTEGER,
    quant_main_dist_cb INTEGER,
    quant_main_dist_cr INTEGER,

    quant_auxd_bits_y INTEGER,
    quant_auxd_bits_cb INTEGER,
    quant_auxd_bits_cr INTEGER,
    quant_auxd_dist_y INTEGER,
    quant_auxd_dist_cb INTEGER,
    quant_auxd_dist_cr INTEGER,

    quant_auxi_bits_y INTEGER,
    quant_auxi_bits_cb INTEGER,
    quant_auxi_bits_cr INTEGER,
    quant_auxi_dist_y INTEGER,
    quant_auxi_dist_cb INTEGER,
    quant_auxi_dist_cr INTEGER,

    lambda_d_y REAL,
    lambda_d_cb REAL,
    lambda_d_cr REAL,
    lambda_i_y REAL,
    lambda_i_cb REAL,
    lambda_i_cr REAL,
    lambda_y REAL,
    lambda_cb REAL,
    lambda_cr REAL
)
'''

# Tworzenie tabel dla default, flat i semiflat
for seq in sequences:
    for suffix in ["", "_flat", "_semiflat"]:
        table_name = seq + suffix
        cursor.execute(f'CREATE TABLE IF NOT EXISTS "{table_name}" {table_schema}')
        print(f"Tabela utworzona: {table_name}")

conn.commit()
conn.close()
print("Utworzono wszystkie tabele dla default, flat i semiflat.")
