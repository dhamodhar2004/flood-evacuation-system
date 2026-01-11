import json
import geopandas as gpd
import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

# -----------------------------
# CONFIG
# -----------------------------
API_URL = "http://127.0.0.1:8000/route"

st.set_page_config(page_title="Flood Evacuation System", layout="centered")

st.title("🌊 Flood Evacuation Routing System")
st.write("Enter your location to find the safest evacuation route.")

# -----------------------------
# SESSION STATE INIT
# -----------------------------
if "result" not in st.session_state:
    st.session_state.result = None

# -----------------------------
# USER INPUT
# -----------------------------
lat = st.number_input("Enter Latitude", value=13.0604, format="%.6f")
lon = st.number_input("Enter Longitude", value=80.2496, format="%.6f")

# -----------------------------
# BUTTON
# -----------------------------
if st.button("🚨 Find Safe Route"):
    payload = {"lat": lat, "lon": lon}

    try:
        response = requests.post(API_URL, json=payload)
        st.session_state.result = response.json()
        st.session_state.user_location = (lat, lon)

    except Exception as e:
        st.session_state.result = {
            "status": "fail",
            "message": str(e)
        }

# -----------------------------
# DISPLAY RESULT (PERSISTENT)
# -----------------------------
if st.session_state.result:

    result = st.session_state.result

    if result["status"] == "success":
        st.success("Safe route found!")

        distance_km = result["distance_meters"] / 1000
        st.metric("Evacuation Distance (km)", round(distance_km, 2))

        lat, lon = st.session_state.user_location

        # Create map
        m = folium.Map(location=[lat, lon], zoom_start=13)

        # User marker
        folium.Marker(
            [lat, lon],
            popup="Your Location",
            icon=folium.Icon(color="blue", icon="user")
        ).add_to(m)

        # Draw safe route if available
        route_coords = result.get("route", [])

        if route_coords:
            folium.PolyLine(
                locations=route_coords,
                color="green",
                weight=5,
                tooltip="Safe Evacuation Route"
            ).add_to(m)
        # -----------------------------
        # SHOW BLOCKED ROADS (RED)
        # -----------------------------
        try:
            blocked_roads = gpd.read_file(
                "backend/data/roads_with_status.geojson"
            )
            blocked_roads = blocked_roads[blocked_roads["status"] == "blocked"]

            for _, row in blocked_roads.iterrows():
                if row.geometry.geom_type == "LineString":
                    coords = [
                        (lat, lon)
                        for lon, lat in row.geometry.coords
                    ]

                    folium.PolyLine(
                        locations=coords,
                        color="red",
                        weight=2,
                        opacity=0.6
                    ).add_to(m)

        except Exception as e:
            st.warning("Blocked roads could not be loaded")
        # -----------------------------
        # SHOW FLOOD ZONES (BLUE)
        # -----------------------------
        try:
            with open("backend/data/flood_polygons.geojson", "r") as f:
                flood_geojson = json.load(f)

            folium.GeoJson(
                flood_geojson,
                name="Flood Zones",
                style_function=lambda x: {
                    "fillColor": "#4da6ff",
                    "color": "#1f78b4",
                    "weight": 1,
                    "fillOpacity": 0.4,
                },
                tooltip="Flooded Area"
            ).add_to(m)

        except Exception:
            st.warning("Flood zones could not be loaded")

        st_folium(m, width=700, height=500)


    else:
        st.error("No safe route found.")
