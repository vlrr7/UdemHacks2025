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

def calculate_target_heart_rate(age):
    max_hr = 220 - age
    return {
        'vo2max': 0.85 * max_hr,
        'seuil anaérobique': 0.90 * max_hr,
        'modéré': 0.70 * max_hr
    }

def get_geolocation():
    # Code JavaScript asynchrone pour récupérer la position
    js_code = """
    async function getLocation() {
      return new Promise((resolve, reject) => {
          if (navigator.geolocation) {
              navigator.geolocation.getCurrentPosition(
                  (position) => {
                      resolve({lat: position.coords.latitude, lon: position.coords.longitude});
                  },
                  (error) => {
                      reject("Erreur de géolocalisation: " + error.message);
                  }
              );
          } else {
              reject("La géolocalisation n'est pas supportée par ce navigateur.");
          }
      });
    }
    getLocation();
    """
    try:
        result = st_javascript(js_code, key="geolocation")
        return result  # Doit être un dictionnaire avec keys "lat" et "lon"
    except Exception as e:
        st.error("Erreur lors de la récupération de la géolocalisation: " + str(e))
        return None

def display_map_page():
    st.title("🏃♂️ Running Tracker")
    
    # Auto-refresh toutes les 5 secondes pour simuler une mise à jour en temps réel
    st_autorefresh(interval=5000, key="datarefresh")
    
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
            
    # Si la course est en cours, récupérer la géolocalisation via le code JS et mettre à jour les données
    if st.session_state.run_start:
        elapsed = time.time() - st.session_state.run_start
        st.session_state.elapsed = elapsed

        geo = get_geolocation()
        if geo and "lat" in geo and "lon" in geo:
            new_position = [geo["lat"], geo["lon"]]
        else:
            new_position = [48.8566, 2.3522]
            st.info("🔍 Recherche du signal GPS...")

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
