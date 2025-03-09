from ai_manager import gemini_predict  # Assurez-vous que ces fonctions sont définies
from database import User, DataEntry, Follow, register, login
import streamlit as st
import datetime
import matplotlib.pyplot as plt
import pandas as pd
import json

def main():
    st.title("Connectez vous à HealthPro!")
    menu = ["Connexion", "Inscription", "Collecte des Données",
            "Analyse", "Social", "Gemini Predictions", "Paramètres"]
    # Configuration du menu latéral toujours ouvert
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Connexion"

    with st.sidebar:
        st.markdown("### Navigation")
        for page in menu:
            if st.button(page, key=f"menu_{page}"):
                st.session_state.current_page = page

    
    # ----- Page de connexion -----
    if st.session_state.current_page == "Connexion":
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

    elif st.session_state.current_page == "Inscription":
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
    elif st.session_state.current_page== "Collecte des Données":
        st.header("Saisie de vos données quotidiennes")
        if 'user_id' not in st.session_state:
            st.error("Veuillez vous connecter pour saisir vos données.")
        else:
            user_id = st.session_state['user_id']
            unformatted_date = st.date_input("Date", datetime.date.today())
            date = datetime.datetime.combine(unformatted_date, datetime.datetime.min.time())

            # Données générales
            st.subheader("Informations générales")
            age = st.number_input("Âge", min_value=0, step=1)
            height = st.number_input("Taille (cm)", min_value=50, max_value=250, step=1)
            weight = st.number_input("Poids (kg)", min_value=20.0, max_value=200.0, step=0.1)
            bmi = weight / ((height / 100) ** 2) if height > 0 else 0

            # Données quotidiennes
            st.subheader("Données quotidiennes")
            water = st.number_input("Eau consommée (L)", min_value=0.0, step=0.1)
            calories = st.number_input("Calories consommées", min_value=0, step=10)
            sleep = st.number_input("Heures de sommeil", min_value=0.0, step=0.5)
            activity_time = st.number_input("Temps d'activité physique (min)", min_value=0, step=1)

            # Données pour ainés (optionnelles)
            st.subheader("Pour les seniors (optionnel)")
            tug = st.number_input("Temps TUG (sec)", min_value=0.0, step=0.1, value=0.0)
            amsler = st.text_input("Résultat test visuel (Amsler)", value="Normal")
            hearing = st.text_input("Résultat test auditif", value="Normal")
            if st.button("Enregistrer les données"):
                new_entry = DataEntry(
                    user_id=user_id,
                    date=date,
                    age=age,
                    height=height,
                    weight=weight,
                    bmi=bmi,
                    water=water,
                    calories=calories,
                    sleep=sleep,
                    activity_time=activity_time,
                    tug=tug,
                    amsler=amsler,
                    hearing=hearing
                )
                new_entry.save()
                st.success("Données enregistrées avec succès!")

    # ----- Analyse des données -----
    elif st.session_state.current_page == "Analyse":
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
                    "Âge": entry.age,
                    "Taille (cm)": entry.height,
                    "Poids (kg)": entry.weight,
                    "IMC": entry.bmi,
                    "Eau (L)": entry.water,
                    "Calories": entry.calories,
                    "Sommeil (h)": entry.sleep,
                    "Activité (min)": entry.activity_time,
                    "TUG (sec)": entry.tug,
                    "Amsler": entry.amsler,
                    "Audition": entry.hearing
                } for entry in entries]
                df = pd.DataFrame(data)
                st.dataframe(df)
                # You can add plots here if needed, but the data structure has changed significantly
                # Example: st.line_chart(df[["date", "Sommeil (h)"]].set_index("date"))

    # ----- Interface sociale -----
    elif st.session_state.current_page == "Social":
        st.header("Réseau Social")
        if 'user_id' not in st.session_state:
            st.error("Veuillez vous connecter pour accéder aux fonctionnalités sociales.")
        else:
            user_id = st.session_state['user_id']
            if 'selected_user_id' not in st.session_state:
                st.session_state.selected_user_id = None
            st.subheader("Suivre un utilisateur")
            follow_username = st.text_input("Nom d'utilisateur à suivre")
            if st.button("Suivre"):
                user_to_follow = User.find_by_username(follow_username)
                if str(user_id) == str(user_to_follow["_id"]):
                    st.info("Vous ne pouvez pas vous suivre vous-même.")
                elif user_to_follow:
                    if not Follow.find_one(user_id, str(user_to_follow["_id"])):
                        new_follow = Follow(follower_id=user_id, followed_id=str(user_to_follow["_id"]))
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
                        if st.button(friend["username"], key=f"friend_{friend["_id"]}_{i}"):
                            st.session_state.selected_user_id = str(friend["_id"])
                            st.session_state.comparison_mode = False
                        if st.button(f"Ne plus suivre {friend["username"]}", key=f"unfollow_{friend["_id"]}_{i}"):
                            Follow.delete(user_id, str(friend["_id"]))
                            st.success(f"Vous ne suivez plus {friend["username"]}.")
                            del st.session_state.selected_user_id
                            st.rerun()
                if 'selected_user_id' in st.session_state:
                    selected_user = User.find_by_id(st.session_state.selected_user_id)
                if selected_user:
                    st.subheader(f"Statistiques de {selected_user["username"]}")
                    if st.button("Ne plus suivre"):
                        Follow.delete(user_id, str(selected_user["_id"]))
                        st.success(f"Vous ne suivez plus {selected_user["username"]}.")
                        del st.session_state.selected_user_id
    
                    entries = DataEntry.find_by_user_id(str(selected_user["_id"]))
                    if not entries:
                        st.warning("Aucune donnée disponible pour cet utilisateur.")
                    else:
                        st.markdown(f"""<style>
                            .stat-box {{
                                border: 1px solid #ccc;
                                padding: 10px;
                                margin: 10px;
                                border-radius: 5px;
                            }}
                            .stat-box h4 {{
                                margin-top: 0;
                                margin-bottom: 10px;
                            }}
                            .comparison-box {{
                                border: 1px solid #ccc;
                                padding: 10px;
                                margin: 10px;
                                border-radius: 5px;
                            }}
                            .comparison-box h4 {{
                                margin-top: 0;
                                margin-bottom: 10px;
                            }} </style>
                        """, unsafe_allow_html=True)
                        
                        available_dates = [entry.date for entry in entries]
                        selected_date = st.selectbox("Sélectionnez une date", available_dates)
                        entry = next((e for e in entries if e.date == selected_date), None)
                        if entry:
                            st.markdown(f"""
                                <div class="stat-box">
                                    <h4>📅 Données du {entry.date}</h4>
                                    <p>Âge : <strong>{entry.age}</strong></p>
                                    <p>Taille (cm) : <strong>{entry.height}</strong></p>
                                    <p>Poids (kg) : <strong>{entry.weight}</strong></p>
                                    <p>IMC : <strong>{entry.bmi:.2f}</strong></p>
                                    <p>💧 Eau (L) : <strong>{entry.water}</strong></p>
                                    <p>Calories : <strong>{entry.calories}</strong></p>
                                    <p>😴 Sommeil (h) : <strong>{entry.sleep}</strong></p>
                                    <p>Activité (min) : <strong>{entry.activity_time}</strong></p>
                                    <p>TUG (sec) : <strong>{entry.tug}</strong></p>
                                    <p>Amsler : <strong>{entry.amsler}</strong></p>
                                    <p>Audition : <strong>{entry.hearing}</strong></p>
                                </div>
                            """, unsafe_allow_html=True)
                        if st.button("Voir les statistiques globales"):
                            avg_age = sum(e.age for e in entries) / len(entries) if entries else 0
                            avg_height = sum(e.height for e in entries) / len(entries) if entries else 0
                            avg_weight = sum(e.weight for e in entries) / len(entries) if entries else 0
                            avg_bmi = sum(e.bmi for e in entries) / len(entries) if entries else 0
                            avg_water = sum(e.water for e in entries) / len(entries) if entries else 0
                            avg_calories = sum(e.calories for e in entries) / len(entries) if entries else 0
                            avg_sleep = sum(e.sleep for e in entries) / len(entries) if entries else 0
                            avg_activity_time = sum(e.activity_time for e in entries) / len(entries) if entries else 0
                            avg_tug = sum(e.tug for e in entries) / len(entries) if entries else 0
                            st.session_state.friend_global = {
                                "Âge": avg_age,
                                "Taille": avg_height,
                                "Poids": avg_weight,
                                "IMC": avg_bmi,
                                "Eau": avg_water,
                                "Calories": avg_calories,
                                "Sommeil": avg_sleep,
                                "Activité": avg_activity_time,
                                "TUG": avg_tug
                            }
                            st.session_state.show_global = True
                        if 'show_global' in st.session_state and st.session_state.show_global:
                            st.markdown(f"""
                                <div class="stat-box">
                                    <h4>📊 Statistiques globales de {selected_user["username"]}</h4>
                                    <p>Âge moyen : <strong>{st.session_state.friend_global['Âge']:.1f}</strong></p>
                                    <p>Taille moyenne : <strong>{st.session_state.friend_global['Taille']:.1f} cm</strong></p>
                                    <p>Poids moyen : <strong>{st.session_state.friend_global['Poids']:.1f} kg</strong></p>
                                    <p>IMC moyen : <strong>{st.session_state.friend_global['IMC']:.1f}</strong></p>
                                    <p>💧 Eau moyenne : <strong>{st.session_state.friend_global['Eau']:.1f} L</strong></p>
                                    <p>Calories moyennes : <strong>{st.session_state.friend_global['Calories']:.1f}</strong></p>
                                    <p>😴 Sommeil moyen : <strong>{st.session_state.friend_global['Sommeil']:.1f} h</strong></p>
                                    <p>Activité moyenne : <strong>{st.session_state.friend_global['Activité']:.1f} min</strong></p>
                                    <p>TUG moyen : <strong>{st.session_state.friend_global['TUG']:.1f} sec</strong></p>
                                </div>
                            """, unsafe_allow_html=True)
                            if st.button("Comparer avec mes statistiques"):
                                my_entries = DataEntry.find_by_user_id(user_id)
                                if my_entries:
                                    my_avg_age = sum(e.age for e in my_entries) / len(my_entries) if my_entries else 0
                                    my_avg_height = sum(e.height for e in my_entries) / len(my_entries) if my_entries else 0
                                    my_avg_weight = sum(e.weight for e in my_entries) / len(my_entries) if my_entries else 0
                                    my_avg_bmi = sum(e.bmi for e in my_entries) / len(my_entries) if my_entries else 0
                                    my_avg_water = sum(e.water for e in my_entries) / len(my_entries) if my_entries else 0
                                    my_avg_calories = sum(e.calories for e in my_entries) / len(my_entries) if my_entries else 0
                                    my_avg_sleep = sum(e.sleep for e in my_entries) / len(my_entries) if my_entries else 0
                                    my_avg_activity_time = sum(e.activity_time for e in my_entries) / len(my_entries) if my_entries else 0
                                    my_avg_tug = sum(e.tug for e in my_entries) / len(my_entries) if my_entries else 0
                                    st.session_state.comparison = {
                                        "user": {
                                            "Âge": my_avg_age,
                                            "Taille": my_avg_height,
                                            "Poids": my_avg_weight,
                                            "IMC": my_avg_bmi,
                                            "Eau": my_avg_water,
                                            "Calories": my_avg_calories,
                                            "Sommeil": my_avg_sleep,
                                            "Activité": my_avg_activity_time,
                                            "TUG": my_avg_tug
                                        },
                                        "friend": st.session_state.friend_global
                                    }
                                    st.session_state.comparison_mode = True
                
                        if 'comparison_mode' in st.session_state and st.session_state.comparison_mode:
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown("""
                                    <div class="comparison-box">
                                        <h4>Vos statistiques</h4>
                                """, unsafe_allow_html=True)
                                st.write(f"Âge : {st.session_state.comparison['user']['Âge']:.1f}")
                                st.write(f"Taille : {st.session_state.comparison['user']['Taille']:.1f} cm")
                                st.write(f"Poids : {st.session_state.comparison['user']['Poids']:.1f} kg")
                                st.write(f"IMC : {st.session_state.comparison['user']['IMC']:.1f}")
                                st.write(f"💧 Eau : {st.session_state.comparison['user']['Eau']:.1f} L")
                                st.write(f"Calories : {st.session_state.comparison['user']['Calories']:.1f}")
                                st.write(f"😴 Sommeil : {st.session_state.comparison['user']['Sommeil']:.1f} h")
                                st.write(f"Activité : {st.session_state.comparison['user']['Activité']:.1f} min")
                                st.write(f"TUG : {st.session_state.comparison['user']['TUG']:.1f} sec")
                                st.markdown("</div>", unsafe_allow_html=True)
                            with col2:
                                st.markdown(f"""
                                    <div class="comparison-box">
                                        <h4>Statistiques de {selected_user["username"]}</h4>
                                """, unsafe_allow_html=True)
                                st.write(f"Âge : {st.session_state.comparison['friend']['Âge']:.1f}")
                                st.write(f"Taille : {st.session_state.comparison['friend']['Taille']:.1f} cm")
                                st.write(f"Poids : {st.session_state.comparison['friend']['Poids']:.1f} kg")
                                st.write(f"IMC : {st.session_state.comparison['friend']['IMC']:.1f}")
                                st.write(f"💧 Eau : {st.session_state.comparison['friend']['Eau']:.1f} L")
                                st.write(f"Calories : {st.session_state.comparison['friend']['Calories']:.1f}")
                                st.write(f"😴 Sommeil : {st.session_state.comparison['friend']['Sommeil']:.1f} h")
                                st.write(f"Activité : {st.session_state.comparison['friend']['Activité']:.1f} min")
                                st.write(f"TUG : {st.session_state.comparison['friend']['TUG']:.1f} sec")
                                st.markdown("</div>", unsafe_allow_html=True)
                            if st.button("Retour aux statistiques simples"):
                                del st.session_state.comparison_mode

    # ----- Prédictions Gemini -----
    if st.session_state.current_page == "Gemini Predictions":
        st.header("Prédictions et Recommandations (Gemini)")
        if 'user_id' not in st.session_state:
            st.error("Veuillez vous connecter pour accéder aux prédictions.")
        else:
            user_id = st.session_state['user_id']
            entries = DataEntry.find_by_user_id(user_id)
            if not entries:
                st.warning("Aucune donnée disponible pour générer une prédiction.")
            else:
                avg_age = sum(e.age for e in entries) / len(entries) if entries else 0
                avg_height = sum(e.height for e in entries) / len(entries) if entries else 0
                avg_weight = sum(e.weight for e in entries) / len(entries) if entries else 0
                avg_bmi = sum(e.bmi for e in entries) / len(entries) if entries else 0
                avg_water = sum(e.water for e in entries) / len(entries) if entries else 0
                avg_calories = sum(e.calories for e in entries) / len(entries) if entries else 0
                avg_sleep = sum(e.sleep for e in entries) / len(entries) if entries else 0
                avg_activity_time = sum(e.activity_time for e in entries) / len(entries) if entries else 0
                avg_tug = sum(e.tug for e in entries) / len(entries) if entries else 0
                user_data = {
                    "age": avg_age,
                    "height": avg_height,
                    "weight": avg_weight,
                    "bmi": avg_bmi,
                    "water": avg_water,
                    "calories": avg_calories,
                    "sleep": avg_sleep,
                    "activity_time": avg_activity_time,
                    "tug": avg_tug
                }
                st.write("Données agrégées pour la prédiction :", user_data)
                prediction = gemini_predict(user_data)
                st.subheader("Résultat de la prédiction")
                st.write(f"{prediction}")

    # ----- Paramètres utilisateur -----
    elif st.session_state.current_page == "Paramètres":
        st.header("Paramètres")
        if 'user_id' not in st.session_state:
            st.error("Veuillez vous connecter pour accéder aux paramètres.")
        else:
            st.write("Ici, vous pouvez gérer vos informations personnelles, modifier votre mot de passe, etc.")
            # À compléter selon les besoins


if __name__ == '__main__':
    main()
