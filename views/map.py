# views/map.py

import streamlit as st
import time
import math
import pydeck as pdk
import datetime
import pandas as pd

from streamlit_autorefresh import st_autorefresh

# Fonction de distance
def haversine(lat1, lon1, lat2, lon2):
    R = 6371e3  # mètres
    def rad(deg): return math.radians(deg)
    dlat = rad(lat2 - lat1)
    dlon = rad(lon2 - lon1)
    a = (math.sin(dlat/2)**2 +
         math.cos(rad(lat1))*math.cos(rad(lat2))*math.sin(dlon/2)**2)
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R*c  # en mètres

def display_map_page():
    st.title("Activité de Course - Suivi en Temps Réel (Auto-Refresh)")

    # Vérifier connexion utilisateur
    if 'user_id' not in st.session_state:
        st.error("Veuillez vous connecter pour accéder à la carte.")
        return

    # Initialiser les variables en session_state
    if 'running' not in st.session_state:
        st.session_state.running = False
    if 'start_time' not in st.session_state:
        st.session_state.start_time = 0.0
    if 'trajectory' not in st.session_state:
        st.session_state.trajectory = []  # liste de dict {lat, lon, timestamp}
    if 'speeds' not in st.session_state:
        st.session_state.speeds = []      # liste de (timestamp, speed_kmh)

    # Barre de refresh automatique : toutes les 2 secondes
    # => la variable "count" s’incrémente à chaque refresh
    count = st_autorefresh(interval=2000, limit=None, key="map_autorefresh_counter")

    # Boutons de contrôle
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Commencer", disabled=st.session_state.running):
            st.session_state.running = True
            st.session_state.start_time = time.time()
            st.session_state.trajectory.clear()
            st.session_state.speeds.clear()

    with col2:
        if st.button("Arrêter", disabled=not st.session_state.running):
            st.session_state.running = False

    # Afficher le chrono si running
    if st.session_state.running:
        elapsed = time.time() - st.session_state.start_time
        m, s = divmod(int(elapsed), 60)
        st.write(f"**Temps écoulé :** {m:02d}:{s:02d}")

        # Simulation de la position
        if len(st.session_state.trajectory) == 0:
            # Point de départ (Paris)
            lat0, lon0 = 48.8566, 2.3522
        else:
            lat0 = st.session_state.trajectory[-1]["lat"]
            lon0 = st.session_state.trajectory[-1]["lon"]

        # Déplacement fictif de 0.0001° par "refresh"
        lat_new = lat0 + 0.0001
        lon_new = lon0

        # Calculer la vitesse (distance / temps)
        if len(st.session_state.trajectory) > 0:
            # distance en m depuis le dernier point
            dist_m = haversine(lat0, lon0, lat_new, lon_new)
            # On suppose 2 secondes entre deux refresh => dt=2
            # (Vous pouvez affiner si vous stockez le timestamp précédent)
            dt = 2
            speed_m_s = dist_m / dt
            speed_kmh = speed_m_s * 3.6
        else:
            speed_kmh = 0.0

        # Stocker la position + vitesse
        st.session_state.trajectory.append({"lat": lat_new, "lon": lon_new, "timestamp": time.time()})
        st.session_state.speeds.append((time.time(), speed_kmh))

    else:
        # Si l'activité n'est pas en cours => afficher un résumé si speeds existe
        if st.session_state.speeds:
            total_sec = st.session_state.speeds[-1][0] - st.session_state.start_time
            m, s = divmod(int(total_sec), 60)
            st.write(f"Activité terminée - Temps total : {m:02d}:{s:02d}")

    # Afficher la trajectoire sur la carte
    if st.session_state.trajectory:
        df_points = pd.DataFrame(st.session_state.trajectory)
        # Path
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
        # Points
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
