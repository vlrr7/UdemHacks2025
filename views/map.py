# views/map.py

import streamlit as st
import time
import pandas as pd
import datetime

def display_map_page():
    st.title("Entraînement sur Carte")
    st.write("""
    Sur cette page, vous pouvez suivre votre course sur une carte, 
    afficher vos données de vitesse, fréquence cardiaque cible, 
    VO2 max, etc., ainsi qu'utiliser un chronomètre pour mesurer 
    votre performance en temps réel.
    """)

    # --- 1) Coordonnées GPS ---
    st.subheader("Localisation GPS")
    # Par défaut, on centre la carte sur Paris (lat=48.8566, lon=2.3522) par exemple
    lat = st.number_input("Latitude", value=48.8566, format="%.6f")
    lon = st.number_input("Longitude", value=2.3522, format="%.6f")

    # DataFrame minimal pour st.map()
    map_data = pd.DataFrame({"lat": [lat], "lon": [lon]})
    st.map(map_data)

    # --- 2) Saisie / Simulation des données en direct ---
    st.subheader("Données en direct")
    speed = st.number_input("Vitesse (km/h)", min_value=0.0, value=10.0, step=0.1)
    heart_rate = st.number_input("Fréquence cardiaque (bpm)", min_value=40, max_value=220, value=120)
    
    # Calcul d'une FC cible ou VO2max simple (exemple) :
    #  - FC max théorique ~ 220 - âge
    #  - VO2max (exemple simplifié) = 15.3 * (FCmax / FC repos)
    #  - Seuil anaérobie ~ 85% de FC max
    age = st.number_input("Âge (ans)", min_value=1, max_value=120, value=30)
    fc_max = 220 - age
    fc_cible = 0.7 * fc_max  # 70% en exemple
    st.write(f"FC max théorique : {fc_max:.0f} bpm")
    st.write(f"FC cible (~70% FC max) : {fc_cible:.0f} bpm")
    
    # --- 3) Chronomètre ---
    st.subheader("Chronomètre")
    if "start_time" not in st.session_state:
        st.session_state.start_time = None
    if "elapsed" not in st.session_state:
        st.session_state.elapsed = 0.0

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Démarrer"):
            st.session_state.start_time = time.time()
        if st.button("Arrêter"):
            if st.session_state.start_time:
                st.session_state.elapsed += time.time() - st.session_state.start_time
                st.session_state.start_time = None
    with col2:
        if st.button("Remettre à zéro"):
            st.session_state.start_time = None
            st.session_state.elapsed = 0.0

    # Calcul du temps écoulé si le chrono est en cours
    if st.session_state.start_time:
        current_elapsed = (time.time() - st.session_state.start_time) + st.session_state.elapsed
    else:
        current_elapsed = st.session_state.elapsed

    # Formatage du temps écoulé en mm:ss
    minutes, seconds = divmod(int(current_elapsed), 60)
    st.write(f"Temps écoulé : **{minutes:02d}:{seconds:02d}**")

    # --- 4) Historique de la vitesse pour le graphique ---
    # On peut stocker la vitesse courante à chaque "run" dans st.session_state
    if "speed_history" not in st.session_state:
        st.session_state.speed_history = []
    if st.button("Enregistrer la vitesse"):
        # On enregistre un tuple (timestamp, speed)
        st.session_state.speed_history.append((datetime.datetime.now(), speed))
        st.success("Vitesse ajoutée à l'historique.")

    # Affichage du graphique
    if st.session_state.speed_history:
        df_speed = pd.DataFrame(st.session_state.speed_history, columns=["time", "speed"])
        df_speed = df_speed.set_index("time")
        st.line_chart(df_speed["speed"], height=200)
        st.write("Évolution de la vitesse (km/h) dans le temps.")

    # --- 5) Intégration potentielle avec la base de données ---
    # Vous pouvez stocker la localisation, la vitesse et les autres données
    # dans une collection "training_sessions" pour un historique plus complet.
    # Ce code n'est pas obligatoire, c'est juste une piste :
    # if st.button("Enregistrer la session dans la base"):
    #     training_session = {
    #         "user_id": st.session_state['user_id'],
    #         "timestamp": datetime.datetime.now(),
    #         "lat": lat,
    #         "lon": lon,
    #         "speed_history": st.session_state.speed_history,
    #         "heart_rate": heart_rate,
    #         "fc_cible": fc_cible,
    #         ...
    #     }
    #     training_sessions_collection.insert_one(training_session)
    #     st.success("Session enregistrée.")
