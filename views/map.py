# views/map.py

import streamlit as st
import time
import math
import pydeck as pdk
import datetime
import pandas as pd

from bokeh.plotting import figure
from bokeh.models.widgets import Button
from bokeh.models import CustomJS, Div
from bokeh.layouts import column

from streamlit_bokeh_events import streamlit_bokeh_events
from streamlit_autorefresh import st_autorefresh

def haversine(lat1, lon1, lat2, lon2):
    R = 6371e3  # mètres
    def rad(x): return math.radians(x)
    dlat = rad(lat2 - lat1)
    dlon = rad(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(rad(lat1)) * math.cos(rad(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def display_map_page():
    st.title("🚀 Tracking GPS en Temps Réel")

    # Vérification connexion
    if 'user_id' not in st.session_state:
        st.error("🔒 Veuillez vous connecter pour accéder à cette fonctionnalité.")
        return

    # Initialisation des états
    defaults = {
        'lat': None,
        'lon': None,
        'running': False,
        'start_time': 0.0,
        'trajectory': [],
        'speeds': []
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Section Géolocalisation
    with st.container():
        st.markdown("### 📍 Obtenir la position initiale")
        loc_button = Button(
            label="Détecter ma position actuelle",
            button_type="primary",
            width=250,
            height=40,
            styles={"font-size": "14px"}
        )
        
        # Script de géolocalisation
        loc_button.js_on_event("button_click", CustomJS(code="""
            if (!navigator.geolocation) {
                document.dispatchEvent(new CustomEvent("GET_LOCATION", {
                    detail: {error: "Géolocalisation non supportée par votre navigateur"}
                }));
            } else {
                navigator.geolocation.getCurrentPosition(
                    pos => {
                        document.dispatchEvent(new CustomEvent("GET_LOCATION", {
                            detail: {
                                lat: pos.coords.latitude,
                                lon: pos.coords.longitude,
                                accuracy: pos.coords.accuracy
                            }
                        }));
                    },
                    err => {
                        document.dispatchEvent(new CustomEvent("GET_LOCATION", {
                            detail: {error: err.message}
                        }));
                    }
                );
            }
        """))

        result = streamlit_bokeh_events(
            column(loc_button),
            events="GET_LOCATION",
            key="geo_events",
            refresh_on_update=True,
            override_height=100,
            debounce_time=0
        )

    # Traitement résultat géolocalisation
    if result and "GET_LOCATION" in result:
        data = result["GET_LOCATION"]
        if "error" in data:
            st.error(f"Erreur de géolocalisation : {data['error']}")
        else:
            st.session_state.lat = data["lat"]
            st.session_state.lon = data["lon"]
            st.success(f"Position détectée : {data['lat']:.5f}, {data['lon']:.5f} (±{data.get('accuracy', '?')}m)")

    # Contrôles d'enregistrement
    col1, col2 = st.columns(2)
    with col1:
        start_disabled = st.session_state.running or not st.session_state.lat
        if st.button("Démarrer l'enregistrement", 
                    disabled=start_disabled,
                    type="primary",
                    help="Commencer à enregistrer la trajectoire"):
            st.session_state.running = True
            st.session_state.start_time = time.time()
            st.session_state.trajectory = [{
                "lat": st.session_state.lat,
                "lon": st.session_state.lon,
                "timestamp": st.session_state.start_time
            }]
            st.session_state.speeds = [(st.session_state.start_time, 0.0)]
            st.rerun()

    with col2:
        if st.button("Arrêter l'enregistrement", 
                   disabled=not st.session_state.running,
                   type="secondary"):
            st.session_state.running = False
            st.rerun()

    # Rafraîchissement automatique
    if st.session_state.running:
        st_autorefresh(interval=2000, key="track_refresh")

    # Mise à jour de la trajectoire
    if st.session_state.running and st.session_state.lat and st.session_state.lon:
        last_point = st.session_state.trajectory[-1]
        if (abs(st.session_state.lat - last_point["lat"]) > 1e-6 or
            abs(st.session_state.lon - last_point["lon"]) > 1e-6):
            
            now = time.time()
            dt = max(now - last_point["timestamp"], 0.1)
            distance = haversine(
                last_point["lat"], last_point["lon"],
                st.session_state.lat, st.session_state.lon
            )
            speed = (distance / dt) * 3.6  # Conversion en km/h

            st.session_state.trajectory.append({
                "lat": st.session_state.lat,
                "lon": st.session_state.lon,
                "timestamp": now
            })
            st.session_state.speeds.append((now, speed))

    # Affichage des métriques
    if st.session_state.running:
        cols = st.columns(3)
        with cols[0]:
            st.metric("Durée", datetime.timedelta(seconds=int(time.time() - st.session_state.start_time)))
        with cols[1]:
            current_speed = st.session_state.speeds[-1][1] if st.session_state.speeds else 0.0
            st.metric("Vitesse actuelle", f"{current_speed:.1f} km/h")
        with cols[2]:
            total_distance = sum(
                haversine(
                    st.session_state.trajectory[i]["lat"], st.session_state.trajectory[i]["lon"],
                    st.session_state.trajectory[i+1]["lat"], st.session_state.trajectory[i+1]["lon"]
                ) for i in range(len(st.session_state.trajectory)-1)
            )
            st.metric("Distance totale", f"{total_distance:.0f} mètres")

    # Visualisation de la carte
    if st.session_state.trajectory:
        df = pd.DataFrame(st.session_state.trajectory)
        
        view_state = pdk.ViewState(
            latitude=df.iloc[-1]["lat"],
            longitude=df.iloc[-1]["lon"],
            zoom=15,
            pitch=50,
            bearing=0
        )

        layers = [
            pdk.Layer(
                "PathLayer",
                data=[[p["lon"], p["lat"]] for p in st.session_state.trajectory],
                get_width=5,
                get_color=[255, 40, 0],
                pickable=True
            ),
            pdk.Layer(
                "ScatterplotLayer",
                data=df.iloc[-1:],
                get_position=["lon", "lat"],
                get_radius=100,
                get_fill_color=[0, 200, 255],
                get_line_color=[0, 0, 0],
                pickable=True
            )
        ]

        st.pydeck_chart(pdk.Deck(
            map_style="road",
            initial_view_state=view_state,
            layers=layers,
            tooltip={
                "html": "<b>Lat:</b> {lat:.5f}<br/><b>Lon:</b> {lon:.5f}",
                "style": {"color": "white"}
            }
        ))

    # Graphique de vitesse
    if st.session_state.speeds:
        df_speed = pd.DataFrame(st.session_state.speeds, columns=["timestamp", "speed"])
        df_speed["time"] = pd.to_datetime(df_speed["timestamp"], unit="s").dt.strftime("%H:%M:%S")
        
        st.area_chart(
            df_speed.set_index("time")["speed"],
            use_container_width=True,
            color="#FF4B4B"
        )
        st.caption("Évolution de la vitesse au cours du temps")