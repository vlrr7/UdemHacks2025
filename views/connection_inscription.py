import streamlit as st
from database import login, register

def display_connection_page():
    st.header("Connexion")
    username = st.text_input("Nom d'utilisateur")
    password = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter"):
        user = login(username, password)
        if user:
            st.success(f"Bienvenue {user.username}!")
            st.session_state['user_id'] = user.id
        else:
            st.error("Identifiants incorrects")


def display_inscription_page():
    st.header("Inscription")
    username = st.text_input("Nom d'utilisateur", key="reg_username")
    email = st.text_input("Email", key="reg_email")
    password = st.text_input("Mot de passe", type="password", key="reg_password")

    if st.button("S'inscrire"):
        user, msg = register(username, password, email)
        if user:
            st.success(msg)
            st.session_state['user_id'] = user.id
        else:
            st.error(msg)