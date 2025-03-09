# views/normes.py
import streamlit as st
import pandas as pd

def display_normes_page():
    st.header("Normes des renseignements")
    st.write("Saisissez vos renseignements pour obtenir le résumé des normes.")

    # Saisie des critères
    age = st.number_input("Âge (ans)", min_value=1, max_value=150, value=25)
    sexe = st.selectbox("Sexe", ["Homme", "Femme"])
    poids = st.number_input("Poids (kg)", min_value=1.0, value=70.0, format="%.2f")
    eau = st.number_input("Eau (L)", min_value=0.0, value=1.5, format="%.2f")
    sommeil = st.number_input("Sommeil (h)", min_value=0.0, value=8.0, format="%.1f")
    calories = st.number_input("Calories", min_value=0, value=2000)
    activite = st.number_input("Activité physique (min)", min_value=0, value=60)
    taille = st.number_input("Taille (cm)", min_value=0.0, value=170.0, format="%.1f")
    imc = st.number_input("IMC", min_value=0.0, value=24.0, format="%.2f")

    if st.button("Afficher les normes"):
        try:
            # Lecture du fichier CSV avec ";" comme délimiteur et "," comme séparateur décimal
            df_normes = pd.read_csv("normes.csv", delimiter=";", decimal=",")
            # Filtrer le DataFrame en fonction de l'âge et du sexe
            norme = df_normes[(df_normes["Âge (ans)"] == age) & (df_normes["Sexe"] == sexe)]
            if norme.empty:
                st.error("Aucune norme trouvée pour ces critères.")
            else:
                st.write(f"Normes pour {sexe} de {age} ans :")
                st.dataframe(norme)
        except Exception as e:
            st.error("Erreur lors de la lecture du fichier CSV : " + str(e))