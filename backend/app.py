from flask import Flask, jsonify, request
from datetime import datetime

from backend.anomaly_detector import AnomalyDetector
from backend.database import init_db, save_telemetry, get_recent_telemetry
from backend.csv_export import export_telemetry_to_csv

app = Flask(__name__)
detector = AnomalyDetector()

init_db()

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
    rows = get_recent_telemetry(limit=limit)
    return jsonify({"telemetry": rows}), 200

@app.route("/export", methods=["POST"])
def export_data():
    file_path = export_telemetry_to_csv()
    return jsonify({
        "message": "CSV exported successfully",
        "file": file_path
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)