# main.py
import streamlit as st

st.set_page_config(
    page_title="HealthPro", 
    page_icon="🏥", 
    layout="wide"
)

# Import des pages de l'application
from views.connection_inscription import display_connection_page, display_inscription_page
from views.data_collection import display_data_collection_page
from views.analysis import display_analysis_page
from views.social import display_social_page
from views.gemini_overview import display_gemini_overview_page
from views.parameters import display_parameters_page
from views.map import display_map_page

def main():
    menu = ["Données", "Analyse", "Social", "Map Running", "AI Overview", "Paramètres"]
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Connexion"

    if (st.session_state.current_page != "Connexion") and (st.session_state.current_page != "Inscription"):
        cols = st.columns(len(menu))
        for i, page in enumerate(menu):
            with cols[i]:
                if st.button(page, key=f"menu_{page}", use_container_width=True):
                    st.session_state.current_page = page

    if st.session_state.current_page == "Connexion":
        display_connection_page()
    elif st.session_state.current_page == "Inscription":
        display_inscription_page()
    elif st.session_state.current_page == "Données":
        display_data_collection_page()
    elif st.session_state.current_page == "Analyse":
        display_analysis_page()
    elif st.session_state.current_page == "Social":
        display_social_page()
    elif st.session_state.current_page == "Map Running":
        display_map_page()
    elif st.session_state.current_page == "AI Overview":
        display_gemini_overview_page()
    elif st.session_state.current_page == "Paramètres":
        display_parameters_page()

if __name__ == '__main__':
    main()
