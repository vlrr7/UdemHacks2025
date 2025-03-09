# views/map.py

import streamlit as st
import time
import math
import pydeck as pdk
import datetime
import pandas as pd

from bokeh.plotting import figure
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from bokeh.layouts import column

from streamlit_bokeh_events import streamlit_bokeh_events
from streamlit_autorefresh import st_autorefresh

def haversine(lat1, lon1, lat2, lon2):
    R = 6371e3  # mètres
    def rad(x): return math.radians(x)
    dlat = rad(lat2 - lat1)
    dlon = rad(lon2 - lon1)
    a = (math.sin(dlat/2)**2 +
         math.cos(rad(lat1))*math.cos(rad(lat2))*math.sin(dlon/2)**2)
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R*c

def display_map_page():
    st.title("Exemple Localisation via streamlit-bokeh-events")

    # Vérifier la connexion
    if 'user_id' not in st.session_state:
        st.error("Veuillez vous connecter pour accéder à la carte.")
        return

    # Initialisations
    if 'lat' not in st.session_state:
        st.session_state.lat = None
    if 'lon' not in st.session_state:
        st.session_state.lon = None
    if 'running' not in st.session_state:
        st.session_state.running = False
    if 'start_time' not in st.session_state:
        st.session_state.start_time = 0.0
    if 'trajectory' not in st.session_state:
        st.session_state.trajectory = []
    if 'speeds' not in st.session_state:
        st.session_state.speeds = []

    # 1) Créer un layout Bokeh avec un bouton
    loc_button = Button(label="Obtenir ma localisation", button_type="success")
    loc_button.js_on_event("button_click", CustomJS(code="""
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                document.dispatchEvent(new CustomEvent("GET_LOCATION", 
                    {detail: {lat: pos.coords.latitude, lon: pos.coords.longitude}}))
            },
            (err) => {
                document.dispatchEvent(new CustomEvent("GET_LOCATION", 
                    {detail: {error: err.message}}))
            }
        )
    """))

    layout = column(loc_button)
    result = streamlit_bokeh_events(
        layout,
        events="GET_LOCATION",
        key="get_location",
        refresh_on_update=False,
        override_height=75,
        debounce_time=0
    )

    # 2) Vérifier le résultat
    if result and "GET_LOCATION" in result:
        data = result["GET_LOCATION"]
        if "error" in data:
            st.error(f"Erreur géolocalisation: {data['error']}")
        else:
            st.session_state.lat = data["lat"]
            st.session_state.lon = data["lon"]
            st.success(f"Position : {data['lat']:.6f}, {data['lon']:.6f}")

    # Boutons “Commencer” / “Arrêter”
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Commencer", disabled=st.session_state.running):
            if st.session_state.lat is None or st.session_state.lon is None:
                st.error("Localisation non disponible. Cliquez sur 'Obtenir ma localisation'.")
            else:
                st.session_state.running = True
                st.session_state.start_time = time.time()
                st.session_state.trajectory = [{
                    "lat": st.session_state.lat,
                    "lon": st.session_state.lon,
                    "timestamp": time.time()
                }]
                st.session_state.speeds = [(time.time(), 0.0)]
    with col2:
        if st.button("Arrêter", disabled=not st.session_state.running):
            st.session_state.running = False

    # Si running => rafraîchissement auto toutes les 2 secondes
    if st.session_state.running:
        st_autorefresh(interval=2000, limit=None, key="auto_refresh_map")

    # Mise à jour en temps réel
    if st.session_state.running and st.session_state.lat is not None and st.session_state.lon is not None:
        # On suppose que l'utilisateur reclique “Obtenir ma localisation”
        # ou qu'il y aurait un code plus avancé pour récupérer la position en continu
        # => on check si la position a changé par rapport au dernier point
        last_point = st.session_state.trajectory[-1]
        lat_new = st.session_state.lat
        lon_new = st.session_state.lon
        if abs(lat_new - last_point["lat"]) > 1e-6 or abs(lon_new - last_point["lon"]) > 1e-6:
            now = time.time()
            dt = now - last_point["timestamp"]
            if dt < 0.1: dt = 0.1
            dist_m = haversine(last_point["lat"], last_point["lon"], lat_new, lon_new)
            speed_kmh = (dist_m / dt) * 3.6
            st.session_state.trajectory.append({"lat": lat_new, "lon": lon_new, "timestamp": now})
            st.session_state.speeds.append((now, speed_kmh))

    # Affichage chrono
    if st.session_state.running:
        elapsed = time.time() - st.session_state.start_time
        mm, ss = divmod(int(elapsed), 60)
        st.write(f"**Temps écoulé** : {mm:02d}:{ss:02d}")
    else:
        if st.session_state.speeds:
            total_sec = st.session_state.speeds[-1][0] - st.session_state.start_time
            mm, ss = divmod(int(total_sec), 60)
            st.write(f"Course terminée : {mm:02d}:{ss:02d}")

    # Affichage carte PyDeck
    if st.session_state.trajectory:
        df = pd.DataFrame(st.session_state.trajectory)
        # Créer la ligne
        line_data = []
        for i in range(len(df)-1):
            p1 = df.iloc[i]
            p2 = df.iloc[i+1]
            line_data.append([[p1["lon"], p1["lat"]], [p2["lon"], p2["lat"]]])
        line_layer = pdk.Layer(
            "PathLayer",
            data=line_data,
            get_path="object",
            get_width=5,
            get_color=[255,0,0]
        )
        point_layer = pdk.Layer(
            "ScatterplotLayer",
            data=df,
            get_position=["lon","lat"],
            get_radius=50,
            get_color=[0,128,255]
        )
        last_point = df.iloc[-1]
        view_state = pdk.ViewState(
            longitude=last_point["lon"],
            latitude=last_point["lat"],
            zoom=15
        )
        r = pdk.Deck(
            layers=[line_layer, point_layer],
            initial_view_state=view_state
        )
        st.pydeck_chart(r)

    # Graphique de vitesse
    if st.session_state.speeds:
        df_speeds = pd.DataFrame(st.session_state.speeds, columns=["timestamp", "speed_kmh"])
        df_speeds["time"] = df_speeds["timestamp"].apply(lambda t: datetime.datetime.fromtimestamp(t).strftime("%H:%M:%S"))
        df_speeds.set_index("time", inplace=True)
        st.line_chart(df_speeds["speed_kmh"])
        st.write("Évolution de la vitesse (km/h).")
