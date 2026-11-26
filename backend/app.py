
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from detection import detect_anomalies
from database import init_db, save_results

app = Flask(__name__)
CORS(app)

init_db()


@app.route("/")
def home():
    return jsonify({"message": "Load Sentinel backend is running"})


@app.route("/analyze", methods=["POST"])
def analyze():
    if "file" not in request.files:
        return jsonify({"error": "Please upload a CSV file"}), 400

    file = request.files["file"]

    if not file.filename.lower().endswith(".csv"):
        return jsonify({"error": "Please upload a CSV file"}), 400

    try:
        df = pd.read_csv(file)

        if df.empty or len(df.columns) < 2:
            return jsonify({
                "error": "CSV needs a timestamp column and at least one meter column"
            }), 400

        timestamp_column = df.columns[0]
        meter_columns = df.columns[1:]

        results = []
        total_readings = 0

        for meter in meter_columns:
            readings = pd.to_numeric(df[meter], errors="coerce")
            valid = readings.dropna()
            total_readings += len(valid)

            if len(valid) < 5:
                continue

            anomaly_indexes = detect_anomalies(valid)

            for index in anomaly_indexes:
                results.append({
                    "timestamp": str(df.loc[index, timestamp_column]),
                    "meter": str(meter),
                    "reading": float(readings.loc[index]),
                    "status": "Anomaly"
                })

        save_results(results)

        return jsonify({
            "message": "Analysis completed successfully",
            "total_readings": total_readings,
            "anomaly_count": len(results),
            "anomalies": results
        })

    except Exception:
        return jsonify({
            "error": "Could not process this CSV. Check its format and readings."
        }), 400


if __name__ == "__main__":
    app.run(debug=True)

