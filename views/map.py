# views/map.py

import streamlit as st
import time
import math
import pydeck as pdk
import datetime
import pandas as pd

from streamlit_autorefresh import st_autorefresh
from streamlit_bokeh_events import streamlit_bokeh_events
from bokeh.models.widgets import Button
from bokeh.models import CustomJS

# Fonction haversine pour calculer la distance entre deux points
def haversine(lat1, lon1, lat2, lon2):
    R = 6371e3  # Rayon de la Terre en mètres
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def display_map_page():
    st.title("Activité de Course - Suivi en Temps Réel")

    # Vérifier que l'utilisateur est connecté
    if 'user_id' not in st.session_state:
        st.error("Veuillez vous connecter pour accéder à la carte.")
        return

    # Initialisation des variables dans st.session_state
    if 'running' not in st.session_state:
        st.session_state.running = False
    if 'start_time' not in st.session_state:
        st.session_state.start_time = 0.0
    if 'trajectory' not in st.session_state:
        st.session_state.trajectory = []  # Liste des points {lat, lon, timestamp}
    if 'speeds' not in st.session_state:
        st.session_state.speeds = []       # Liste des tuples (timestamp, speed_kmh)
    if 'last_timestamp' not in st.session_state:
        st.session_state.last_timestamp = 0.0
    if 'current_location' not in st.session_state:
        st.session_state.current_location = None  # {lat, lon}

    # Utilisation de streamlit-bokeh-events pour demander la géolocalisation
    st.markdown("### Obtenir votre localisation")
    loc_button = Button(label="Obtenir ma localisation")
    loc_button.js_on_event("button_click", CustomJS(code="""
        navigator.geolocation.getCurrentPosition(
            (loc) => {
                document.dispatchEvent(new CustomEvent("GET_LOCATION", {detail: {lat: loc.coords.latitude, lon: loc.coords.longitude}}))
            },
            (err) => {
                document.dispatchEvent(new CustomEvent("GET_LOCATION", {detail: {error: err.message}}))
            }
        )
        """))
    result = streamlit_bokeh_events(
        loc_button,
        events="GET_LOCATION",
        key="get_location",
        refresh_on_update=False,
        override_height=75,
        debounce_time=0)
    
    # Si une erreur est renvoyée par le navigateur
    if result and "event" in result:
        if "error" in result["event"]:
            st.error(f"Erreur de géolocalisation: {result['event']['error']}")
        else:
            # Mise à jour de la position actuelle
            st.session_state.current_location = {
                "lat": result["event"]["lat"],
                "lon": result["event"]["lon"]
            }
            st.write(f"Position obtenue: {st.session_state.current_location['lat']:.6f}, {st.session_state.current_location['lon']:.6f}")
    
    # Boutons de contrôle de la course
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Commencer", disabled=st.session_state.running):
            if st.session_state.current_location is None:
                st.error("La localisation n'est pas disponible. Veuillez cliquer sur 'Obtenir ma localisation'.")
            else:
                st.session_state.running = True
                st.session_state.start_time = time.time()
                st.session_state.last_timestamp = st.session_state.start_time
                st.session_state.trajectory = [st.session_state.current_location.copy() | {"timestamp": st.session_state.start_time}]
                st.session_state.speeds = [(st.session_state.start_time, 0.0)]
    with col2:
        if st.button("Arrêter", disabled=not st.session_state.running):
            st.session_state.running = False

    # Rafraîchissement automatique seulement si course en cours
    if st.session_state.running:
        st_autorefresh(interval=2000, limit=None, key="map_autorefresh")

    # Mise à jour en temps réel de la trajectoire et de la vitesse
    if st.session_state.running and st.session_state.current_location is not None:
        new_lat = st.session_state.current_location["lat"]
        new_lon = st.session_state.current_location["lon"]
        now = time.time()
        dt = now - st.session_state.last_timestamp
        if dt < 0.1:
            dt = 0.1  # Pour éviter la division par zéro
        last_point = st.session_state.trajectory[-1]
        distance = haversine(last_point["lat"], last_point["lon"], new_lat, new_lon)
        speed_kmh = (distance / dt) * 3.6
        st.session_state.trajectory.append({"lat": new_lat, "lon": new_lon, "timestamp": now})
        st.session_state.speeds.append((now, speed_kmh))
        st.session_state.last_timestamp = now

    # Affichage du chronomètre
    if st.session_state.running:
        elapsed = time.time() - st.session_state.start_time
        m, s = divmod(int(elapsed), 60)
        st.write(f"**Temps écoulé :** {m:02d}:{s:02d}")
    else:
        if st.session_state.speeds:
            total_sec = st.session_state.speeds[-1][0] - st.session_state.start_time
            m, s = divmod(int(total_sec), 60)
            st.write(f"**Course terminée - Temps total :** {m:02d}:{s:02d}")

    # Affichage de la carte avec PyDeck
    if st.session_state.trajectory:
        df_points = pd.DataFrame(st.session_state.trajectory)
        line_data = []
        for i in range(len(df_points) - 1):
            p1 = df_points.iloc[i]
            p2 = df_points.iloc[i+1]
            line_data.append([[p1["lon"], p1["lat"]], [p2["lon"], p2["lat"]]])
        line_layer = pdk.Layer(
            "PathLayer",
            data=line_data,
            get_path="object",
            get_width=5,
            width_min_pixels=2,
            get_color=[255, 0, 0],
            pickable=True
        )
        point_layer = pdk.Layer(
            "ScatterplotLayer",
            data=df_points,
            get_position=["lon", "lat"],
            get_color=[0, 128, 255],
            get_radius=30,
        )
        last_point = df_points.iloc[-1]
        view_state = pdk.ViewState(
            longitude=last_point["lon"],
            latitude=last_point["lat"],
            zoom=15
        )
        deck = pdk.Deck(
            layers=[line_layer, point_layer],
            initial_view_state=view_state,
            map_style="mapbox://styles/mapbox/streets-v11"
        )
        st.pydeck_chart(deck)

    # Graphique de vitesse
    if st.session_state.speeds:
        df_speed = pd.DataFrame(st.session_state.speeds, columns=["timestamp", "speed_kmh"])
        df_speed["time"] = df_speed["timestamp"].apply(lambda t: datetime.datetime.fromtimestamp(t).strftime("%H:%M:%S"))
        df_speed.set_index("time", inplace=True)
        st.line_chart(df_speed["speed_kmh"])
        st.write("Évolution de la vitesse (km/h).")
