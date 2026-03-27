const express = require('express');
const cors = require('cors');
const { spawn } = require('child_process');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Helper function to run Python script
function runPythonScript(script, args = []) {
    return new Promise((resolve, reject) => {
        const python = spawn('python', [script, ...args], {
            cwd: __dirname,
            stdio: ['pipe', 'pipe', 'pipe']
        });

        let dataString = '';
        let errorString = '';

        python.stdout.on('data', (data) => {
            dataString += data.toString();
        });

        python.stderr.on('data', (data) => {
            errorString += data.toString();
        });

        python.on('close', (code) => {
            if (code !== 0) {
                reject(new Error(`Python script exited with code ${code}: ${errorString}`));
            } else {
                try {
                    const result = JSON.parse(dataString);
                    resolve(result);
                } catch (e) {
                    // If JSON parsing fails, return raw string
                    resolve(dataString.trim());
                }
            }
        });

        python.on('error', (error) => {
            reject(error);
        });
    });
}

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ 
        status: 'healthy', 
        server: 'Node.js',
        python_integration: 'active'
    });
});

// Predict risk for a single location
app.post('/predict', async (req, res) => {
    try {
        const { lat, lng } = req.body;
        
        if (!lat || !lng) {
            return res.status(400).json({ error: 'Latitude and longitude are required' });
        }

        // Create a simple Python script for prediction
        const pythonScript = `
import joblib
import pandas as pd
import numpy as np
import geopandas as gpd
import json

# Load model and data
model = joblib.load("risk_model.pkl")
water = gpd.read_file("water.geojson")
hospital = gpd.read_file("hospital.geojson")
buildings = gpd.read_file("building.geojson")

def get_points(gdf):
    gdf = gdf.to_crs(epsg=3857)
    centroids = gdf.geometry.centroid
    centroids = gpd.GeoSeries(centroids, crs=3857).to_crs(4326)
    gdf["lat"] = centroids.y
    gdf["lng"] = centroids.x
    return gdf[["lat","lng"]].values

water_points = get_points(water)
hospital_points = get_points(hospital)
building_points = get_points(buildings)

def distance(p, points):
    if len(points) == 0:
        return 0
    d = np.sqrt((points[:,0] - p[0])**2 + (points[:,1] - p[1])**2)
    return np.min(d)

def density(p, points):
    if len(points) == 0:
        return 0
    d = np.sqrt((points[:,0] - p[0])**2 + (points[:,1] - p[1])**2)
    return np.sum(d < 0.01)

# Calculate features
lat = ${lat}
lng = ${lng}
dist_water = distance([lat, lng], water_points)
dist_hospital = distance([lat, lng], hospital_points)
building_density = density([lat, lng], building_points)

# Prepare data for prediction
data = pd.DataFrame([[
    lat, lng, 2, 1, dist_water, dist_hospital, building_density, 
    0, 1, 1, 0, 1, 0
]], columns=[
    "lat", "lng", "type", "road_type", "dist_water", "dist_hospital", 
    "building_density", "cluster", "time", "weather", "hill", "crime", "network"
])

# Make prediction
prediction = model.predict(data)[0]
risk_score = model.predict_proba(data)[0].max()

result = {
    "risk_level": int(prediction),
    "risk_score": float(risk_score),
    "features": {
        "water_distance": float(dist_water),
        "hospital_distance": float(dist_hospital),
        "building_density": int(building_density)
    }
}

print(json.dumps(result))
`;

        // Write the script to a temporary file
        const fs = require('fs');
        const tempScript = 'temp_predict.py';
        fs.writeFileSync(tempScript, pythonScript);

        // Run the script
        const result = await runPythonScript(tempScript);
        
        // Clean up
        fs.unlinkSync(tempScript);
        
        res.json(result);
    } catch (error) {
        console.error('Prediction error:', error);
        res.status(500).json({ error: error.message });
    }
});

// Calculate safe route between two points
app.post('/route', async (req, res) => {
    try {
        const { start, end } = req.body;
        
        if (!start || !end || start.length !== 2 || end.length !== 2) {
            return res.status(400).json({ error: 'Valid start and end coordinates are required' });
        }

        // Use existing route_safety.py
        const pythonScript = `
import sys
sys.path.append('.')
from route_safety import get_safe_route
import json

start = [${start[0]}, ${start[1]}]
end = [${end[0]}, ${end[1]}]

try:
    route_points, risk_zones = get_safe_route(start, end)
    result = {
        "route": route_points,
        "zones": risk_zones
    }
    print(json.dumps(result))
except Exception as e:
    error_result = {"error": str(e)}
    print(json.dumps(error_result))
`;

        // Write the script to a temporary file
        const fs = require('fs');
        const tempScript = 'temp_route.py';
        fs.writeFileSync(tempScript, pythonScript);

        // Run the script
        const result = await runPythonScript(tempScript);
        
        // Clean up
        fs.unlinkSync(tempScript);
        
        // Parse the result
        let parsedResult;
        try {
            parsedResult = JSON.parse(result);
        } catch (e) {
            parsedResult = { error: 'Invalid response from Python script' };
        }
        
        if (parsedResult.error) {
            res.status(500).json(parsedResult);
        } else {
            res.json(parsedResult);
        }
    } catch (error) {
        console.error('Route calculation error:', error);
        res.status(500).json({ error: error.message });
    }
});

// Serve static files (for frontend)
app.use(express.static('.'));

// Start server
app.listen(PORT, () => {
    console.log(`🚀 Tourism Safety Backend Server running on port ${PORT}`);
    console.log(`📍 API endpoints:`);
    console.log(`   GET  /health - Health check`);
    console.log(`   POST /predict - Risk prediction`);
    console.log(`   POST /route  - Safe route calculation`);
    console.log(`🌐 Frontend available at: http://localhost:${PORT}/map.html`);
});

module.exports = app;
