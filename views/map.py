# views/map.py

import streamlit as st
import time
import math
import pydeck as pdk
import datetime

# --- Pour calculer la distance entre deux points (lat, lon) ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6371e3  # Rayon de la Terre en mètres
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (math.sin(dphi/2)**2 +
         math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2)
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c  # distance en mètres

def display_map_page():
    st.title("Activité de Course - Suivi en Temps Réel")

    # 1) Récupérer les infos de l'utilisateur depuis la base
    # (Ici, on suppose que vous avez déjà st.session_state['user_id'] et une fonction
    #  pour récupérer le profil complet, y compris l'âge, la VO2max, etc. 
    #  Ex: user_profile = get_user_profile(st.session_state['user_id']) )
    if 'user_id' not in st.session_state:
        st.error("Veuillez vous connecter pour accéder à la carte.")
        return
    # user_profile = get_user_profile(st.session_state['user_id'])  # Pseudo-code

    # 2) Initialiser les variables de session
    if 'running' not in st.session_state:
        st.session_state.running = False
    if 'start_time' not in st.session_state:
        st.session_state.start_time = 0
    if 'trajectory' not in st.session_state:
        # Liste de dicts : [{lat, lon, timestamp}, ...]
        st.session_state.trajectory = []
    if 'speeds' not in st.session_state:
        # Liste de (timestamp, speed_kmh)
        st.session_state.speeds = []

    # 3) Boutons pour démarrer / arrêter
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Commencer", disabled=st.session_state.running):
            st.session_state.running = True
            st.session_state.start_time = time.time()
            st.session_state.trajectory.clear()
            st.session_state.speeds.clear()
            st.experimental_rerun()

    with col2:
        if st.button("Arrêter", disabled=not st.session_state.running):
            st.session_state.running = False
            st.experimental_rerun()

    # 4) Si on est en mode “running”, on met à jour en temps réel
    if st.session_state.running:
        # Chronomètre
        elapsed_sec = time.time() - st.session_state.start_time
        minutes, seconds = divmod(int(elapsed_sec), 60)
        st.write(f"**Temps écoulé** : {minutes:02d}:{seconds:02d}")

        # Simuler ou récupérer la position en temps réel
        # ------------------------------------------------
        # Pour l'exemple, on va juste faire bouger la latitude
        # d'environ 0.0001 degrés par seconde.
        # Remplacez ceci par votre code de géolocalisation réel.
        if len(st.session_state.trajectory) == 0:
            # Point de départ
            lat0, lon0 = 48.8566, 2.3522  # Paris
        else:
            lat0 = st.session_state.trajectory[-1]['lat']
            lon0 = st.session_state.trajectory[-1]['lon']

        # Calcul d'un petit déplacement (ex: 0.0001° en latitude)
        # en fonction du temps écoulé (ex: 1 point par "run").
        lat_new = lat0 + 0.0001
        lon_new = lon0

        # Calcul de la distance (en mètres) + vitesse
        if len(st.session_state.trajectory) > 0:
            dist_m = haversine(lat0, lon0, lat_new, lon_new)
            dt = 1  # On suppose 1 seconde entre 2 runs => simplification
            speed_ms = dist_m / dt  # m/s
            speed_kmh = speed_ms * 3.6
        else:
            speed_kmh = 0.0

        # Enregistrer le nouveau point
        st.session_state.trajectory.append({
            "lat": lat_new,
            "lon": lon_new,
            "timestamp": time.time()
        })
        # Enregistrer la vitesse
        st.session_state.speeds.append((time.time(), speed_kmh))

        # Forcer un re-run après 1 seconde pour actualiser
        st.experimental_rerun()

    # 5) Afficher le chronomètre si non-running
    if not st.session_state.running and st.session_state.start_time > 0:
        total_sec = st.session_state.speeds[-1][0] - st.session_state.start_time if st.session_state.speeds else 0
        minutes, seconds = divmod(int(total_sec), 60)
        st.write(f"**Activité terminée** - Temps total : {minutes:02d}:{seconds:02d}")

    # 6) Affichage de la carte (PyDeck) avec la trajectoire
    if len(st.session_state.trajectory) > 0:
        # DataFrame des points
        import pandas as pd
        df_points = pd.DataFrame(st.session_state.trajectory)

        # Couche "trajet" => line_layer
        # On doit transformer la liste des points en segments
        # simple : on dessine un polygone reliant les points
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

        # Couche "points"
        point_layer = pdk.Layer(
            "ScatterplotLayer",
            data=df_points,
            get_position=["lon", "lat"],
            get_color=[0, 128, 255],
            get_radius=30,
        )

        # Définir la vue (centrée sur le dernier point)
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

    # 7) Afficher le graphique de vitesse
    if len(st.session_state.speeds) > 0:
        import pandas as pd
        df_speeds = pd.DataFrame(st.session_state.speeds, columns=["timestamp", "speed_kmh"])
        df_speeds["time"] = df_speeds["timestamp"].apply(
            lambda t: datetime.datetime.fromtimestamp(t).strftime("%H:%M:%S")
        )
        df_speeds.set_index("time", inplace=True)
        st.line_chart(df_speeds["speed_kmh"], height=200)
        st.write("Évolution de la vitesse (km/h).")
