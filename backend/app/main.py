from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/api/health")
def health():
    return {"status": "ok"}

@app.route("/api/process", methods=["POST"])
def process():
    return jsonify({
        "patient_name": "PATIENT_NAME",
        "chief_complaint": "Brustschmerzen seit 2 Tagen",
        "assessment": "Verdacht auf Angina pectoris"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)