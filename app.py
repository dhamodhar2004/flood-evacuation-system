import json
import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

# Optional imports (used only if available locally)
try:
    import geopandas as gpd
except Exception:
    gpd = None

try:
    from geopy.geocoders import Nominatim
except Exception:
    Nominatim = None


# -----------------------------
# API URL CONFIG (SAFE)
# -----------------------------
API_URL = "http://127.0.0.1:8000/route"

try:
    API_URL = st.secrets["API_URL"]
except Exception:
    pass


# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="Flood Evacuation System", layout="centered")

st.title("🌊 Flood Evacuation Routing System")
st.write("Enter your location to find the safest evacuation route.")


# -----------------------------
# SESSION STATE INIT
# -----------------------------
if "result" not in st.session_state:
    st.session_state.result = None

if "user_location" not in st.session_state:
    st.session_state.user_location = None


# -----------------------------
# LOCATION INPUT MODE
# -----------------------------
input_mode = st.radio(
    "Choose location input method:",
    ["Location Name", "Latitude & Longitude"]
)


# -----------------------------
# USER INPUT
# -----------------------------
if input_mode == "Location Name":
    location_name = st.text_input(
        "Enter Location Name",
        value="Egmore, Chennai"
    )

else:
    lat = st.number_input(
        "Enter Latitude",
        value=13.0604,
        format="%.6f"
    )
    lon = st.number_input(
        "Enter Longitude",
        value=80.2496,
        format="%.6f"
    )


# -----------------------------
# BUTTON ACTION
# -----------------------------
if st.button("🚨 Find Safe Route"):

    # Resolve location name → lat/lon
    if input_mode == "Location Name":

        if Nominatim is None:
            st.error("Geocoding service not available.")
            st.stop()

        try:
            geolocator = Nominatim(user_agent="flood-evacuation-system")
            location = geolocator.geocode(location_name)

            if location is None:
                st.error("Location not found. Please try a different name.")
                st.stop()

            lat = location.latitude
            lon = location.longitude

            st.info(
                f"📍 Resolved location: ({lat:.5f}, {lon:.5f})"
            )

        except Exception:
            st.error("Failed to resolve location name.")
            st.stop()

    payload = {"lat": lat, "lon": lon}

    try:
        response = requests.post(API_URL, json=payload, timeout=15)
        st.session_state.result = response.json()
        st.session_state.user_location = (lat, lon)

    except Exception:
        st.warning(
            "Backend is running locally. "
            "For full demo, please run the backend on a local machine."
        )
        st.session_state.result = None


# -----------------------------
# DISPLAY RESULT (PERSISTENT)
# -----------------------------
if st.session_state.result:

    result = st.session_state.result

    if result.get("status") == "success":

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

        # -----------------------------
        # SAFE ROUTE (GREEN)
        # -----------------------------
        route_coords = result.get("route", [])

        if route_coords:
            folium.PolyLine(
                locations=route_coords,
                color="green",
                weight=5,
                tooltip="Safe Evacuation Route"
            ).add_to(m)

        # -----------------------------
        # BLOCKED ROADS (RED) – LOCAL ONLY
        # -----------------------------
        if gpd is not None:
            try:
                blocked_roads = gpd.read_file(
                    "backend/data/roads_with_status.geojson"
                )
                blocked_roads = blocked_roads[
                    blocked_roads["status"] == "blocked"
                ]

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

            except Exception:
                st.info("Blocked roads shown in local demo only.")

        # -----------------------------
        # FLOOD ZONES (BLUE) – LOCAL ONLY
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
            st.info("Flood zones shown in local demo only.")

        st_folium(m, width=700, height=500)

    else:
        st.error("No safe route found.")
