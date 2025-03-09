import streamlit as st
from database import User, Follow, DataEntry

def display_social_page():
    st.title("HealthPro")
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
            if not user_to_follow:
                st.error("Utilisateur non trouvé.")
            elif str(user_id) == str(user_to_follow["_id"]):
                st.info("Vous ne pouvez pas vous suivre vous-même.")
            else:
                if not Follow.find_one(user_id, str(user_to_follow["_id"])):
                    new_follow = Follow(follower_id=user_id, followed_id=str(user_to_follow["_id"]))
                    new_follow.save()
                    st.success(f"Vous suivez désormais {follow_username}!")
                else:
                    st.info("Vous suivez déjà cet utilisateur.")

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
                                <p>Sexe : <strong>{entry.sexe}</strong></p>
                                <p>Taille (cm) : <strong>{entry.height}</strong></p>
                                <p>Poids (kg) : <strong>{entry.weight}</strong></p>
                                <p>IMC : <strong>{entry.bmi:.2f}</strong></p>
                                <p>💧 Eau (L) : <strong>{entry.water}</strong></p>
                                <p>Calories : <strong>{entry.calories}</strong></p>
                                <p>😴 Sommeil (h) : <strong>{entry.sleep}</strong></p>
                                <p>Activité (min) : <strong>{entry.activity_time}</strong></p>
                                <p>TUG (sec) : <strong>{entry.timed_up_and_go_test}</strong></p>
                                <p>Amsler : <strong>{entry.amsler}</strong></p>
                                <p>Audition : <strong>{entry.hearing}</strong></p>
                            </div>
                        """, unsafe_allow_html=True)
                        if st.button("Voir les statistiques globales"):
                            entries = DataEntry.find_by_user_id(str(selected_user["_id"]))
                            if entries:
                                # Obtenir la dernière entrée
                                latest_entry = max(entries, key=lambda x: x.date)
                                st.session_state.friend_global = {
                                    "Âge": latest_entry.age,
                                    "Taille": latest_entry.height,
                                    "Poids": latest_entry.weight,
                                    "IMC": latest_entry.bmi,
                                    "Eau": latest_entry.water,
                                    "Calories": latest_entry.calories,
                                    "Sommeil": latest_entry.sleep,
                                    "Activité": latest_entry.activity_time,
                                    "TUG": latest_entry.timed_up_and_go_test
                                }
                                st.session_state.show_global = True
                            else:
                                st.warning("Aucune donnée disponible pour cet utilisateur.")


                        if 'show_global' in st.session_state and st.session_state.show_global:
                            st.markdown(f"""
                                <div class="stat-box">
                                    <h4>📊 Dernières statistiques de {selected_user["username"]}</h4>
                                    <p>Âge : <strong>{st.session_state.friend_global['Âge']}</strong></p>
                                    <p>Taille : <strong>{st.session_state.friend_global['Taille']} cm</strong></p>
                                    <p>Poids : <strong>{st.session_state.friend_global['Poids']} kg</strong></p>
                                    <p>IMC : <strong>{st.session_state.friend_global['IMC']:.1f}</strong></p>
                                    <p>💧 Eau : <strong>{st.session_state.friend_global['Eau']} L</strong></p>
                                    <p>Calories : <strong>{st.session_state.friend_global['Calories']}</strong></p>
                                    <p>😴 Sommeil : <strong>{st.session_state.friend_global['Sommeil']} h</strong></p>
                                    <p>Activité : <strong>{st.session_state.friend_global['Activité']} min</strong></p>
                                    <p>TUG : <strong>{st.session_state.friend_global['TUG']} sec</strong></p>
                                </div>
                            """, unsafe_allow_html=True)

                        if st.button("Comparer avec mes statistiques"):
                            my_entries = DataEntry.find_by_user_id(user_id)
                            if my_entries:
                                # Obtenir ma dernière entrée
                                latest_my_entry = max(my_entries, key=lambda x: x.date)
                                my_data = {
                                    "Âge": latest_my_entry.age,
                                    "Taille": latest_my_entry.height,
                                    "Poids": latest_my_entry.weight,
                                    "IMC": latest_my_entry.bmi,
                                    "Eau": latest_my_entry.water,
                                    "Calories": latest_my_entry.calories,
                                    "Sommeil": latest_my_entry.sleep,
                                    "Activité": latest_my_entry.activity_time,
                                    "TUG": latest_my_entry.timed_up_and_go_test
                                }
                                st.session_state.comparison = {
                                    "user": my_data,
                                    "friend": st.session_state.friend_global
                                }
                                st.session_state.comparison_mode = True
            
                    if 'comparison_mode' in st.session_state and st.session_state.comparison_mode:
                        col1, col2 = st.columns(2)
                        with col1 as c:
                            container = st.container(border=True, border_radius=10)
                            container.write(f"Âge : {st.session_state.comparison['user']['Âge']:.1f}")
                            container.write(f"Taille : {st.session_state.comparison['user']['Taille']:.1f} cm")
                            container.write(f"Poids : {st.session_state.comparison['user']['Poids']:.1f} kg")
                            container.write(f"IMC : {st.session_state.comparison['user']['IMC']:.1f}")
                            container.write(f"💧 Eau : {st.session_state.comparison['user']['Eau']:.1f} L")
                            container.write(f"Calories : {st.session_state.comparison['user']['Calories']:.1f}")
                            container.write(f"😴 Sommeil : {st.session_state.comparison['user']['Sommeil']:.1f} h")
                            container.write(f"Activité : {st.session_state.comparison['user']['Activité']:.1f} min")
                            container.write(f"TUG : {st.session_state.comparison['user']['TUG']:.1f} sec")

                        with col2:
                            container = st.container(border=True, border_radius=10)
                            container.write(f"Âge : {st.session_state.comparison['friend']['Âge']:.1f}")
                            container.write(f"Taille : {st.session_state.comparison['friend']['Taille']:.1f} cm")
                            container.write(f"Poids : {st.session_state.comparison['friend']['Poids']:.1f} kg")
                            container.write(f"IMC : {st.session_state.comparison['friend']['IMC']:.1f}")
                            container.write(f"💧 Eau : {st.session_state.comparison['friend']['Eau']:.1f} L")
                            container.write(f"Calories : {st.session_state.comparison['friend']['Calories']:.1f}")
                            container.write(f"😴 Sommeil : {st.session_state.comparison['friend']['Sommeil']:.1f} h")
                            container.write(f"Activité : {st.session_state.comparison['friend']['Activité']:.1f} min")
                            container.write(f"TUG : {st.session_state.comparison['friend']['TUG']:.1f} sec")
                            
                        if st.button("Retour aux statistiques simples"):
                            del st.session_state.comparison_mode