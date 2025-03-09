import streamlit as st
from database import DataEntry
import pandas as pd

def display_analysis_page():
    st.title("HealthPro")
    st.header("Analyse de vos données")
    if 'user_id' not in st.session_state:
        st.error("Veuillez vous connecter pour accéder à l'analyse.")
    else:
        user_id = st.session_state['user_id']
        entries = DataEntry.find_by_user_id(user_id)
        if not entries:
            st.warning("Aucune donnée disponible pour l'analyse.")
        else:
            data = [{
                "date": entry.date,
                "Âge": entry.age,
                "Taille (cm)": entry.height,
                "Poids (kg)": entry.weight,
                "IMC": entry.bmi,
                "Eau (L)": entry.water,
                "Calories": entry.calories,
                "Sommeil (h)": entry.sleep,
                "Activité (min)": entry.activity_time,
                "TUG (sec)": entry.timed_up_and_go_test,
                "Amsler": entry.amsler,
                "Audition": entry.hearing
            } for entry in entries]
            df = pd.DataFrame(data)
            st.dataframe(df)
            # You can add plots here if needed, but the data structure has changed significantly
            # Example: st.line_chart(df[["date", "Sommeil (h)"]].set_index("date"))