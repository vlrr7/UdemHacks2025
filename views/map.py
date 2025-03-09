# views/map.py

import streamlit as st
import time
import math
import pydeck as pdk
import datetime
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# Fonction de calcul de la distance (en mètres) entre deux points via la formule haversine
def haversine(lat1, lon1, lat2, lon2):
    R = 6371e3  # Rayon de la Terre en mètres
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def display_map_page():
    st.title("Course en Temps Réel")

    # Vérification de la connexion utilisateur
    if 'user_id' not in st.session_state:
        st.error("Veuillez vous connecter pour accéder à la carte.")
        return

    # Initialisations dans st.session_state
    if 'running' not in st.session_state:
        st.session_state.running = False
    if 'start_time' not in st.session_state:
        st.session_state.start_time = 0.0
    if 'trajectory' not in st.session_state:
        st.session_state.trajectory = []  # Liste des points {lat, lon, timestamp}
    if 'speeds' not in st.session_state:
        st.session_state.speeds = []      # Liste des tuples (timestamp, speed_kmh)

    # Affichage de la géolocalisation en temps réel via get_position
    location = None # get_position("Veuillez autoriser l'accès à votre localisation")
    if location is None:
        st.warning("En attente de la localisation...")
        return  # On quitte tant qu'on n'a pas la position
    else:
        current_lat = location.get("latitude")
        current_lon = location.get("longitude")
        st.write(f"Votre position actuelle : {current_lat:.6f}, {current_lon:.6f}")

    # Boutons pour démarrer/arrêter la course
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Commencer", disabled=st.session_state.running):
            st.session_state.running = True
            st.session_state.start_time = time.time()
            st.session_state.trajectory = [{"lat": current_lat, "lon": current_lon, "timestamp": time.time()}]
            st.session_state.speeds = [(time.time(), 0.0)]
    with col2:
        if st.button("Arrêter", disabled=not st.session_state.running):
            st.session_state.running = False

    # Rafraîchissement automatique de la page si la course est en cours (toutes les 2 secondes)
    if st.session_state.running:
        st_autorefresh(interval=2000, limit=None, key="map_autorefresh")

    # Mise à jour de la trajectoire et calcul de la vitesse
    if st.session_state.running:
        # Si la position a changé (vérifier que la nouvelle position diffère du dernier point)
        last_point = st.session_state.trajectory[-1]
        if abs(current_lat - last_point["lat"]) > 1e-6 or abs(current_lon - last_point["lon"]) > 1e-6:
            now = time.time()
            dt = now - last_point["timestamp"]
            if dt <= 0:
                dt = 1  # pour éviter la division par zéro
            distance = haversine(last_point["lat"], last_point["lon"], current_lat, current_lon)
            speed_m_s = distance / dt
            speed_kmh = speed_m_s * 3.6
            st.session_state.trajectory.append({"lat": current_lat, "lon": current_lon, "timestamp": now})
            st.session_state.speeds.append((now, speed_kmh))
        else:
            speed_kmh = st.session_state.speeds[-1][1]  # Pas de changement, vitesse inchangée

    # Chronomètre
    if st.session_state.running:
        elapsed = time.time() - st.session_state.start_time
        m, s = divmod(int(elapsed), 60)
        st.write(f"**Temps écoulé :** {m:02d}:{s:02d}")
    else:
        if st.session_state.speeds:
            total_time = st.session_state.speeds[-1][0] - st.session_state.start_time
            m, s = divmod(int(total_time), 60)
            st.write(f"**Course terminée - Temps total :** {m:02d}:{s:02d}")

    # Affichage de la carte avec PyDeck
    if st.session_state.trajectory:
        df_points = pd.DataFrame(st.session_state.trajectory)
        # Créer une liste de segments pour tracer la trajectoire
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
