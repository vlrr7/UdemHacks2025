# views/map.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import time
from database import DataEntry, User
import pydeck as pdk

def calculate_target_heart_rate(age):
    max_hr = 220 - age
    return {
        'vo2max_zone': 0.85 * max_hr,
        'anaerobic_threshold': 0.90 * max_hr,
        'moderate': 0.70 * max_hr
    }

def display_map_page():
    st.title("Running Tracker")
    
    if 'user_id' not in st.session_state:
        st.error("Veuillez vous connecter")
        return
    
    user_id = st.session_state['user_id']
    user_data = User.find_by_id(user_id)
    
    # Section configuration
    with st.expander("Configuration de la séance"):
        age = st.number_input("Âge", value=user_data.get('age', 25))
        target_type = st.selectbox("Type d'entraînement", 
                                ["VO2Max", "Seuil anaérobique", "Modéré"])
    
    # Calcul des cibles
    heart_rates = calculate_target_heart_rate(age)
    
    # Initialisation des données de session
    if 'run_data' not in st.session_state:
        st.session_state.run_data = {
            'timestamps': [],
            'speeds': [],
            'heart_rates': [],
            'positions': []
        }
        st.session_state.run_start = None
        st.session_state.elapsed = 0
    
    # Contrôles de la course
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Démarrer la course"):
            st.session_state.run_start = time.time()
    with col2:
        if st.button("Arrêter"):
            st.session_state.run_start = None
    with col3:
        if st.button("Réinitialiser"):
            st.session_state.run_data = {'timestamps': [], 'speeds': [], 'heart_rates': [], 'positions': []}
            st.session_state.elapsed = 0

    # Simulation de données (à remplacer par données réelles)
    if st.session_state.run_start:
        try:
            gps_data = st.experimental_get_query_params()
            lat = float(gps_data.get('lat', [0])[0])
            lon = float(gps_data.get('lon', [0])[0])
            new_position = [lat, lon]
        except:
            new_position = [48.8566, 2.3522]  # Fallback Paris
        

        # Génération de données simulées
        new_data = {
            'timestamp': datetime.now(),
            'speed': np.random.uniform(10, 15),  # km/h
            'heart_rate': np.random.randint(120, 190),
            'position': [
                np.random.uniform(-0.0001, 0.0001) + 48.8566,  # Latitude 
                np.random.uniform(-0.0001, 0.0001) + 2.3522     # Longitude
            ]
        }
        
        st.session_state.run_data['timestamps'].append(new_data['timestamp'])
        st.session_state.run_data['speeds'].append(new_data['speed'])
        st.session_state.run_data['heart_rates'].append(new_data['heart_rate'])
        st.session_state.run_data['positions'].append(new_data['position'])

    # Affichage des métriques
    if st.session_state.run_data['speeds']:
        current_speed = st.session_state.run_data['speeds'][-1]
        current_hr = st.session_state.run_data['heart_rates'][-1]
    else:
        current_speed = 0
        current_hr = 0

    metric_cols = st.columns(4)
    metric_cols[0].metric("Temps", f"{int(st.session_state.elapsed // 60)}:{int(st.session_state.elapsed % 60):02d}")
    metric_cols[1].metric("Vitesse (km/h)", f"{current_speed:.1f}")
    metric_cols[2].metric("FC Actuelle", f"{current_hr} bpm")
    metric_cols[3].metric("Cible FC", f"{heart_rates[target_type.lower()]:.0f} bpm")

    # Carte PyDeck
    if st.session_state.run_data['positions']:
        df = pd.DataFrame({
            'lat': [pos[0] for pos in st.session_state.run_data['positions']],
            'lon': [pos[1] for pos in st.session_state.run_data['positions']]
        })

        layer = pdk.Layer(
            'ScatterplotLayer',
            data=df,
            get_position='[lon, lat]',
            get_color='[200, 30, 0, 160]',
            get_radius=20,
        )

        view_state = pdk.ViewState(
            latitude=df['lat'].mean(),
            longitude=df['lon'].mean(),
            zoom=14,
            pitch=50
        )

        st.pydeck_chart(pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            map_style='mapbox://styles/mapbox/outdoors-v11'
        ))

    # Graphiques
    if st.session_state.run_data['speeds']:
        st.line_chart(pd.DataFrame({
            'Vitesse (km/h)': st.session_state.run_data['speeds'],
            'Fréquence cardiaque': st.session_state.run_data['heart_rates']
        }))