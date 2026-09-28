import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "database" / "telemetry.db"

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            temperature REAL,
            pressure REAL,
            imu TEXT,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_telemetry(payload, result):
    conn = sqlite3.connect(DB_PATH)

    conn.execute("""
        INSERT INTO telemetry (timestamp, temperature, pressure, imu, status)
        VALUES (?, ?, ?, ?, ?)
    """, (
        payload.get("timestamp"),
        payload.get("temperature"),
        payload.get("barometer", {}).get("pressure") if payload.get("barometer") else None,
        str(payload.get("imu")),
        str(result)
    ))

    conn.commit()
    conn.close()

def get_recent_telemetry(limit=20):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT *
        FROM telemetry
        ORDER BY id DESC
        LIMIT ?
    """, (limit,)).fetchall()

    conn.close()
    return [dict(row) for row in rows]