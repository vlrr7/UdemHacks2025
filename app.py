from ai_manager import gemini_predict, evaluate_risk
from database import session, User, DataEntry, Follow
from connection import login, register

import streamlit as st
import datetime
import matplotlib.pyplot as plt
import pandas as pd
import json


# -----------------------------
# Application Streamlit
# -----------------------------
def main():
    st.title("Application HealthPro")
    menu = ["Accueil", "Connexion", "Inscription", "Collecte des Données",
            "Analyse", "Social", "Gemini Predictions", "Paramètres"]
    choice = st.sidebar.selectbox("Menu", menu)

    # ----- Page d'accueil -----
    if choice == "Accueil":
        st.header("Bienvenue sur l'application HealthPro")
        st.write("Veuillez vous connecter ou vous inscrire pour commencer.")
    # ----- Page de connexion -----
    elif choice == "Connexion":
        st.header("Connexion")
        username = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter"):
            user = login(username, password)
            if user:
                st.success(f"Bienvenue {user.username}!")
                st.session_state['user_id'] = user.id
            else:
                st.error("Nom d'utilisateur ou mot de passe incorrect.")

    # ----- Page d'inscription -----
    elif choice == "Inscription":
        st.header("Inscription")
        username = st.text_input("Nom d'utilisateur", key="reg_username")
        email = st.text_input("Email", key="reg_email")
        password = st.text_input(
            "Mot de passe", type="password", key="reg_password")

        if st.button("S'inscrire"):
            user, msg = register(username, password, email)
            if user:
                st.success(msg)
            else:
                st.error(msg)

    # ----- Collecte des données -----
    elif choice == "Collecte des Données":
        st.header("Saisie de vos données quotidiennes")
        if 'user_id' not in st.session_state:
            st.error("Veuillez vous connecter pour saisir vos données.")
        else:
            user_id = st.session_state['user_id']
            date = st.date_input("Date", datetime.date.today())
            pushups = st.number_input("Nombre de pompes", min_value=0, step=1)
            meals_count = st.number_input(
                "Nombre de repas", min_value=0, step=1)
            st.info(
                "Saisissez les détails de vos repas au format JSON. Ex: {\"petit_dejeuner\": \"oeufs, toast\", \"dejeuner\": \"salade\"}")
            meals_details = st.text_area("Détails des repas", height=100)
            water_intake = st.number_input(
                "Consommation d'eau (litres)", min_value=0.0, step=0.1, format="%.2f")
            sleep_hours = st.number_input(
                "Heures de sommeil", min_value=0.0, step=0.5, format="%.1f")
            time_spent = st.number_input(
                "Temps passé sur activités (en minutes)", min_value=0, step=1)
            if st.button("Enregistrer les données"):
                try:
                    meals_json = json.loads(
                        meals_details) if meals_details else {}
                except Exception as e:
                    st.error(
                        "Le format des détails des repas n'est pas un JSON valide.")
                    return
                new_entry = DataEntry(
                    user_id=user_id,
                    date=date,
                    pushups=pushups,
                    meals_count=meals_count,
                    meals_details=json.dumps(meals_json),
                    water_intake=water_intake,
                    sleep_hours=sleep_hours,
                    time_spent=time_spent
                )
                session.add(new_entry)
                session.commit()
                st.success("Données enregistrées avec succès!")

    # ----- Analyse des données -----
    elif choice == "Analyse":
        st.header("Analyse de vos données")
        if 'user_id' not in st.session_state:
            st.error("Veuillez vous connecter pour accéder à l'analyse.")
        else:
            user_id = st.session_state['user_id']
            entries = session.query(DataEntry).filter_by(user_id=user_id).all()
            if not entries:
                st.warning("Aucune donnée disponible pour l'analyse.")
            else:
                # Conversion des données en DataFrame
                data = [{
                    "date": entry.date,
                    "pompes": entry.pushups,
                    "repas": entry.meals_count,
                    "eau (L)": entry.water_intake,
                    "sommeil (h)": entry.sleep_hours,
                    "temps (min)": entry.time_spent
                } for entry in entries]
                df = pd.DataFrame(data)
                st.dataframe(df)

                # Visualisation avec Matplotlib
                fig, ax = plt.subplots()
                ax.plot(df["date"], df["pompes"], marker="o", label="Pompes")
                ax.set_title("Évolution du nombre de pompes")
                ax.set_xlabel("Date")
                ax.set_ylabel("Nombre de pompes")
                ax.legend()
                st.pyplot(fig)

    # ----- Interface sociale -----
    elif choice == "Social":
        st.header("Réseau Social")
        
        if 'user_id' not in st.session_state:
            st.error("Veuillez vous connecter pour accéder aux fonctionnalités sociales.")
        else:
            user_id = st.session_state['user_id']

            # ---- Suivre un utilisateur ----
            st.subheader("Suivre un utilisateur")
            follow_username = st.text_input("Nom d'utilisateur à suivre")
            if st.button("Suivre"):
                user_to_follow = session.query(User).filter_by(username=follow_username).first()
                if user_to_follow:
                    exists = session.query(Follow).filter_by(
                        follower_id=user_id, followed_id=user_to_follow.id).first()
                    if not exists:
                        new_follow = Follow(follower_id=user_id, followed_id=user_to_follow.id)
                        session.add(new_follow)
                        session.commit()
                        st.success(f"Vous suivez désormais {follow_username}!")
                    else:
                        st.info("Vous suivez déjà cet utilisateur.")
                else:
                    st.error("Utilisateur non trouvé.")

            # ---- Liste des amis ----
            st.subheader("Vos amis")
            # Force refresh des données après une action
            follows = session.query(Follow).filter_by(follower_id=user_id).all()
            followed_ids = [follow.followed_id for follow in follows]
            
            if not followed_ids:
                st.info("Vous ne suivez personne actuellement.")
            else:
                followed_users = session.query(User).filter(User.id.in_(followed_ids)).all()
                selected_user = None

                # Affichage dynamique avec colonnes
                cols = st.columns(len(followed_users))
                for i, friend in enumerate(followed_users):
                    with cols[i]:
                        # Utilisation de st.session_state pour conserver la sélection
                        if st.button(friend.username, key=f"friend_{friend.id}"):
                            st.session_state.selected_user_id = friend.id

                # Récupération de l'utilisateur sélectionné
                if 'selected_user_id' in st.session_state:
                    selected_user = session.query(User).get(st.session_state.selected_user_id)

                if selected_user:
                    st.subheader(f"Statistiques de {selected_user.username}")
                    
                    # ---- Option Ne plus suivre ----
                    if st.button("Ne plus suivre"):
                        session.query(Follow).filter_by(
                            follower_id=user_id, followed_id=selected_user.id).delete()
                        session.commit()
                        st.success(f"Vous ne suivez plus {selected_user.username}.")
                        # Suppression de la sélection et rechargement
                        del st.session_state.selected_user_id
                        st.rerun()  # Utilisation de st.rerun() à la place de experimental_rerun()

                    # ---- Affichage des données ----
                    entries = session.query(DataEntry).filter_by(user_id=selected_user.id).order_by(DataEntry.date.desc()).all()
                    
                    if not entries:
                        st.warning("Aucune donnée disponible pour cet utilisateur.")
                    else:
                        available_dates = [entry.date for entry in entries]
                        selected_date = st.selectbox("Sélectionnez une date", available_dates)
                        entry = next(e for e in entries if e.date == selected_date)
                        
                        st.write(f"📅 **Date:** {entry.date}")
                        st.write(f"💪 **Pompes:** {entry.pushups}")
                        st.write(f"🍽 **Repas:** {entry.meals_count}")
                        st.write(f"💧 **Eau (L):** {entry.water_intake}")
                        st.write(f"😴 **Sommeil (h):** {entry.sleep_hours}")
                        st.write(f"📱 **Temps passé (min):** {entry.time_spent}")

                        # ---- Statistiques globales ----
                        if st.button("Voir les statistiques globales de cet utilisateur"):
                            avg_pushups = sum(e.pushups for e in entries) / len(entries)
                            avg_meals = sum(e.meals_count for e in entries) / len(entries)
                            avg_water = sum(e.water_intake for e in entries) / len(entries)
                            avg_sleep = sum(e.sleep_hours for e in entries) / len(entries)
                            avg_time = sum(e.time_spent for e in entries) / len(entries)

                            st.write("📊 **Statistiques globales**")
                            st.write(f"💪 **Pompes moyennes:** {avg_pushups:.1f}")
                            st.write(f"🍽 **Repas moyens:** {avg_meals:.1f}")
                            st.write(f"💧 **Eau moyenne (L):** {avg_water:.1f}")
                            st.write(f"😴 **Sommeil moyen (h):** {avg_sleep:.1f}")
                            st.write(f"📱 **Temps passé moyen (min):** {avg_time:.1f}")

                            # ---- Comparaison ----
                            my_entries = session.query(DataEntry).filter_by(user_id=user_id).all()
                            if my_entries and st.button("Comparer mes statistiques avec cet utilisateur"):
                                my_avg_pushups = sum(e.pushups for e in my_entries)/len(my_entries)
                                my_avg_meals = sum(e.meals_count for e in my_entries)/len(my_entries)
                                my_avg_water = sum(e.water_intake for e in my_entries)/len(my_entries)
                                my_avg_sleep = sum(e.sleep_hours for e in my_entries)/len(my_entries)
                                my_avg_time = sum(e.time_spent for e in my_entries)/len(my_entries)

                                df_comparison = pd.DataFrame({
                                    "Statistique": ["Pompes", "Repas", "Eau (L)", "Sommeil (h)", "Temps (min)"],
                                    "Moi": [my_avg_pushups, my_avg_meals, my_avg_water, my_avg_sleep, my_avg_time],
                                    selected_user.username: [avg_pushups, avg_meals, avg_water, avg_sleep, avg_time]
                                })

                                st.subheader("📊 Comparaison des statistiques")
                                st.dataframe(df_comparison)

                                fig, ax = plt.subplots(figsize=(6, 4))
                                df_comparison.set_index("Statistique").plot(kind="bar", ax=ax)
                                ax.set_title(f"Comparaison: Moi vs {selected_user.username}")
                                st.pyplot(fig)

    # ----- Prédictions Gemini -----
    elif choice == "Gemini Predictions":
        st.header("Prédictions et Recommandations (Gemini)")
        if 'user_id' not in st.session_state:
            st.error("Veuillez vous connecter pour accéder aux prédictions.")
        else:
            user_id = st.session_state['user_id']
            entries = session.query(DataEntry).filter_by(user_id=user_id).all()
            if not entries:
                st.warning(
                    "Aucune donnée disponible pour générer une prédiction.")
            else:
                # Agrégation des données pour l'analyse
                avg_pushups = sum(e.pushups for e in entries) / len(entries)
                avg_meals = sum(e.meals_count for e in entries) / len(entries)
                avg_water = sum(e.water_intake for e in entries) / len(entries)
                avg_sleep = sum(e.sleep_hours for e in entries) / len(entries)
                avg_time = sum(e.time_spent for e in entries) / len(entries)

                user_data = {
                    "avg_pushups": avg_pushups,
                    "avg_meals": avg_meals,
                    "avg_water": avg_water,
                    "avg_sleep": avg_sleep,
                    "avg_time": avg_time
                }
                st.write("Données agrégées pour la prédiction :", user_data)
                prediction = gemini_predict(user_data)
                st.subheader("Résultat de la prédiction")
                st.write(f"**Niveau de risque :** {prediction['risk_level']}")
                st.write(
                    f"**Conditions potentielles :** {', '.join(prediction['potential_conditions'])}")
                st.write(
                    f"**Recommandations :** {prediction['recommendations']}")

    # ----- Paramètres utilisateur -----
    elif choice == "Paramètres":
        st.header("Paramètres")
        if 'user_id' not in st.session_state:
            st.error("Veuillez vous connecter pour accéder aux paramètres.")
        else:
            st.write(
                "Ici, vous pouvez gérer vos informations personnelles, modifier votre mot de passe, etc.")
            # À compléter selon les besoins


if __name__ == '__main__':
    main()
