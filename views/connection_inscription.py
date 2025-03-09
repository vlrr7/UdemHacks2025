import streamlit as st
from database import login, register

def display_connection_page():
    st.title("Connectez vous à HealthPro!")
    st.header("Authentification")
    
    username = st.text_input("Nom d'utilisateur")
    password = st.text_input("Mot de passe", type="password")

    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Se connecter"):
                user = login(username, password)
                if user:
                    st.success(f"Bienvenue {user.username}!")
                    st.session_state['user_id'] = user.id
                    st.session_state.current_page = "Données"
                    st.rerun()
                else:
                    st.error("Identifiants incorrects")
        with col2:
            coli, colj, colk, colm = st.columns(4)
            colk.write("Pas encore inscrit ?")
            if colm.button("S'inscrire"):
                st.session_state.current_page = "Inscription"
                st.rerun()


def display_inscription_page():
    st.title("HealthPro")
    st.header("Inscription")
    username = st.text_input("Nom d'utilisateur", key="reg_username")
    email = st.text_input("Email", key="reg_email")
    password = st.text_input("Mot de passe", type="password", key="reg_password")

    if st.button("S'inscrire"):
        user, msg = register(username, password, email)
        if user:
            st.success(msg)
            st.session_state['user_id'] = user.id
            st.session_state.current_page = "Données"
            st.rerun()
        else:
            st.error(msg)