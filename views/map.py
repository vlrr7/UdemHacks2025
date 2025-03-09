# views/map.py

import streamlit as st
import time
import math
import pydeck as pdk
import datetime
import pandas as pd

from streamlit_autorefresh import st_autorefresh

def haversine(lat1, lon1, lat2, lon2):
    """Calcule la distance (en mètres) entre deux points (lat, lon)."""
    R = 6371e3
    def rad(deg): return math.radians(deg)
    dlat = rad(lat2 - lat1)
    dlon = rad(lon2 - lon1)
    a = (math.sin(dlat/2)**2 +
         math.cos(rad(lat1))*math.cos(rad(lat2))*math.sin(dlon/2)**2)
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R*c

def display_map_page():
    st.title("Course : Localisation et Chronomètre en Temps Réel")

    # Vérifier connexion
    if 'user_id' not in st.session_state:
        st.error("Veuillez vous connecter pour accéder à la carte.")
        return

    # Initialisations
    if 'running' not in st.session_state:
        st.session_state.running = False
    if 'start_time' not in st.session_state:
        st.session_state.start_time = 0.0
    if 'trajectory' not in st.session_state:
        st.session_state.trajectory = []  # [{lat, lon, timestamp}]
    if 'speeds' not in st.session_state:
        st.session_state.speeds = []      # [(timestamp, speed_kmh)]
    if 'last_timestamp' not in st.session_state:
        st.session_state.last_timestamp = 0.0

    # Permet un rafraîchissement toutes les 2 secondes
    # seulement si on est en mode "running"
    if st.session_state.running:
        count = st_autorefresh(interval=2000, limit=None, key="map_autorefresh_counter")
    else:
        # Pas de refresh automatique si on n'est pas en course
        pass

    # Boutons Démarrer / Arrêter
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Commencer", disabled=st.session_state.running):
            st.session_state.running = True
            st.session_state.start_time = time.time()
            st.session_state.last_timestamp = st.session_state.start_time
            st.session_state.trajectory.clear()
            st.session_state.speeds.clear()

    with col2:
        if st.button("Arrêter", disabled=not st.session_state.running):
            st.session_state.running = False

    # Champs manuels pour la position
    st.subheader("Localisation actuelle")
    # Par défaut, si on n'a pas de points, on affiche Paris
    if len(st.session_state.trajectory) == 0:
        default_lat, default_lon = 48.8566, 2.3522
    else:
        default_lat = st.session_state.trajectory[-1]["lat"]
        default_lon = st.session_state.trajectory[-1]["lon"]

    lat_input = st.number_input("Latitude", value=default_lat, format="%.6f")
    lon_input = st.number_input("Longitude", value=default_lon, format="%.6f")

    # Afficher un bouton "Mettre à jour la position" (optionnel)
    if st.button("Mettre à jour la position"):
        # On ajoute un nouveau point seulement si running = True
        # ou si c'est le premier point
        if st.session_state.running or len(st.session_state.trajectory) == 0:
            add_new_point(lat_input, lon_input)
        else:
            st.info("La course n'est pas démarrée, la position reste affichée mais n'affecte pas la vitesse.")

    # Chronomètre
    if st.session_state.running:
        elapsed = time.time() - st.session_state.start_time
        m, s = divmod(int(elapsed), 60)
        st.write(f"**Temps écoulé :** {m:02d}:{s:02d}")
    else:
        # Course arrêtée => si on a un historique, on affiche la durée finale
        if st.session_state.speeds:
            total_sec = st.session_state.speeds[-1][0] - st.session_state.start_time
            m, s = divmod(int(total_sec), 60)
            st.write(f"Course terminée - Durée : {m:02d}:{s:02d}")

    # Affichage carte PyDeck
    display_map_and_speed_chart()


def add_new_point(lat_new, lon_new):
    """
    Ajoute un nouveau point (lat_new, lon_new) au 'trajectory' 
    et calcule la vitesse en fonction du point précédent.
    """
    import time

    now_ts = time.time()
    if len(st.session_state.trajectory) == 0:
        # Premier point => vitesse = 0
        st.session_state.trajectory.append({
            "lat": lat_new,
            "lon": lon_new,
            "timestamp": now_ts
        })
        st.session_state.speeds.append((now_ts, 0.0))
        st.session_state.last_timestamp = now_ts
    else:
        # Comparer au dernier point
        last_pt = st.session_state.trajectory[-1]
        dist_m = haversine(last_pt["lat"], last_pt["lon"], lat_new, lon_new)
        dt = now_ts - st.session_state.last_timestamp
        if dt < 0.1:
            dt = 0.1  # pour éviter une division par 0 si trop rapide
        speed_m_s = dist_m / dt
        speed_kmh = speed_m_s * 3.6

        st.session_state.trajectory.append({
            "lat": lat_new,
            "lon": lon_new,
            "timestamp": now_ts
        })
        st.session_state.speeds.append((now_ts, speed_kmh))
        st.session_state.last_timestamp = now_ts


def display_map_and_speed_chart():
    """Affiche la carte PyDeck + le graphique de vitesse, qu'on soit running ou pas."""
    if st.session_state.trajectory:
        df_points = pd.DataFrame(st.session_state.trajectory)
        # Créer la "ligne" du parcours
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
            zoom=14
        )

        r = pdk.Deck(
            layers=[line_layer, point_layer],
            initial_view_state=view_state,
            map_style="mapbox://styles/mapbox/streets-v11"
        )
        st.pydeck_chart(r)

    # Graphique de vitesse
    if st.session_state.speeds:
        df_speeds = pd.DataFrame(st.session_state.speeds, columns=["timestamp", "speed_kmh"])
        df_speeds["time"] = df_speeds["timestamp"].apply(
            lambda t: datetime.datetime.fromtimestamp(t).strftime("%H:%M:%S")
        )
        df_speeds.set_index("time", inplace=True)
        st.line_chart(df_speeds["speed_kmh"])
        st.write("Évolution de la vitesse (km/h).")
