import streamlit as st
from database import DataEntry, update_session_state
import pandas as pd
import matplotlib.pyplot as plt

# Configuration initiale de Matplotlib
plt.rcParams.update({'font.size': 8})
plt.style.use('ggplot')

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
                "Sexe": entry.sexe,
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

            st.markdown("---")

            # Configuration des colonnes pour le selecteur et le bouton
            col1, col2 = st.columns([2, 1])

            # Liste des options de graphes
            graph_options = ["Taille", "Poids", "IMC", "Eau", "Calories", "Sommeil", "Activité", "TUG", "Audition"]

            # Selecteur de graphe
            with col1:
                selected_graph = st.selectbox("Sélectionner un graphe", options=graph_options, key="selected_graph")

            # Bouton pour afficher/supprimer le graphe
            with col2:
                st.write("\n")
                if 'graph' in st.session_state and st.session_state.graph == selected_graph:
                    if st.button(f"Supprimer {selected_graph}"):
                        del st.session_state.graph
                        st.rerun()
                else:
                    if st.button(f"Afficher {selected_graph}"):
                        st.session_state.graph = selected_graph
                        st.rerun()

            # Zone fixe pour les graphiques
            graph_placeholder = st.empty()

             # Affichage conditionnel des graphiques
            if 'graph' in st.session_state:
                fig, ax = plt.subplots(figsize=(8, 4))

                # Mapping des colonnes
                column_map = {
                    "Taille": "Taille (cm)",
                    "Poids": "Poids (kg)",
                    "IMC": "IMC",
                    "Eau": "Eau (L)",
                    "Calories": "Calories",
                    "Sommeil": "Sommeil (h)",
                    "Activité": "Activité (min)",
                    "TUG": "TUG (sec)",
                    "Audition": "Audition"
                }

                column = column_map[st.session_state.graph]

                # Création du graphique
                ax.plot(df["date"], df[column], marker='o', linestyle='-')
                ax.set_title(f"Évolution de {st.session_state.graph}")
                ax.set_xlabel("Date")
                ax.set_ylabel(column)
                plt.xticks(rotation=45)
                plt.tight_layout()

                # Affichage dans la zone réservée
                with graph_placeholder.container():
                    st.pyplot(fig)

                # Nettoyage après affichage
                plt.close(fig)

        st.markdown("---")
        # Saisie des critères
        update_session_state()
        age = st.number_input("Âge (ans)", min_value=0, max_value=150, value=st.session_state['age'])
        sexe = st.selectbox("Sexe", ["Homme", "Femme"], index=st.session_state['sexe_index'])

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