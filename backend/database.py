import sqlite3
from pathlib import Path

from database.database import Database

DB_PATH = Path(__file__).resolve().parent.parent / "database" / "telemetry.db"

_db = Database()


def init_db():
	return _db


def save_telemetry(payload, result):
	_db.insert_telemetry(payload, result)
	_db.insert_anomaly_events(payload.get("timestamp"), result)


def get_recent_telemetry(limit=20):
	conn = sqlite3.connect(DB_PATH)
	conn.row_factory = sqlite3.Row

	rows = conn.execute(
		"""
		SELECT *
		FROM telemetry
		ORDER BY id DESC
		LIMIT ?
		""",
		(limit,),
	).fetchall()

	conn.close()
	return [dict(row) for row in rows]


def close():
	_db.close()
