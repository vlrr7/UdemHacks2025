# views/map.py
import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime
import pydeck as pdk
from streamlit_autorefresh import st_autorefresh
from database import User
from streamlit_javascript import st_javascript  # Nouvelle librairie pour exécuter du JS
import time
from streamlit_js_eval import get_geolocation
import math



def haversine_distance(coord1, coord2):
    """
    Calcule la distance en mètres entre deux points (lat, lon) en utilisant la formule de Haversine.
    """
    R = 6371e3  # rayon de la Terre en mètres
    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c





# Update refresh rate to 1 second for better real-time feel
st_autorefresh(interval=1000, key="maprefresh")

def calculate_target_heart_rate(age):
    max_hr = 220 - age
    return {
        'vo2max': 0.85 * max_hr,
        'seuil anaérobique': 0.90 * max_hr,
        'modéré': 0.70 * max_hr
    }

# Replace your existing `get_geolocation` function with this:
# def get_geolocation():
#     handle_geolocation_message()  # This updates st.session_state.geolocation_result
#     geo = st.session_state.get("geolocation_result", None)
#     print(geo)
#     return geo


# Add this to capture JS messages
def handle_geolocation_message():
    # Generate a unique key using timestamp
    unique_key = f"geolocation_async_{time.time()}"
    
    result = st_javascript("""
    new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(
            position => resolve({
                lat: position.coords.latitude,
                lon: position.coords.longitude
            }),
            error => reject(error.message)
        );
    })
    """, key=unique_key)  # Use dynamic key here
    print("result : " + str(result))
    if result and "lat" in result:
        st.session_state.geolocation_result = (result["lat"], result["lon"])
    elif result and "error" in result:
        st.error(f"Geolocation Error: {result['error']}")

def display_map_page():
    handle_geolocation_message()  # <-- Add this line

    st.title("🏃 Running Tracker")    
    
    # Vérifier que l'utilisateur est connecté
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
    
    # Initialisation des données de course si elles n'existent pas
    if 'run_data' not in st.session_state:
        st.session_state.run_data = {
            'positions': [],
            'timestamps': [],
            'speeds': [],
            'heart_rates': []
            
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
                'positions': [],
                'timestamps': [],
                'speeds': [],
                'heart_rates': []
                
            }
            st.session_state.elapsed = 0
            
    # Si la course est en cours, récupérer la géolocalisation via le code JS et mettre à jour les données
    if st.session_state.run_start:
        elapsed = time.time() - st.session_state.run_start
        st.session_state.elapsed = elapsed

        geo = get_geolocation()
        st.info(str(geo))
        if geo and geo["coords"]:
            new_position = [geo["coords"]["latitude"], geo["coords"]["longitude"]]
        else:
            new_position = [48.8566, 2.3522]
            st.info("🔍 Recherche du signal GPS...")

        # Calcule de la vitesse réelle si une position précédente existe
        current_timestamp = datetime.now()
        if st.session_state.run_data['positions']:
            previous_position = st.session_state.run_data['positions'][-1]
            previous_timestamp = st.session_state.run_data['timestamps'][-1]
            time_diff = (current_timestamp - previous_timestamp).total_seconds()
            if time_diff > 0:
                distance = haversine_distance(previous_position, new_position)  # en mètres
                speed = (distance / time_diff) * 3.6  # conversion m/s en km/h
            else:
                speed = 0
        else:
            speed = 0

        new_data = {
        'timestamp': current_timestamp,
        'speed': speed,
        'heart_rate': np.random.randint(120, 190),
        'position': new_position
        }
        st.session_state.run_data['timestamps'].append(new_data['timestamp'])
        st.session_state.run_data['speeds'].append(new_data['speed'])
        st.session_state.run_data['heart_rates'].append(new_data['heart_rate'])
        st.session_state.run_data['positions'].append(new_data['position'])

    else:
        # Si la course est arrêtée, on n'actualise pas les données de course.
        st.info("La course est arrêtée. Appuyez sur '🚩 Démarrer la course' pour actualiser les données GPS.")

        
    current_speed = st.session_state.run_data['speeds'][-1] if st.session_state.run_data['speeds'] else 0
    current_hr = st.session_state.run_data['heart_rates'][-1] if st.session_state.run_data['heart_rates'] else 0
    
    with st.container():
        cols = st.columns(4)
        cols[0].metric("⏱️ Temps", f"{int(st.session_state.elapsed // 60)}:{int(st.session_state.elapsed % 60):02d}")
        cols[1].metric("📈 Vitesse", f"{current_speed:.1f} km/h")
        cols[2].metric("💓 FC Actuelle", f"{current_hr} bpm")
        cols[3].metric("🎯 Cible FC", f"{heart_rates[target_type.lower()]:.0f} bpm")
        
    # Replace your existing pydeck chart code with this:
    if st.session_state.run_data['positions']:
        latest_lat = st.session_state.run_data['positions'][-1][0]
        latest_lon = st.session_state.run_data['positions'][-1][1]
        


    if st.session_state.run_data['positions']:
    # Convertir la liste des positions au format [lon, lat] pour PathLayer
        path_positions = [[pos[1], pos[0]] for pos in st.session_state.run_data['positions']]
        latest_lat = st.session_state.run_data['positions'][-1][0]
        latest_lon = st.session_state.run_data['positions'][-1][1]


        st.pydeck_chart(pdk.Deck(
    map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",  # Utilisation d'OpenStreetMap, sans clé API Mapbox
    initial_view_state=pdk.ViewState(
        latitude=latest_lat,  # Centrer la vue sur la dernière position
        longitude=latest_lon,
        zoom=16,            # Zoom rapproché pour un suivi en temps réel
        pitch=50
    ),
    layers=[
        pdk.Layer(
            'ScatterplotLayer',
            data=pd.DataFrame({
                'lat': [latest_lat],
                'lon': [latest_lon]
            }),
            get_position='[lon, lat]',
            get_color='[0, 128, 255, 200]',  # Point bleu pour la position actuelle
            get_radius=25,
        ),
        pdk.Layer(
            'PathLayer',
            data=pd.DataFrame({'path': [path_positions]}),
            get_path='path',
            get_color='[255, 0, 0, 150]',  # Ligne rouge pour la trajectoire
            get_width=5,
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
