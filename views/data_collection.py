import streamlit as st
import datetime
from database import DataEntry

def display_data_collection_page():
    st.header("Saisie de vos données quotidiennes")
    if 'user_id' not in st.session_state:
        st.error("Veuillez vous connecter pour saisir vos données.")
    else:
        user_id = st.session_state['user_id']
        unformatted_date = st.date_input("Date", datetime.date.today())
        date = datetime.datetime.combine(unformatted_date, datetime.datetime.min.time())

        # Données générales
        st.subheader("Informations générales")
        age = st.number_input("Âge", min_value=0, step=1)
        height = st.number_input("Taille (cm)", min_value=50, max_value=250, step=1)
        weight = st.number_input("Poids (kg)", min_value=20.0, max_value=200.0, step=0.1)
        bmi = weight / ((height / 100) ** 2) if height > 0 else 0

        # Données quotidiennes
        st.subheader("Données quotidiennes")
        water = st.number_input("Eau consommée (L)", min_value=0.0, step=0.1)
        calories = st.number_input("Calories consommées", min_value=0, step=10)
        sleep = st.number_input("Heures de sommeil", min_value=0.0, step=0.5)
        activity_time = st.number_input("Temps d'activité physique (min)", min_value=0, step=1)

        # Données pour ainés (optionnelles)
        st.subheader("Pour les seniors (optionnel)")
        tug = st.number_input("Temps TUG (sec)", min_value=0.0, step=0.1, value=0.0)
        amsler = st.text_input("Résultat test visuel (Amsler)", value="Normal")
        hearing = st.text_input("Résultat test auditif", value="Normal")
        if st.button("Enregistrer les données"):
            new_entry = DataEntry(
                user_id=user_id,
                date=date,
                age=age,
                height=height,
                weight=weight,
                bmi=bmi,
                water=water,
                calories=calories,
                sleep=sleep,
                activity_time=activity_time,
                timed_up_and_go_test=tug,
                amsler=amsler,
                hearing=hearing
            )
            new_entry.save()
            st.success("Données enregistrées avec succès!")