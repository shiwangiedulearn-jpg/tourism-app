from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import pandas as pd
import numpy as np
import geopandas as gpd
import json
from route_safety import get_safe_route

app = Flask(__name__)
CORS(app)

# Load the trained model
model = joblib.load("risk_model.pkl")

@app.route('/route', methods=['POST'])
def route():
    """Endpoint to calculate safe route between two points"""
    try:
        data = request.get_json()
        start = data['start']
        end = data['end']
        
        # Calculate safe route using your existing route_safety module
        route_points, risk_zones = get_safe_route(start, end)
        
        return jsonify({
            "route": route_points,
            "zones": risk_zones
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "model_loaded": True})

if __name__ == '__main__':
    print("Starting Tourism Safety Risk Backend...")
    print("Model loaded successfully!")
    app.run(debug=True, host='0.0.0.0', port=5000)
