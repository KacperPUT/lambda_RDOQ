# 00b_init_lambda_compare_db.py
import sqlite3
import os

# Ścieżka do pliku nowej bazy danych
db_path = r"C:\Users\ITM\Desktop\database\lambda_compare.db"

# Lista sekwencji
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

# Upewnij się, że katalog istnieje
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# Połączenie z bazą
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Funkcja tworząca tabelę dla sekwencji z QuantTabLayout i LambdaMode
def create_sequence_table(sequence_name):
    sql = f'''
    CREATE TABLE IF NOT EXISTS "{sequence_name}" (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Q INTEGER,
        LambdaMode INTEGER,      -- 0 = referencyjny, 1 = Twój model
        QuantTabLayout TEXT,     -- 'Default', 'Flat', 'SemiFlat'
        Bitrate_kib REAL,
        PSNR_Y REAL,
        PSNR_Cb REAL,
        PSNR_Cr REAL,
        EncodeTime_ms REAL,
        DecodeTime_ms REAL,
        TotalTime_ms REAL
    )
    '''
    cursor.execute(sql)

# Tworzenie tabel dla wszystkich sekwencji
for seq in sequences:
    create_sequence_table(seq)

# Zatwierdzenie zmian i zamknięcie połączenia
conn.commit()
conn.close()

print(f"Baza danych utworzona: {db_path} z tabelami dla {len(sequences)} sekwencji")
