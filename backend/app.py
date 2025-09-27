from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os, tempfile, shutil, uuid, math
from dotenv import load_dotenv
import rasterio
from rasterio.warp import reproject, Resampling
import numpy as np
from PIL import Image
import requests
from pathlib import Path

app = FastAPI(title="DEM Compare - Backend")

# Allow CORS from localhost (frontend dev). Adjust in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# serve static files (generated PNGs/meshes)
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

load_dotenv(dotenv_path=Path(__file__).parent / '.env')
OPEN_TOPO_KEY = os.getenv("OPEN_TOPO_KEY", None)
OPEN_TOPO_URL = "https://portal.opentopography.org/API/globaldem"

def fetch_dem_opentopo(bounds, out_path, demtype="SRTMGL1"):
    """
    Fetch a DEM GeoTIFF from OpenTopography for the provided bounds.
    bounds: (left, bottom, right, top)
    out_path: path to write GeoTIFF
    demtype: dataset name (e.g., 'SRTMGL1', 'NASADEM_HGT')
    Requires OPEN_TOPO_KEY env var for large/authorized requests (optional for some endpoints).
    """
    params = {
        "demtype": demtype,
        "west": bounds[0],
        "south": bounds[1],
        "east": bounds[2],
        "north": bounds[3],
        "outputFormat": "GTiff"
    }
    api_key = os.getenv("OPEN_TOPO_KEY", None)
    print(f"[DEBUG] Using OPEN_TOPO_KEY: {api_key}")
    if api_key:
        params["API_Key"] = api_key
    # stream download
    with requests.get(OPEN_TOPO_URL, params=params, stream=True, timeout=60) as r:
        if r.status_code != 200:
            raise Exception(f"OpenTopography API failed {r.status_code}: {r.text[:200]}")
        with open(out_path, "wb") as f:
            shutil.copyfileobj(r.raw, f)
    return out_path

def normalize_to_png(arr, mask=None, vmin=None, vmax=None):
    """Normalize numpy array to 0-255 uint8 PNG. mask=True means masked pixels -> 0"""
    if mask is None:
        mask = np.isnan(arr)
    valid = arr[~mask]
    if valid.size == 0:
        raise Exception("No valid pixels to normalize")
    if vmin is None:
        vmin = float(valid.min())
    if vmax is None:
        vmax = float(valid.max())
    if vmax == vmin:
        vmax = vmin + 1.0
    norm = (arr - vmin) / (vmax - vmin)
    norm = np.clip(norm, 0.0, 1.0)
    img = (norm * 255).astype('uint8')
    img[mask] = 0
    return img, vmin, vmax

@app.post("/upload-dem/")
async def upload_dem(file: UploadFile = File(...)):
    """
    Accepts a GeoTIFF upload (user's DEM). Fetches a current DEM over same bbox from OpenTopography,
    reprojects/resamples it to the user's grid, computes difference (current - user),
    writes a normalized PNG heightmap to /static and returns metrics + URL.
    """
    filename = file.filename
    if not filename.lower().endswith(('.tif', '.tiff')):
        raise HTTPException(status_code=400, detail="Please upload a GeoTIFF (.tif) file for MVP.")
    tmpdir = Path(tempfile.mkdtemp())
    try:
        user_path = tmpdir / filename
        with open(user_path, "wb") as f:
            f.write(await file.read())

        # Read user DEM
        with rasterio.open(str(user_path)) as src:
            user_arr = src.read(1, masked=False).astype('float32')
            user_meta = src.meta.copy()
            user_bounds = src.bounds  # left, bottom, right, top
            user_transform = src.transform
            user_crs = src.crs
            user_width = src.width
            user_height = src.height
            user_nodata = src.nodata if src.nodata is not None else np.nan

        # Fetch current DEM from OpenTopography (writes to fetched.tif)
        fetched_path = tmpdir / "current_dem.tif"
        try:
            fetch_dem_opentopo((user_bounds.left, user_bounds.bottom, user_bounds.right, user_bounds.top), str(fetched_path))
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Failed to fetch DEM from OpenTopography: {e}")

        # Reproject & resample fetched DEM to match user's grid
        with rasterio.open(str(fetched_path)) as src:
            dst_arr = np.empty((user_height, user_width), dtype='float32')
            reproject(
                source=rasterio.band(src, 1),
                destination=dst_arr,
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=user_transform,
                dst_crs=user_crs,
                resampling=Resampling.bilinear,
                dst_nodata=user_nodata
            )

        # Mask nodata
        user_mask = np.isnan(user_arr) | (user_arr == user_nodata)
        dst_mask = np.isnan(dst_arr) | (dst_arr == user_nodata)
        combined_mask = user_mask | dst_mask

        # Compute diff: current - user
        diff = dst_arr - user_arr
        diff_masked = np.ma.array(diff, mask=combined_mask)

        if diff_masked.size == 0 or diff_masked.count() == 0:
            raise HTTPException(status_code=400, detail="No overlapping valid pixels between uploaded DEM and fetched DEM.")

        max_diff = float(diff_masked.max())
        min_diff = float(diff_masked.min())
        mean_diff = float(diff_masked.mean())

        # Approximate pixel area in m^2: only accurate if user CRS units are meters.
        # If user CRS is geographic (degrees), this will be incorrect. Frontend should warn if CRS is degrees.
        try:
            pixel_width = abs(user_transform.a)
            pixel_height = abs(user_transform.e)
            pixel_area = pixel_width * pixel_height
            volume_m3 = float((diff_masked.filled(0)).sum() * pixel_area)
        except Exception:
            volume_m3 = None

        # Create normalized PNG for frontend displacement map
        png_arr, vmin, vmax = normalize_to_png(diff, mask=combined_mask)
        uid = uuid.uuid4().hex[:12]
        png_name = f"diff_{uid}.png"
        png_path = static_dir / png_name
        Image.fromarray(png_arr).save(str(png_path))

        # Save metadata for scaling on frontend
        meta = {
            "min_diff": min_diff,
            "max_diff": max_diff,
            "vmin": vmin,
            "vmax": vmax,
            "width": user_width,
            "height": user_height,
            "pixel_area_m2": pixel_area if 'pixel_area' in locals() else None
        }
        meta_name = f"diff_{uid}.json"
        meta_path = static_dir / meta_name
        with open(meta_path, "w") as mf:
            import json
            json.dump(meta, mf)

        return JSONResponse({
            "status": "success",
            "max_diff": max_diff,
            "min_diff": min_diff,
            "mean_diff": mean_diff,
            "volume_m3": volume_m3,
            "heightmap_url": f"/static/{png_name}",
            "meta_url": f"/static/{meta_name}"
        })

    finally:
        # keep tmpdir for debugging in dev; you may remove it in production
        pass

# Simple healthcheck
@app.get("/health")
def health():
    return {"status":"ok"}
