# views/map.py

import streamlit as st
import time
import math
import pydeck as pdk
import datetime

def haversine(lat1, lon1, lat2, lon2):
    R = 6371e3
    phi1, phi2 = map(math.radians, [lat1, lat2])
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (math.sin(dphi/2)**2 +
         math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2)
    return R * 2*math.atan2(math.sqrt(a), math.sqrt(1-a))  # en mètres

def display_map_page():
    st.title("Activité de Course - Suivi en Temps Réel (version Timer)")
    
    if 'user_id' not in st.session_state:
        st.error("Veuillez vous connecter pour accéder à la carte.")
        return
    
    # Initialisation
    if 'running' not in st.session_state:
        st.session_state.running = False
    if 'start_time' not in st.session_state:
        st.session_state.start_time = 0
    if 'trajectory' not in st.session_state:
        st.session_state.trajectory = []
    if 'speeds' not in st.session_state:
        st.session_state.speeds = []
    if 'last_update' not in st.session_state:
        st.session_state.last_update = 0.0  # Pour gérer le refresh

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

    # Affichage du chrono
    if st.session_state.running:
        elapsed_sec = time.time() - st.session_state.start_time
        m, s = divmod(int(elapsed_sec), 60)
        st.write(f"**Temps écoulé** : {m:02d}:{s:02d}")

        # Simuler la localisation + calculer vitesse
        if len(st.session_state.trajectory) == 0:
            lat0, lon0 = 48.8566, 2.3522
        else:
            lat0 = st.session_state.trajectory[-1]["lat"]
            lon0 = st.session_state.trajectory[-1]["lon"]
        lat_new = lat0 + 0.0001  # Simulation
        lon_new = lon0

        dist_m = 0
        speed_kmh = 0
        if len(st.session_state.trajectory) > 0:
            dist_m = haversine(lat0, lon0, lat_new, lon_new)
            speed_kmh = (dist_m * 3.6)  # Sur 1 seconde => simplification

        st.session_state.trajectory.append({
            "lat": lat_new,
            "lon": lon_new,
            "timestamp": time.time()
        })
        st.session_state.speeds.append((time.time(), speed_kmh))

        # On rafraîchit la page seulement toutes les 2 secondes
        now = time.time()
        if now - st.session_state.last_update > 2:
            st.session_state.last_update = now
            st.experimental_rerun()

    else:
        # Activité terminée ?
        if st.session_state.speeds:
            total_sec = st.session_state.speeds[-1][0] - st.session_state.start_time
            m, s = divmod(int(total_sec), 60)
            st.write(f"Activité terminée - Temps total : {m:02d}:{s:02d}")

    # Affichage de la map
    if st.session_state.trajectory:
        import pandas as pd
        df_points = pd.DataFrame(st.session_state.trajectory)
        # PathLayer
        line_data = []
        for i in range(len(df_points) - 1):
            p1 = df_points.iloc[i]
            p2 = df_points.iloc[i+1]
            line_data.append([[p1["lon"], p1["lat"]], [p2["lon"], p2["lat"]]])
        line_layer = pdk.Layer(
            "PathLayer",
            line_data,
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
        r = pdk.Deck(
            layers=[line_layer, point_layer],
            initial_view_state=view_state,
            map_style="mapbox://styles/mapbox/streets-v11"
        )
        st.pydeck_chart(r)

    # Graphique de vitesse
    if st.session_state.speeds:
        import pandas as pd
        df_speeds = pd.DataFrame(st.session_state.speeds, columns=["timestamp", "speed_kmh"])
        df_speeds["time"] = df_speeds["timestamp"].apply(
            lambda t: datetime.datetime.fromtimestamp(t).strftime("%H:%M:%S")
        )
        df_speeds.set_index("time", inplace=True)
        st.line_chart(df_speeds["speed_kmh"])
        st.write("Évolution de la vitesse (km/h).")
