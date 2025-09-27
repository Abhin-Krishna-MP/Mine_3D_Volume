from rasterio.transform import from_origin
import rasterio
import numpy as np

# Create a small 10x10 DEM with georeferencing

# Generate a larger DEM for better visualization
arr = np.random.uniform(100, 200, (100, 100)).astype('float32')
transform = from_origin(72.0, 19.0, 0.001, 0.001)  # (west, north, xsize, ysize)

with rasterio.open(
    'sample_georef_dem.tif', 'w',
    driver='GTiff',
    height=arr.shape[0],
    width=arr.shape[1],
    count=1,
    dtype=arr.dtype,
    crs='EPSG:4326',
    transform=transform,
) as dst:
    dst.write(arr, 1)
