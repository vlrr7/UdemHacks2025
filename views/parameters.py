import streamlit as st
from database import User, users_collection

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

            # --- Changer les informations personnelles ---
            st.subheader("👤 Modifier les informations générales")

            new_username = st.text_input("Nouveau nom d'utilisateur", value=user["username"])
            new_age = st.number_input("Âge", min_value=0, step=1, value=user["age"])
            new_sexe = st.selectbox("Sexe", ["Homme", "Femme", "Autre"], index=["Homme", "Femme", "Autre"].index(user["sexe"]))
            new_height = st.number_input("Taille (cm)", min_value=50, max_value=250, step=1, value=user["height"])
            new_weight = st.number_input("Poids (kg)", min_value=20.0, max_value=200.0, step=0.1, value=user["weight"])

            if st.button("Enregistrer les modifications"):
                user["username"] = new_username
                user["age"] = new_age
                user["sexe"] = new_sexe
                user["height"] = new_height
                user["weight"] = new_weight

                # Save changes to MongoDB
                users_collection.update_one({"_id": user["_id"]}, {"$set": user})

                st.success("Informations mises à jour avec succès.")

            st.markdown("---")
