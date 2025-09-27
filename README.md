# DEM Compare - Full Project (MVP)

This repository contains a minimal, ready-to-run MVP for:
- Uploading a user GeoTIFF DEM (backend)
- Fetching current DEM from OpenTopography
- Reprojecting/resampling and computing difference
- Returning a normalized PNG heightmap and basic metrics
- A minimal React frontend to upload and visualize the heightmap (Three.js)

## Quick start (local, without Docker)
1. Backend
   - cd backend
   - Create venv and install:
     ```
     python3 -m venv venv
     source venv/bin/activate
     pip install -r requirements.txt
     ```
   - Set OpenTopography API key:
     ```
     export OPEN_TOPO_KEY="YOUR_KEY_HERE"
     ```
   - Run:
     ```
     uvicorn app:app --reload --host 0.0.0.0 --port 8000
     ```

2. Frontend
   - cd frontend
   - npm install
   - npm run dev
   - Open http://localhost:5173

## Quick start (with Docker Compose)
- Ensure Docker is installed.
- Create .env with OPEN_TOPO_KEY
- Run:
  ```
  docker compose up --build
  ```
- Backend: http://localhost:8000
- Frontend: run locally (recommended) or build and serve separately.

## Notes & next steps
- Volume computations assume metric CRS. If uploaded DEM uses geographic CRS (degrees), reproject to UTM for accurate area/volume calculations.
- Add robust error handling, job queue (Celery/RQ) for long-running processing, S3 storage for generated assets, and authentication for production use.
