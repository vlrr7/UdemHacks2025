import streamlit as st
from database import DataEntry
from ai_manager import gemini_predict

def display_gemini_overview_page():
    st.header("Prédictions et Recommandations (Gemini)")
    if 'user_id' not in st.session_state:
        st.error("Veuillez vous connecter pour accéder aux prédictions.")
    else:
        user_id = st.session_state['user_id']
        entries = DataEntry.find_by_user_id(user_id)
        if not entries:
            st.warning("Aucune donnée disponible pour générer une prédiction.")
        else:
            avg_age = sum(e.age for e in entries) / len(entries) if entries else 0
            avg_height = sum(e.height for e in entries) / len(entries) if entries else 0
            avg_weight = sum(e.weight for e in entries) / len(entries) if entries else 0
            avg_bmi = sum(e.bmi for e in entries) / len(entries) if entries else 0
            avg_water = sum(e.water for e in entries) / len(entries) if entries else 0
            avg_calories = sum(e.calories for e in entries) / len(entries) if entries else 0
            avg_sleep = sum(e.sleep for e in entries) / len(entries) if entries else 0
            avg_activity_time = sum(e.activity_time for e in entries) / len(entries) if entries else 0
            avg_tug = sum(e.tug for e in entries) / len(entries) if entries else 0
            user_data = {
                "age": avg_age,
                "height": avg_height,
                "weight": avg_weight,
                "bmi": avg_bmi,
                "water": avg_water,
                "calories": avg_calories,
                "sleep": avg_sleep,
                "activity_time": avg_activity_time,
                "tug": avg_tug
            }
            st.write("Données agrégées pour la prédiction :", user_data)
            prediction = gemini_predict(user_data)
            st.subheader("Résultat de la prédiction")
            st.write(f"{prediction}")