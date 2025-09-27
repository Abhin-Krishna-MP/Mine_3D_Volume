# DEM Compare - Backend

## Overview
FastAPI backend that accepts a user-provided GeoTIFF DEM, fetches a current DEM for the same bbox from OpenTopography,
reprojects/resamples to the user's grid, computes the difference (current - user), and returns:
- normalized PNG heightmap (for frontend displacement)
- metadata JSON with min/max for accurate scaling
- metrics (min/max/mean/volume)

## Setup (local)
1. Install system GDAL libs (Ubuntu):
   ```bash
   sudo apt update
   sudo apt install -y build-essential gdal-bin libgdal-dev
   ```

2. Create venv and install Python deps:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Set OpenTopography API key (optional but recommended for some datasets):
   ```bash
   export OPEN_TOPO_KEY="your_api_key_here"
   ```

4. Run:
   ```bash
   uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```

Static assets (generated PNGs and metadata) are served from `/static`.

## Notes
- This MVP assumes the uploaded GeoTIFF has CRS units in meters for volume computation. If it's in degrees, reproject to an appropriate metric CRS (UTM) before volume calc for accuracy.
- For large areas or higher accuracy, consider additional processing and handling (tiling, PDAL for LAS/LAZ support).
