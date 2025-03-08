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

            # Style CSS pour les boîtes
            st.markdown("""
                <style>
                    .stat-box { border: 1px solid #e0e0e0; padding: 20px; border-radius: 10px; margin: 10px 0; }
                    .comparison-box { border: 1px solid #d0d0d0; padding: 20px; border-radius: 10px; }
                </style>
            """, unsafe_allow_html=True)

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
            follows = session.query(Follow).filter_by(follower_id=user_id).all()
            followed_ids = [follow.followed_id for follow in follows]
            
            if not followed_ids:
                st.info("Vous ne suivez personne actuellement.")
            else:
                followed_users = session.query(User).filter(User.id.in_(followed_ids)).all()
                selected_user = None

                # Affichage des amis
                cols = st.columns(len(followed_users))
                for i, friend in enumerate(followed_users):
                    with cols[i]:
                        if st.button(friend.username, key=f"friend_{friend.id}"):
                            st.session_state.selected_user_id = friend.id
                            st.session_state.comparison_mode = False  # Reset comparaison

                # Gestion de la sélection
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
                        del st.session_state.selected_user_id
                        st.rerun()

                    # ---- Affichage des données ----
                    entries = session.query(DataEntry).filter_by(user_id=selected_user.id).order_by(DataEntry.date.desc()).all()
                    
                    if not entries:
                        st.warning("Aucune donnée disponible pour cet utilisateur.")
                    else:
                        # Affichage des données quotidiennes
                        available_dates = [entry.date for entry in entries]
                        selected_date = st.selectbox("Sélectionnez une date", available_dates)
                        entry = next(e for e in entries if e.date == selected_date)
                        
                        with st.container():
                            st.markdown('<div class="stat-box">', unsafe_allow_html=True)
                            st.write(f"📅 **Date:** {entry.date}")
                            st.write(f"💪 **Pompes:** {entry.pushups}")
                            st.write(f"🍽 **Repas:** {entry.meals_count}")
                            st.write(f"💧 **Eau (L):** {entry.water_intake}")
                            st.write(f"😴 **Sommeil (h):** {entry.sleep_hours}")
                            st.write(f"📱 **Temps passé (min):** {entry.time_spent}")
                            st.markdown('</div>', unsafe_allow_html=True)

                        # ---- Statistiques globales ----
                        if st.button("Voir les statistiques globales de cet utilisateur"):
                            avg_pushups = sum(e.pushups for e in entries) / len(entries)
                            avg_meals = sum(e.meals_count for e in entries) / len(entries)
                            avg_water = sum(e.water_intake for e in entries) / len(entries)
                            avg_sleep = sum(e.sleep_hours for e in entries) / len(entries)
                            avg_time = sum(e.time_spent for e in entries) / len(entries)

                            # Stockage des données pour la comparaison
                            st.session_state.friend_stats = {
                                "Pompes": avg_pushups,
                                "Repas": avg_meals,
                                "Eau (L)": avg_water,
                                "Sommeil (h)": avg_sleep,
                                "Temps (min)": avg_time
                            }
                            st.session_state.show_global = True

                        # Affichage des stats globales
                        if 'show_global' in st.session_state and st.session_state.show_global:
                            with st.container():
                                st.markdown('<div class="stat-box">', unsafe_allow_html=True)
                                st.write("📊 **Statistiques globales**")
                                st.write(f"💪 **Pompes moyennes:** {st.session_state.friend_stats['Pompes']:.1f}")
                                st.write(f"🍽 **Repas moyens:** {st.session_state.friend_stats['Repas']:.1f}")
                                st.write(f"💧 **Eau moyenne (L):** {st.session_state.friend_stats['Eau (L)']:.1f}")
                                st.write(f"😴 **Sommeil moyen (h):** {st.session_state.friend_stats['Sommeil (h)']:.1f}")
                                st.write(f"📱 **Temps passé moyen (min):** {st.session_state.friend_stats['Temps (min)']:.1f}")
                                st.markdown('</div>', unsafe_allow_html=True)

                                # ---- Comparaison ----
                                if st.button("Comparer avec mes statistiques"):
                                    my_entries = session.query(DataEntry).filter_by(user_id=user_id).all()
                                    if my_entries:
                                        my_avg_pushups = sum(e.pushups for e in my_entries)/len(my_entries)
                                        my_avg_meals = sum(e.meals_count for e in my_entries)/len(my_entries)
                                        my_avg_water = sum(e.water_intake for e in my_entries)/len(my_entries)
                                        my_avg_sleep = sum(e.sleep_hours for e in my_entries)/len(my_entries)
                                        my_avg_time = sum(e.time_spent for e in my_entries)/len(my_entries)

                                        # Stockage des données de comparaison
                                        st.session_state.comparison = {
                                            "user": {
                                                "Pompes": my_avg_pushups,
                                                "Repas": my_avg_meals,
                                                "Eau (L)": my_avg_water,
                                                "Sommeil (h)": my_avg_sleep,
                                                "Temps (min)": my_avg_time
                                            },
                                            "friend": st.session_state.friend_stats
                                        }
                                        st.session_state.comparison_mode = True
                                        st.rerun()

                        # Mode comparaison
                        if 'comparison_mode' in st.session_state and st.session_state.comparison_mode:
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                with st.container():
                                    st.markdown('<div class="comparison-box">', unsafe_allow_html=True)
                                    st.subheader("Mes statistiques")
                                    st.write(f"💪 Pompes: {st.session_state.comparison['user']['Pompes']:.1f}")
                                    st.write(f"🍽 Repas: {st.session_state.comparison['user']['Repas']:.1f}")
                                    st.write(f"💧 Eau: {st.session_state.comparison['user']['Eau (L)']:.1f}")
                                    st.write(f"😴 Sommeil: {st.session_state.comparison['user']['Sommeil (h)']:.1f}")
                                    st.write(f"📱 Temps: {st.session_state.comparison['user']['Temps (min)']:.1f}")
                                    st.markdown('</div>', unsafe_allow_html=True)

                            with col2:
                                with st.container():
                                    st.markdown('<div class="comparison-box">', unsafe_allow_html=True)
                                    st.subheader(f"Statistiques de {selected_user.username}")
                                    st.write(f"💪 Pompes: {st.session_state.comparison['friend']['Pompes']:.1f}")
                                    st.write(f"🍽 Repas: {st.session_state.comparison['friend']['Repas']:.1f}")
                                    st.write(f"💧 Eau: {st.session_state.comparison['friend']['Eau (L)']:.1f}")
                                    st.write(f"😴 Sommeil: {st.session_state.comparison['friend']['Sommeil (h)']:.1f}")
                                    st.write(f"📱 Temps: {st.session_state.comparison['friend']['Temps (min)']:.1f}")
                                    st.markdown('</div>', unsafe_allow_html=True)

                            # Option pour quitter le mode comparaison
                            if st.button("Retour aux statistiques simples"):
                                del st.session_state.comparison_mode
                                st.rerun()

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
