import osmnx as ox
import geopandas as gpd
import networkx as nx

# -----------------------------
# CONFIG
# -----------------------------
PLACE_NAME = "Chennai, India"
ROADS_STATUS_PATH = "backend/data/roads_with_status.geojson"

# -----------------------------
# LOAD ROADS WITH STATUS
# -----------------------------
roads = gpd.read_file(ROADS_STATUS_PATH)
roads = roads.set_crs(epsg=4326, allow_override=True)

blocked_roads = roads[roads["status"] == "blocked"]
print("Blocked roads:", len(blocked_roads))

# -----------------------------
# LOAD GRAPH ONCE
# -----------------------------
print("Downloading OSM graph...")
G = ox.graph_from_place(PLACE_NAME, network_type="drive")
print("Graph loaded")

# -----------------------------
# GET GRAPH EDGES AS GDF (ONCE)
# -----------------------------
nodes, edges = ox.graph_to_gdfs(G)
edges = edges.set_crs(epsg=4326)

print("Total graph edges:", len(edges))

# -----------------------------
# FIND BLOCKED EDGES (FAST)
# -----------------------------
blocked_union = blocked_roads.geometry.unary_union

edges["blocked"] = edges.geometry.intersects(blocked_union)
blocked_edges = edges[edges["blocked"]]

print("Graph edges to remove:", len(blocked_edges))

# -----------------------------
# REMOVE BLOCKED EDGES (FAST)
# -----------------------------
for u, v, k in blocked_edges.index:
    if G.has_edge(u, v, k):
        G.remove_edge(u, v, k)

print("Blocked edges removed")
print("Remaining edges:", len(G.edges))

# -----------------------------
# DEFINE SHELTERS
# -----------------------------
shelters = [
    (13.0827, 80.2707),
    (13.0674, 80.2376),
]

# -----------------------------
# USER LOCATION
# -----------------------------
user_lat = 13.0604
user_lon = 80.2496

user_node = ox.distance.nearest_nodes(G, user_lon, user_lat)
shelter_nodes = [
    ox.distance.nearest_nodes(G, lon, lat)
    for lat, lon in shelters
]

# -----------------------------
# ROUTING
# -----------------------------
best_route = None
best_length = float("inf")

for s in shelter_nodes:
    try:
        length = nx.shortest_path_length(G, user_node, s, weight="length")
        route = nx.shortest_path(G, user_node, s, weight="length")
        if length < best_length:
            best_length = length
            best_route = route
    except nx.NetworkXNoPath:
        continue

# -----------------------------
# RESULT
# -----------------------------
if best_route:
    print("✅ Safe route found")
    print("Distance (meters):", round(best_length, 2))
else:
    print("❌ No safe route found")
