import csv
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "database" / "telemetry.db"
EXPORT_PATH = Path(__file__).resolve().parent.parent / "logs" / "telemetry_export.csv"

def export_telemetry_to_csv():
    EXPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    columns = [
        "id",
        "timestamp",
        "temperature",
        "pressure",
        "altitude",
        "accel_x",
        "accel_y",
        "accel_z",
        "gyro_x",
        "gyro_y",
        "gyro_z",
        "temperature_status",
        "pressure_status",
        "imu_status",
    ]
    export_path = EXPORT_PATH

    if export_path.exists():
        with open(export_path, newline="") as csv_file:
            existing_columns = next(csv.reader(csv_file), None)

        if existing_columns != columns:
            export_path = EXPORT_PATH.with_name("telemetry_export_v2.csv")

    last_exported_id = 0
    if export_path.exists():
        with open(export_path, newline="") as csv_file:
            reader = csv.reader(csv_file)
            next(reader, None)
            last_row = None
            for last_row in reader:
                pass
            if last_row:
                last_exported_id = int(last_row[0])

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM telemetry WHERE id > ? ORDER BY id ASC",
        (last_exported_id,),
    ).fetchall()
    conn.close()

    file_exists = export_path.exists()
    with open(export_path, "a", newline="") as csv_file:
        writer = csv.writer(csv_file)
        if not file_exists:
            writer.writerow(columns)

        for row in rows:
            writer.writerow([row[column] for column in columns])

    return str(export_path)