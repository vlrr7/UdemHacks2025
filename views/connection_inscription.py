import streamlit as st
from database import login, register

def display_connection_page():
    st.markdown(
        """
        <style>
        .fade-in {
            opacity: 0;
            transform: translateY(20px);
            animation: fadeIn 0.5s forwards;
        }

        @keyframes fadeIn {
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("Connectez vous à HealthPro!")
    st.header("Connexion",  )
    
    # Apply the fade-in class to the content
    st.write("<div class='fade-in'>", unsafe_allow_html=True)
    username = st.text_input("Nom d'utilisateur")
    password = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter"):
        user = login(username, password)
        if user:
            st.success(f"Bienvenue {user.username}!")
            st.session_state['user_id'] = user.id
        else:
            st.error("Identifiants incorrects")
    st.write("</div>", unsafe_allow_html=True)


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
        else:
            st.error(msg)