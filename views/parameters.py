import streamlit as st
from database import User, users_collection
from werkzeug.security import generate_password_hash, check_password_hash

def display_parameters_page():
    st.title("HealthPro")
    st.header("Paramètres")

    if 'user_id' not in st.session_state:
        st.error("Veuillez vous connecter pour accéder aux paramètres.")
    else:
        user_id = st.session_state['user_id']
        user = User.find_by_id(user_id)  # Retrieve user info from the database
        print(user)

        if not user:
            st.error("Utilisateur introuvable.")
        else:
              # --- Déconnexion ---
            st.subheader("🚪 Déconnexion")
            if st.button("Se déconnecter"):
                del st.session_state['user_id']
                st.success("Vous avez été déconnecté.")
                st.session_state.current_page = "Connexion"
                st.rerun()
                
           # --- Changer le mot de passe ---
            st.subheader("🔑 Changer le mot de passe")

            # Input fields
            current_password = st.text_input("Mot de passe actuel", type="password")
            new_password = st.text_input("Nouveau mot de passe", type="password")
            confirm_password = st.text_input("Confirmer le nouveau mot de passe", type="password")

            if st.button("Mettre à jour le mot de passe"):
                if new_password == confirm_password:
                    if 'user_id' in st.session_state:
                        user_id = st.session_state['user_id']
                        success = User.update_password(user_id, current_password, new_password)  # Static method call
                        if success:
                            st.success("Mot de passe mis à jour avec succès.")
                        else:
                            st.error("Mot de passe actuel incorrect.")
                    else:
                        st.error("Utilisateur non connecté. Veuillez vous reconnecter.")
                else:
                    st.error("Les nouveaux mots de passe ne correspondent pas.")

            st.markdown("---")

            # --- Supprimer le compte ---
            st.subheader("🗑️ Supprimer le compte")
            st.warning("⚠️ Cette action est irréversible. Votre compte sera définitivement supprimé.")
            
            delete_password = generate_password_hash(st.text_input("Entrez votre mot de passe pour confirmer", type="password"))
            
            if st.button("Supprimer mon compte"):
                if user["password"] == delete_password: # Verify password
                    users_collection.delete_one({"_id":user_id})  # Delete user from DB
                    del st.session_state['user_id']  # Clear session
                    st.success("Votre compte a été supprimé avec succès. Redirection vers la page d'accueil...")
                    st.session_state.current_page = "Accueil"
                    st.rerun()
                else:
                    st.error("Mot de passe incorrect. Impossible de supprimer le compte.")