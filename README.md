# Tourism Safety Risk Prediction System

A machine learning-powered system that predicts safety risks for tourism routes and provides safe route recommendations.

## Features

- **Risk Prediction**: Predicts safety risk levels for any geographic location
- **Safe Route Planning**: Calculates the safest route between two points
- **Real-time Analysis**: Considers weather, terrain, building density, and other factors
- **Interactive Map**: Visual interface for route planning

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Backend Server
```bash
python app.py
```
Or run the batch file:
```bash
start_backend.bat
```

### 3. Open the Frontend
Open `map.html` in your web browser.

## API Endpoints

### POST /predict
Predict risk for a single location.

**Request:**
```json
{
  "lat": 31.32,
  "lng": 75.57
}
```

**Response:**
```json
{
  "risk_level": 1,
  "risk_score": 0.75,
  "features": {
    "water_distance": 0.5,
    "hospital_distance": 1.2,
    "building_density": 3
  }
}
```

### POST /route
Calculate safe route between two points.

**Request:**
```json
{
  "start": [31.32, 75.57],
  "end": [31.35, 75.60]
}
```

**Response:**
```json
{
  "route": [[31.32, 75.57], [31.33, 75.58], ...],
  "zones": ["green", "yellow", "red", ...]
}
```

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true
}
```

## Risk Levels

- **0 (Green)**: Low risk - Safe area
- **1 (Yellow)**: Medium risk - Exercise caution
- **2 (Red)**: High risk - Avoid if possible

## How It Works

1. **Data Processing**: The system processes geographical data including water bodies, hospitals, buildings, and roads
2. **Feature Extraction**: Calculates distances, densities, and environmental factors
3. **ML Prediction**: Uses a trained Random Forest model to predict risk levels
4. **Route Optimization**: Evaluates multiple route options to find the safest path

## Files Structure

- `app.py` - Flask backend server
- `predict.py` - Standalone prediction script
- `train_model.py` - Model training script
- `route_safety.py` - Route calculation logic
- `map.html` - Frontend interface
- `risk_model.pkl` - Trained machine learning model
- `*.geojson` - Geographical data files
- `*.csv` - Dataset files

## Requirements

- Python 3.8+
- Flask
- Scikit-learn
- GeoPandas
- OSMnx
- NetworkX
- Pandas
- NumPy

## Usage

1. Run the backend server
2. Open `map.html` in your browser
3. Click on the map to set start and end points
4. The system will automatically calculate and display the safest route with color-coded risk zones

## Model Features

The ML model considers:
- Geographic coordinates
- Distance to water bodies
- Distance to hospitals
- Building density
- Time of day
- Weather conditions
- Terrain elevation
- Crime probability
- Network coverage
