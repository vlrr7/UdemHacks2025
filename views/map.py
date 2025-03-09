# views/map.py
import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime
import pydeck as pdk
from streamlit.components.v1 import html
from streamlit_autorefresh import st_autorefresh
from database import User

def calculate_target_heart_rate(age):
    max_hr = 220 - age
    return {
        'vo2max': 0.85 * max_hr,
        'seuil anaérobique': 0.90 * max_hr,
        'modéré': 0.70 * max_hr
    }

def display_map_page():
    st.title("🏃♂️ Running Tracker")

    # Auto-refresh toutes les 5 secondes pour simuler une actualisation en temps réel
    st_autorefresh(interval=5000, key="datarefresh")

    # Injection d'un bouton HTML personnalisé et du code JavaScript associé
    html("""
    <button id="start-tracking" style="padding:10px;font-size:16px;">🚩 Démarrer la course (JS)</button>
    <script>
    function startTracking() {
        console.log("Bouton cliqué, demande de géolocalisation lancée");
        if (!navigator.geolocation) {
            alert("La géolocalisation n'est pas supportée par ce navigateur.");
            return;
        }
        navigator.geolocation.watchPosition(
            function(position) {
                const params = new URLSearchParams(window.location.search);
                params.set('lat', position.coords.latitude);
                params.set('lon', position.coords.longitude);
                window.history.replaceState({}, '', `${location.pathname}?${params}`);
                console.log("Position mise à jour:", position.coords);
            },
            function(error) {
                console.error('Erreur de géolocalisation:', error);
            },
            {
                enableHighAccuracy: true,
                maximumAge: 0,
                timeout: 5000
            }
        );
    }
    document.getElementById("start-tracking").addEventListener("click", startTracking);
    </script>
    """, height=150)

    # Vérification de la connexion utilisateur
    if 'user_id' not in st.session_state:
        st.error("Veuillez vous connecter")
        return

    user_id = st.session_state['user_id']
    user_data = User.find_by_id(user_id)

    # Configuration de la séance
    with st.expander("⚙️ Configuration de la séance"):
        age = st.number_input("Âge", value=user_data.get('age', 25))
        target_type = st.selectbox("Type d'entraînement", ["VO2Max", "Seuil anaérobique", "Modéré"])

    heart_rates = calculate_target_heart_rate(age)

    # Initialisation des données de la course
    if 'run_data' not in st.session_state:
        st.session_state.run_data = {
            'timestamps': [],
            'speeds': [],
            'heart_rates': [],
            'positions': []
        }
        st.session_state.run_start = None
        st.session_state.elapsed = 0

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🚩 Démarrer la course", key='demarrer-course-py'):
            st.session_state.run_start = time.time()
    with col2:
        if st.button("⏹️ Arrêter"):
            st.session_state.run_start = None
    with col3:
        if st.button("🔄 Réinitialiser"):
            st.session_state.run_data = {
                'timestamps': [],
                'speeds': [],
                'heart_rates': [],
                'positions': []
            }
            st.session_state.elapsed = 0

    # Mise à jour des données de localisation si la course est en cours
    if st.session_state.run_start:
        elapsed = time.time() - st.session_state.run_start
        st.session_state.elapsed = elapsed

        # Utilisation de la nouvelle API stable st.query_params (propriété, sans parenthèses)
        query_params = st.query_params
        try:
            lat = float(query_params.get('lat', [48.8566])[0])
            lon = float(query_params.get('lon', [2.3522])[0])
            new_position = [lat, lon]
            if lat == 48.8566 and lon == 2.3522:
                st.info("🔍 Recherche du signal GPS...")
        except Exception as e:
            st.error(f"Erreur GPS: {str(e)}")
            new_position = [48.8566, 2.3522]

        new_data = {
            'timestamp': datetime.now(),
            'speed': np.random.uniform(10, 15),
            'heart_rate': np.random.randint(120, 190),
            'position': new_position
        }
        st.session_state.run_data['timestamps'].append(new_data['timestamp'])
        st.session_state.run_data['speeds'].append(new_data['speed'])
        st.session_state.run_data['heart_rates'].append(new_data['heart_rate'])
        st.session_state.run_data['positions'].append(new_data['position'])

    current_speed = st.session_state.run_data['speeds'][-1] if st.session_state.run_data['speeds'] else 0
    current_hr = st.session_state.run_data['heart_rates'][-1] if st.session_state.run_data['heart_rates'] else 0

    with st.container():
        cols = st.columns(4)
        cols[0].metric("⏱️ Temps", f"{int(st.session_state.elapsed // 60)}:{int(st.session_state.elapsed % 60):02d}")
        cols[1].metric("📈 Vitesse", f"{current_speed:.1f} km/h")
        cols[2].metric("💓 FC Actuelle", f"{current_hr} bpm")
        cols[3].metric("🎯 Cible FC", f"{heart_rates[target_type.lower()]:.0f} bpm")

    if st.session_state.run_data['positions']:
        df = pd.DataFrame({
            'lat': [pos[0] for pos in st.session_state.run_data['positions']],
            'lon': [pos[1] for pos in st.session_state.run_data['positions']]
        })

        st.pydeck_chart(pdk.Deck(
            map_style='mapbox://styles/mapbox/outdoors-v11',
            initial_view_state=pdk.ViewState(
                latitude=df['lat'].mean(),
                longitude=df['lon'].mean(),
                zoom=14,
                pitch=50
            ),
            layers=[
                pdk.Layer(
                    'ScatterplotLayer',
                    data=df,
                    get_position='[lon, lat]',
                    get_color='[200, 30, 0, 160]',
                    get_radius=20,
                )
            ]
        ))
    else:
        st.info("🗺️ La carte s'affichera ici dès la réception des données GPS")

    if st.session_state.run_data['speeds']:
        st.line_chart(pd.DataFrame({
            'Vitesse (km/h)': st.session_state.run_data['speeds'],
            'Fréquence cardiaque': st.session_state.run_data['heart_rates']
        }))
