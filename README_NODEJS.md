# Tourism Safety Risk Prediction System - Node.js Backend

A Node.js backend server that integrates with your Python ML model for tourism safety risk prediction.

## Features

- **Node.js Express Server** with CORS support
- **Python ML Integration** - Calls your existing Python scripts
- **RESTful API** - Same endpoints as before but running on Node.js
- **Static File Serving** - Serves your frontend from the same server
- **Error Handling** - Robust error handling and logging

## Quick Start

### 1. Install Node.js Dependencies
```bash
npm install
```

### 2. Start the Node.js Server
```bash
npm start
```

Or for development with auto-restart:
```bash
npm run dev
```

### 3. Access the Application
- **Full Application**: `http://localhost:3000/map.html`
- **API Health Check**: `http://localhost:3000/health`
- **API Endpoints**: 
  - `POST /predict` - Risk prediction
  - `POST /route` - Safe route calculation

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
  "server": "Node.js",
  "python_integration": "active"
}
```

## How It Works

1. **Node.js Server** handles HTTP requests and serves the frontend
2. **Python Integration** - Server spawns Python processes to run your ML model
3. **Dynamic Script Generation** - Creates temporary Python scripts for predictions
4. **Existing Code Reuse** - Uses your existing `route_safety.py` and `risk_model.pkl`
5. **Unified Port** - Both frontend and backend run on port 3000

## Benefits of Node.js Backend

- **Single Server** - No need for separate frontend/backend servers
- **Better Performance** - Node.js handles concurrent connections efficiently
- **Easy Deployment** - Single process to manage
- **JavaScript Ecosystem** - Access to npm packages and tools
- **Hot Reload** - Development server with auto-restart

## Files Structure

- `server.js` - Node.js Express server
- `package.json` - Node.js dependencies and scripts
- `app.py` - Original Flask backend (backup)
- `map.html` - Frontend interface
- `route_safety.py` - Python route calculation logic
- `risk_model.pkl` - Trained ML model

## Migration from Flask

The Node.js backend provides the same API endpoints as the Flask backend:
- Same request/response formats
- Same functionality
- Better performance and easier deployment

## Requirements

- Node.js 14+ 
- Python 3.8+ (for ML model)
- All Python packages from `requirements.txt`

## Usage

1. Install Node.js dependencies: `npm install`
2. Start the server: `npm start`
3. Open `http://localhost:3000/map.html` in your browser
4. Use the map interface to test predictions and routes
