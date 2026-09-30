import csv
import io
import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request

from backend.anomaly_detector import AnomalyDetector
from backend.database import DB_PATH, init_db, save_telemetry, get_recent_telemetry
from backend.csv_export import export_telemetry_to_csv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"

app = Flask(
    __name__,
    template_folder=str(DASHBOARD_DIR / "templates"),
    static_folder=str(DASHBOARD_DIR / "static"),
)
detector = AnomalyDetector()

init_db()

@app.route("/dashboard", methods=["GET"])
def dashboard():
    return render_template("index.html")

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "message": "Backend is running",
        "status": "ok"
    }), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat()
    }), 200

@app.route("/analyze", methods=["POST"])
def analyze():
    payload = request.get_json(silent=True) or {}

    if not payload:
        return jsonify({"error": "No JSON payload provided"}), 400

    if "timestamp" not in payload:
        payload["timestamp"] = datetime.utcnow().isoformat()

    result = detector.analyze(payload)
    save_telemetry(payload, result)

    return jsonify({
        "timestamp": payload["timestamp"],
        "status": result
    }), 200

@app.route("/telemetry", methods=["GET"])
def telemetry():
    limit = request.args.get("limit", default=20, type=int)
    limit = max(1, min(limit, 500))
    rows = get_recent_telemetry(limit=limit)
    return jsonify({"telemetry": rows}), 200

@app.route("/export/csv", methods=["GET"])
def download_telemetry_csv():
    sensor = request.args.get("sensor", "all")
    columns_by_sensor = {
        "all": [
            "id", "timestamp", "temperature", "pressure", "altitude",
            "accel_x", "accel_y", "accel_z", "gyro_x", "gyro_y", "gyro_z",
            "temperature_status", "pressure_status", "imu_status",
        ],
        "temperature": ["id", "timestamp", "temperature", "temperature_status"],
        "pressure": ["id", "timestamp", "pressure", "altitude", "pressure_status"],
        "imu": [
            "id", "timestamp", "accel_x", "accel_y", "accel_z",
            "gyro_x", "gyro_y", "gyro_z", "imu_status",
        ],
    }
    columns = columns_by_sensor.get(sensor)
    if columns is None:
        return jsonify({"error": "Unsupported sensor selection"}), 400

    start = request.args.get("start") or None
    end = request.args.get("end") or None
    if start and len(start) == 16:
        start += ":00"
    if end and len(end) == 16:
        end += ":59.999999"

    query = "SELECT " + ", ".join(columns) + " FROM telemetry"
    conditions = []
    parameters = []
    if start:
        conditions.append("timestamp >= ?")
        parameters.append(start)
    if end:
        conditions.append("timestamp <= ?")
        parameters.append(end)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY id ASC"

    with sqlite3.connect(DB_PATH) as connection:
        rows = connection.execute(query, parameters).fetchall()

    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(columns)
    writer.writerows(rows)

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="telemetry_{sensor}.csv"'},
    )

@app.route("/export", methods=["POST"])
def export_data():
    file_path = export_telemetry_to_csv()
    return jsonify({
        "message": "CSV exported successfully",
        "file": file_path
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)