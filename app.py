from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import pandas as pd
import numpy as np
import geopandas as gpd
import json
import os
from route_safety import get_safe_route

app = Flask(__name__)
CORS(app)

# Load the trained model
model = joblib.load("risk_model.pkl")

@app.route('/route', methods=['POST'])
def route():
    try:
        data = request.get_json()

        start = data['start']
        end = data['end']

        result = get_safe_route(start, end)

        return jsonify({
            "route": result["route"],
            "zones": result["zones"],
            "score": result["score"]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/', methods=['GET'])
def home():
    """Welcome endpoint"""
    return jsonify({
        "message": "Tourism Safety Risk Prediction API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "predict": "/predict (POST)",
            "route": "/route (POST)"
        },
        "status": "running"
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "model_loaded": True})

if __name__ == '__main__':
    print("Starting Tourism Safety Risk Backend...")
    print("Model loaded successfully!")
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
