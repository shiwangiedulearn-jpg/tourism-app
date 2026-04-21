# Deploy Tourism Safety App on Render

## Step-by-Step Guide

### 1. Prepare Your Repository
```bash
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

### 2. Deploy on Render

1. **Go to [render.com](https://render.com)**
2. **Sign up/Login** with your GitHub account
3. **Click "New +"** -> **"Web Service"**
4. **Connect your GitHub repository**
5. **Configure the service:**
   - **Name**: tourism-safety-api
   - **Region**: Choose nearest region
   - **Branch**: main
   - **Runtime**: Python 3**
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: Free (or paid for better performance)

### 3. Environment Variables (Optional)
Add these in Render dashboard:
- `FLASK_ENV=production`
- `PYTHON_VERSION=3.11.0`

### 4. Deploy
Click **"Create Web Service"** and wait for deployment.

### 5. Access Your App
Once deployed, your API will be available at:
`https://tourism-safety-api.onrender.com`

### 6. Test Your Deployment
```bash
# Health check
curl https://tourism-safety-api.onrender.com/health

# Test route prediction
curl -X POST https://tourism-safety-api.onrender.com/route \
  -H "Content-Type: application/json" \
  -d '{"start": [31.32, 75.57], "end": [31.35, 75.60]}'
```

### 7. Frontend Integration
Update your `map.html` to use the deployed API:
```javascript
const API_BASE_URL = 'https://tourism-safety-api.onrender.com';
```

## Important Notes

- **Free tier** has 15-minute sleep time - first request may be slow
- **Model file** (risk_model.pkl) is included in deployment
- **GeoJSON files** are included for geographic data
- **Automatic redeployment** on git push

## Troubleshooting

If deployment fails:
1. Check Render build logs
2. Verify all files are committed to git
3. Check requirements.txt for missing dependencies
4. Ensure model file is not in .gitignore

## Scaling Up

For production, consider:
- Upgrading to paid tier for better performance
- Adding monitoring and logging
- Implementing caching for API responses
- Setting up custom domain
