import geopandas as gpd

ROADS_PATH = "backend/data/roads.geojson"
OUTPUT_PATH = "backend/data/roads_with_status.geojson"

# -----------------------------
# LOAD ROADS
# -----------------------------
roads = gpd.read_file(ROADS_PATH)
print("Roads loaded:", len(roads))

# Force CRS (lat/lon)
roads = roads.set_crs(epsg=4326, allow_override=True)

# -----------------------------
# CREATE DEMO FLOOD ZONE
# -----------------------------
# Take city center and create a flood buffer around it
city_center = roads.geometry.unary_union.centroid

# Convert to meters for buffering
roads_m = roads.to_crs(epsg=3857)
center_m = gpd.GeoSeries([city_center], crs=4326).to_crs(epsg=3857).iloc[0]

# Create a flood zone of ~2 km radius
flood_zone = center_m.buffer(2000)

# -----------------------------
# MARK ROADS
# -----------------------------
roads_m["status"] = roads_m.geometry.apply(
    lambda g: "blocked" if g.intersects(flood_zone) else "safe"
)

# Convert back to lat/lon
roads_final = roads_m.to_crs(epsg=4326)

# -----------------------------
# SAVE OUTPUT
# -----------------------------
roads_final.to_file(OUTPUT_PATH, driver="GeoJSON")

print("Blocked roads marked successfully!")
print(roads_final["status"].value_counts())
