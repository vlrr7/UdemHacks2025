import streamlit as st
from database import DataEntry
from ai_manager import generate_content

def display_gemini_overview_page():
    st.title("HealthPro")
    st.header("Analyse et Recommandations à l'aide de Gemini.")
    if 'user_id' not in st.session_state:
        st.error("Veuillez vous connecter pour accéder aux prédictions.")
    else:
        user_id = st.session_state['user_id']
        entries = DataEntry.find_by_user_id(user_id)
        if not entries:
            st.warning("Aucune donnée disponible pour générer une prédiction.")
        else:
            avg_age = entries[-1].age if entries else 0
            avg_height = entries[-1].height if entries else 0
            avg_weight = sum(e.weight for e in entries) / len(entries) if entries else 0
            avg_bmi = sum(e.bmi for e in entries) / len(entries) if entries else 0
            avg_water = sum(e.water for e in entries) / len(entries) if entries else 0
            avg_calories = sum(e.calories for e in entries) / len(entries) if entries else 0
            avg_sleep = sum(e.sleep for e in entries) / len(entries) if entries else 0
            avg_activity_time = sum(e.activity_time for e in entries) / len(entries) if entries else 0
            avg_tug = sum(e.timed_up_and_go_test for e in entries) / len(entries) if entries else 0
            user_data = {
                "age": avg_age,
                "height": avg_height,
                "weight": avg_weight,
                "bmi": avg_bmi,
                "water": avg_water,
                "calories": avg_calories,
                "sleep": avg_sleep,
                "activity_time": avg_activity_time,
                "timed_up_and_go_test": avg_tug
            }
            st.write(str(user_data))
            prediction = generate_content(user_data)
            st.subheader("Résultat de la prédiction")
            response_lines = prediction.split('\n')
            for line in response_lines:
                st.write(line)