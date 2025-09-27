# DEM Compare - Frontend (Vite + React)

## Setup
1. Install dependencies:
   ```
   npm install
   ```

2. Run dev server:
   ```
   npm run dev
   ```

3. Make sure backend is running at http://localhost:8000 (default). The frontend posts file to http://localhost:8000/upload-dem/

## Notes
- This is a minimal UI: upload a GeoTIFF, wait for backend processing, then the heightmap viewer will display the normalized difference heightmap.
- For production, host frontend (Vercel, Netlify) and backend with proper CORS and secure keys.
