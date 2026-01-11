import rasterio
import numpy as np
import geopandas as gpd
from rasterio.features import shapes
from shapely.geometry import shape
from skimage.filters import threshold_otsu

IMAGE_PATH = "backend/data/sentinel_image.tif"
OUTPUT_PATH = "backend/data/flood_polygons.geojson"

# -----------------------------
# STEP 1: Load image
# -----------------------------
with rasterio.open(IMAGE_PATH) as src:
    print("Satellite image loaded")

    print("Number of bands:", src.count)

    # For RGB image:
    # Band 1 = Red
    # Band 2 = Green
    # Band 3 = Blue
    red = src.read(1).astype("float32")
    green = src.read(2).astype("float32")
    blue = src.read(3).astype("float32")

    transform = src.transform
    crs = src.crs

# -----------------------------
# STEP 2: Simple water index
# -----------------------------
# Blue - Red highlights water reasonably well for demo
water_index = blue - red

print("Water index calculated")

# -----------------------------
# STEP 3: Threshold
# -----------------------------
threshold = threshold_otsu(water_index)
flood_mask = water_index > threshold

print("Flood mask created")

# -----------------------------
# STEP 4: Mask → polygons
# -----------------------------
polygons = []

for geom, value in shapes(
    flood_mask.astype("uint8"),
    transform=transform
):
    if value == 1:
        polygons.append(shape(geom))

print("Flood polygons found:", len(polygons))

# -----------------------------
# STEP 5: Save GeoJSON
# -----------------------------
gdf = gpd.GeoDataFrame({"geometry": polygons}, crs=crs)
gdf.to_file(OUTPUT_PATH, driver="GeoJSON")

print("Flood polygons saved successfully!")
