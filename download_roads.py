import osmnx as ox
import geopandas as gpd

# -----------------------------
# AREA NAME (CHANGE IF YOU WANT)
# -----------------------------
PLACE_NAME = "Chennai, India"   # you can narrow later

OUTPUT_PATH = "backend/data/roads.geojson"

print("Downloading road network from OpenStreetMap...")

# -----------------------------
# DOWNLOAD ROAD NETWORK
# -----------------------------
G = ox.graph_from_place(PLACE_NAME, network_type="drive")

# Convert graph edges to GeoDataFrame
roads = ox.graph_to_gdfs(G, nodes=False)

print("Total roads downloaded:", len(roads))

# -----------------------------
# SAVE AS GEOJSON
# -----------------------------
roads.to_file(OUTPUT_PATH, driver="GeoJSON")

print("Roads saved to:", OUTPUT_PATH)
