from ai_manager import gemini_predict, evaluate_risk  # Assurez-vous que ces fonctions sont définies
from database import User, DataEntry, Follow, register, login
import streamlit as st
import datetime
import matplotlib.pyplot as plt
import pandas as pd
import json

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
                st.error("Identifiants incorrects")

    elif choice == "Inscription":
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

    # ----- Collecte des données -----
    elif choice == "Collecte des Données":
        st.header("Saisie de vos données quotidiennes")
        if 'user_id' not in st.session_state:
            st.error("Veuillez vous connecter pour saisir vos données.")
        else:
            user_id = st.session_state['user_id']
            date = st.date_input("Date", datetime.date.today())
            pushups = st.number_input("Nombre de pompes", min_value=0, step=1)
            meals_count = st.number_input("Nombre de repas", min_value=0, step=1)
            st.info("Saisissez les détails de vos repas au format JSON. Ex: {\"petit_dejeuner\": \"oeufs, toast\", \"dejeuner\": \"salade\"}")
            meals_details = st.text_area("Détails des repas", height=100)
            water_intake = st.number_input("Consommation d'eau (litres)", min_value=0.0, step=0.1, format="%.2f")
            sleep_hours = st.number_input("Heures de sommeil", min_value=0.0, step=0.5, format="%.1f")
            time_spent = st.number_input("Temps passé sur activités (en minutes)", min_value=0, step=1)
            if st.button("Enregistrer les données"):
                try:
                    # Si vous souhaitez stocker un dictionnaire, ne pas utiliser json.dumps ici
                    meals_json = json.loads(meals_details) if meals_details else {}
                except Exception as e:
                    st.error("Le format des détails des repas n'est pas un JSON valide.")
                    return
                new_entry = DataEntry(
                    user_id=user_id,
                    date=date,
                    pushups=pushups,
                    meals_count=meals_count,
                    meals_details=meals_json,
                    water_intake=water_intake,
                    sleep_hours=sleep_hours,
                    time_spent=time_spent
                )
                new_entry.save()
                st.success("Données enregistrées avec succès!")

    # ----- Analyse des données -----
    elif choice == "Analyse":
        st.header("Analyse de vos données")
        if 'user_id' not in st.session_state:
            st.error("Veuillez vous connecter pour accéder à l'analyse.")
        else:
            user_id = st.session_state['user_id']
            entries = DataEntry.find_by_user_id(user_id)
            if not entries:
                st.warning("Aucune donnée disponible pour l'analyse.")
            else:
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
            st.subheader("Suivre un utilisateur")
            follow_username = st.text_input("Nom d'utilisateur à suivre")
            if st.button("Suivre"):
                user_to_follow = User.find_by_username(follow_username)
                if user_to_follow:
                    if not Follow.find_one(user_id, str(user_to_follow._id)):
                        new_follow = Follow(follower_id=user_id, followed_id=str(user_to_follow._id))
                        new_follow.save()
                        st.success(f"Vous suivez désormais {follow_username}!")
                    else:
                        st.info("Vous suivez déjà cet utilisateur.")
                else:
                    st.error("Utilisateur non trouvé.")
            st.subheader("Vos amis")
            follows = Follow.find_by_follower_id(user_id)
            followed_ids = [f.followed_id for f in follows]
            if not followed_ids:
                st.info("Vous ne suivez personne actuellement.")
            else:
                followed_users = [User.find_by_id(uid) for uid in followed_ids]
                selected_user = None
                cols = st.columns(len(followed_users))
                for i, friend in enumerate(followed_users):
                    with cols[i]:
                        if st.button(friend.username, key=f"friend_{friend._id}"):
                            st.session_state.selected_user_id = str(friend._id)
                            st.session_state.comparison_mode = False
                if 'selected_user_id' in st.session_state:
                    selected_user = User.find_by_id(st.session_state.selected_user_id)
                if selected_user:
                    st.subheader(f"Statistiques de {selected_user.username}")
                    if st.button("Ne plus suivre"):
                        Follow.delete(user_id, str(selected_user._id))
                        st.success(f"Vous ne suivez plus {selected_user.username}.")
                        del st.session_state.selected_user_id
                        st.experimental_rerun()
                    entries = DataEntry.find_by_user_id(str(selected_user._id))
                    if not entries:
                        st.warning("Aucune donnée disponible pour cet utilisateur.")
                    else:
                        available_dates = [entry.date for entry in entries]
                        selected_date = st.selectbox("Sélectionnez une date", available_dates)
                        entry = next((e for e in entries if e.date == selected_date), None)
                        if entry:
                            st.markdown(f"""
                                <div class="stat-box">
                                    <h4>📅 Données du {entry.date}</h4>
                                    <p>💪 Pompes : <strong>{entry.pushups}</strong></p>
                                    <p>🍽 Repas : <strong>{entry.meals_count}</strong></p>
                                    <p>💧 Eau (L) : <strong>{entry.water_intake}</strong></p>
                                    <p>😴 Sommeil (h) : <strong>{entry.sleep_hours}</strong></p>
                                    <p>📱 Temps (min) : <strong>{entry.time_spent}</strong></p>
                                </div>
                            """, unsafe_allow_html=True)
                        if st.button("Voir les statistiques globales"):
                            avg_pushups = sum(e.pushups for e in entries) / len(entries)
                            avg_meals = sum(e.meals_count for e in entries) / len(entries)
                            avg_water = sum(e.water_intake for e in entries) / len(entries)
                            avg_sleep = sum(e.sleep_hours for e in entries) / len(entries)
                            avg_time = sum(e.time_spent for e in entries) / len(entries)
                            st.session_state.friend_global = {
                                "Pompes": avg_pushups,
                                "Repas": avg_meals,
                                "Eau": avg_water,
                                "Sommeil": avg_sleep,
                                "Temps": avg_time
                            }
                            st.session_state.show_global = True
                        if 'show_global' in st.session_state and st.session_state.show_global:
                            st.markdown(f"""
                                <div class="stat-box">
                                    <h4>📊 Statistiques globales de {selected_user.username}</h4>
                                    <p>💪 Pompes moyennes : <strong>{st.session_state.friend_global['Pompes']:.1f}</strong></p>
                                    <p>🍽 Repas moyens : <strong>{st.session_state.friend_global['Repas']:.1f}</strong></p>
                                    <p>💧 Eau moyenne : <strong>{st.session_state.friend_global['Eau']:.1f} L</strong></p>
                                    <p>😴 Sommeil moyen : <strong>{st.session_state.friend_global['Sommeil']:.1f} h</strong></p>
                                    <p>📱 Temps moyen : <strong>{st.session_state.friend_global['Temps']:.1f} min</strong></p>
                                </div>
                            """, unsafe_allow_html=True)
                            if st.button("Comparer avec mes statistiques"):
                                my_entries = DataEntry.find_by_user_id(user_id)
                                if my_entries:
                                    my_avg_pushups = sum(e.pushups for e in my_entries) / len(my_entries)
                                    my_avg_meals = sum(e.meals_count for e in my_entries) / len(my_entries)
                                    my_avg_water = sum(e.water_intake for e in my_entries) / len(my_entries)
                                    my_avg_sleep = sum(e.sleep_hours for e in my_entries) / len(my_entries)
                                    my_avg_time = sum(e.time_spent for e in my_entries) / len(my_entries)
                                    st.session_state.comparison = {
                                        "user": {
                                            "Pompes": my_avg_pushups,
                                            "Repas": my_avg_meals,
                                            "Eau": my_avg_water,
                                            "Sommeil": my_avg_sleep,
                                            "Temps": my_avg_time
                                        },
                                        "friend": st.session_state.friend_global
                                    }
                                    st.session_state.comparison_mode = True
                                    st.experimental_rerun()
                        if 'comparison_mode' in st.session_state and st.session_state.comparison_mode:
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown("""
                                    <div class="comparison-box">
                                        <h4>Vos statistiques</h4>
                                """, unsafe_allow_html=True)
                                st.write(f"💪 Pompes : {st.session_state.comparison['user']['Pompes']:.1f}")
                                st.write(f"🍽 Repas : {st.session_state.comparison['user']['Repas']:.1f}")
                                st.write(f"💧 Eau : {st.session_state.comparison['user']['Eau']:.1f} L")
                                st.write(f"😴 Sommeil : {st.session_state.comparison['user']['Sommeil']:.1f} h")
                                st.write(f"📱 Temps : {st.session_state.comparison['user']['Temps']:.1f} min")
                                st.markdown("</div>", unsafe_allow_html=True)
                            with col2:
                                st.markdown(f"""
                                    <div class="comparison-box">
                                        <h4>Statistiques de {selected_user.username}</h4>
                                """, unsafe_allow_html=True)
                                st.write(f"💪 Pompes : {st.session_state.comparison['friend']['Pompes']:.1f}")
                                st.write(f"🍽 Repas : {st.session_state.comparison['friend']['Repas']:.1f}")
                                st.write(f"💧 Eau : {st.session_state.comparison['friend']['Eau']:.1f} L")
                                st.write(f"😴 Sommeil : {st.session_state.comparison['friend']['Sommeil']:.1f} h")
                                st.write(f"📱 Temps : {st.session_state.comparison['friend']['Temps']:.1f} min")
                                st.markdown("</div>", unsafe_allow_html=True)
                            if st.button("Retour aux statistiques simples"):
                                del st.session_state.comparison_mode
                                st.experimental_rerun()

    # ----- Prédictions Gemini -----
    elif choice == "Gemini Predictions":
        st.header("Prédictions et Recommandations (Gemini)")
        if 'user_id' not in st.session_state:
            st.error("Veuillez vous connecter pour accéder aux prédictions.")
        else:
            user_id = st.session_state['user_id']
            entries = DataEntry.find_by_user_id(user_id)
            if not entries:
                st.warning("Aucune donnée disponible pour générer une prédiction.")
            else:
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
                st.write(f"**Conditions potentielles :** {', '.join(prediction['potential_conditions'])}")
                st.write(f"**Recommandations :** {prediction['recommendations']}")

    # ----- Paramètres utilisateur -----
    elif choice == "Paramètres":
        st.header("Paramètres")
        if 'user_id' not in st.session_state:
            st.error("Veuillez vous connecter pour accéder aux paramètres.")
        else:
            st.write("Ici, vous pouvez gérer vos informations personnelles, modifier votre mot de passe, etc.")
            # À compléter selon les besoins

if __name__ == '__main__':
    main()
