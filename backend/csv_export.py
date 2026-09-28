import csv
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "database" / "telemetry.db"
EXPORT_PATH = Path(__file__).resolve().parent.parent / "logs" / "telemetry_export.csv"

def export_telemetry_to_csv():
    EXPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT *
        FROM telemetry
        ORDER BY id DESC
    """).fetchall()
    conn.close()

    with open(EXPORT_PATH, "w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["id", "timestamp", "temperature", "pressure", "imu", "status"])

        for row in rows:
            writer.writerow([
                row["id"],
                row["timestamp"],
                row["temperature"],
                row["pressure"],
                row["imu"],
                row["status"]
            ])

    return str(EXPORT_PATH)