import streamlit as st

st.set_page_config(
    page_title="HealthPro", 
    page_icon="🏥", 
    layout="wide"
)

from views.connection_inscription import display_connection_page, display_inscription_page
from views.data_collection import display_data_collection_page
from views.analysis import display_analysis_page
from views.social import display_social_page
from views.gemini_overview import display_gemini_overview_page
from views.parameters import display_parameters_page
try:
    from views.map import display_map_page
except Exception as e:
    st.error(f"Une erreur s'est produite: {str(e)}")


def main():
    menu = ["Connexion", "Inscription", "Données",
            "Analyse", "Social", "Map Running", "AI Overview", "Paramètres"]
    # Configuration du menu latéral toujours ouvert
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Connexion"

    cols = st.columns(len(menu))
    for i, page in enumerate(menu):
        with cols[i]:
            if st.button(page, key=f"menu_{page}", use_container_width=True):
                st.session_state.current_page = page

    
    
    # ----- Page de connexion -----
    if st.session_state.current_page == "Connexion":
        display_connection_page()

    elif st.session_state.current_page == "Inscription":
        display_inscription_page()

    # ----- données -----
    elif st.session_state.current_page== "Données":
        display_data_collection_page()

    # ----- Analyse des données -----
    elif st.session_state.current_page == "Analyse":
        display_analysis_page()

    # ----- Interface sociale -----
    elif st.session_state.current_page == "Social":
        display_social_page()

    elif st.session_state.current_page == "Map Running":
        try:
            display_map_page()
        except Exception as e:
            st.error(f"Une erreur s'est produite: {str(e)}")

    # ----- Prédictions Gemini -----
    elif st.session_state.current_page == "AI Overview":
        display_gemini_overview_page()

    # ----- Paramètres utilisateur -----
    elif st.session_state.current_page == "Paramètres":
        display_parameters_page()

if __name__ == '__main__':
    main()