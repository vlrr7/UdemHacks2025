import streamlit as st

from views.connection_inscription import display_connection_page, display_inscription_page
from views.data_collection import display_data_collection_page
from views.analysis import display_analysis_page
from views.social import display_social_page
from views.gemini_overview import display_gemini_overview_page
from views.parameters import display_parameters_page
from views.map import display_map_page


def main():
    menu = ["Connexion", "Inscription", "Collecte des Données",
            "Analyse", "Social", "Map Running", "Gemini Predictions", "Paramètres"]
    # Configuration du menu latéral toujours ouvert
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Connexion"

    with st.sidebar:
        st.markdown("### Navigation")
        for page in menu:
            if st.button(page, key=f"menu_{page}"):
                st.session_state.current_page = page

    
    
    # ----- Page de connexion -----
    if st.session_state.current_page == "Connexion":
        display_connection_page()

    elif st.session_state.current_page == "Inscription":
        display_inscription_page()

    # ----- Collecte des données -----
    elif st.session_state.current_page== "Collecte des Données":
        display_data_collection_page()

    # ----- Analyse des données -----
    elif st.session_state.current_page == "Analyse":
        display_analysis_page()

    # ----- Interface sociale -----
    elif st.session_state.current_page == "Social":
        display_social_page()

    elif st.session_state.current_page == "Map Running":
        display_map_page()

    # ----- Prédictions Gemini -----
    elif st.session_state.current_page == "Gemini Predictions":
        display_gemini_overview_page()

    # ----- Paramètres utilisateur -----
    elif st.session_state.current_page == "Paramètres":
        display_parameters_page()        

if __name__ == '__main__':
    main()