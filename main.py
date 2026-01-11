from fastapi import FastAPI
from pydantic import BaseModel
import osmnx as ox
import geopandas as gpd
import networkx as nx

app = FastAPI(title="Flood Evacuation Routing API")

# -----------------------------
# LOAD DATA ONCE (IMPORTANT)
# -----------------------------
PLACE_NAME = "Chennai, India"
ROADS_STATUS_PATH = "backend/data/roads_with_status.geojson"

print("Loading blocked roads...")
roads = gpd.read_file(ROADS_STATUS_PATH)
roads = roads.set_crs(epsg=4326, allow_override=True)
blocked_roads = roads[roads["status"] == "blocked"]

print("Downloading OSM graph...")
G = ox.graph_from_place(PLACE_NAME, network_type="drive")

# Convert graph edges to GeoDataFrame
nodes, edges = ox.graph_to_gdfs(G)
edges = edges.set_crs(epsg=4326)

# Remove blocked edges (FAST)
blocked_union = blocked_roads.geometry.unary_union
edges["blocked"] = edges.geometry.intersects(blocked_union)

for u, v, k in edges[edges["blocked"]].index:
    if G.has_edge(u, v, k):
        G.remove_edge(u, v, k)

print("Graph ready for routing")

# -----------------------------
# SHELTERS (FIXED)
# -----------------------------
SHELTERS = [
    (13.0827, 80.2707),
    (13.0674, 80.2376),
]

# -----------------------------
# REQUEST MODEL
# -----------------------------
class RouteRequest(BaseModel):
    lat: float
    lon: float

# -----------------------------
# API ENDPOINT
# -----------------------------
@app.post("/route")
def get_safe_route(req: RouteRequest):
    user_node = ox.distance.nearest_nodes(G, req.lon, req.lat)
    shelter_nodes = [
        ox.distance.nearest_nodes(G, lon, lat)
        for lat, lon in SHELTERS
    ]

    best_route = None
    best_length = float("inf")

    for s in shelter_nodes:
        try:
            route = nx.shortest_path(G, user_node, s, weight="length")
            length = nx.shortest_path_length(G, user_node, s, weight="length")

            if length < best_length:
                best_length = length
                best_route = route

        except nx.NetworkXNoPath:
            continue

    if best_route is None:
        return {
            "status": "fail",
            "message": "No safe route found"
        }

    # Convert route nodes → lat/lon
    route_coords = [
        [G.nodes[n]["y"], G.nodes[n]["x"]]
        for n in best_route
    ]

    return {
        "status": "success",
        "distance_meters": round(best_length, 2),
        "route": route_coords
    }
