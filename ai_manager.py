from google import genai
import streamlit as st


api_key = "test" # st.secrets["GEMINI_API_KEY"]
# -----------------------------
# Fonction de simulation d'appel à l'API Gemini
# -----------------------------


def gemini_predict(data):
    """
    Cette fonction simule un appel à l'API Gemini.
    Pour une intégration réelle, utilisez requests pour envoyer vos données à l'API.
    """
    # Ici, nous retournons une réponse fictive :
    client = genai.Client(api_key=st.secrets.GEMINI_API_KEY)
    response = client.models.generate_content(
        model="gemini-2.0-flash", contents= f"""{str(data)}. These are the user's data for an application that tracks
        what a routine and health conditions and is able to predict his risk level of found conditions.
       Réponds uniquement avec les résultats demandés, sans aucun texte avant ou après la réponse. 
        Formate la réponse exactement comme ceci :

Niveau de risque: (Faible, Modéré, Élevé)
Conditions potentiels: (Liste des conditions possibles)
Recommandations: (Conseils à suivre)

Ne dis rien d'autre.""")
    return response.text

    # prediction = {
    #     "risk_level": "Faible",
    #     "potential_conditions": ["Aucune anomalie détectée"],
    #     "recommendations": "Continuez à suivre un régime équilibré et à pratiquer une activité physique régulière."
    # }
    # return prediction


def evaluate_risk(data):
    risk_score = 0
    conditions = []
    recommendations = []

    # --- Évaluation des facteurs de risque ---

    # Manque de sommeil
    if data["avg_sleep"] < 5:
        risk_score += 3
        conditions.append("Manque de sommeil sévère")
        recommendations.append(
            "Essayez de dormir au moins 7 à 8 heures par nuit.")

    elif 5 <= data["avg_sleep"] < 6:
        risk_score += 1
        conditions.append("Léger manque de sommeil")
        recommendations.append("Essayez d'améliorer votre hygiène de sommeil.")

    # Hydratation insuffisante
    if data["avg_water"] < 1.0:
        risk_score += 2
        conditions.append("Hydratation insuffisante")
        recommendations.append("Buvez au moins 2 litres d'eau par jour.")

    elif 1.0 <= data["avg_water"] < 1.5:
        risk_score += 1
        conditions.append("Hydratation modérée")
        recommendations.append(
            "Augmentez légèrement votre consommation d'eau.")

    # Activité physique faible
    if data["avg_pushups"] == 0:
        risk_score += 3
        conditions.append("Aucune activité physique")
        recommendations.append(
            "Essayez d'ajouter au moins 10 minutes d'exercice par jour.")

    elif 1 <= data["avg_pushups"] < 5:
        risk_score += 1
        conditions.append("Faible activité physique")
        recommendations.append(
            "Augmentez votre niveau d'exercice progressivement.")

    # Sédentarité élevée
    if data["avg_time"] > 300:
        risk_score += 2
        conditions.append("Mode de vie sédentaire")
        recommendations.append(
            "Réduisez le temps assis et bougez toutes les heures.")

    # Alimentation irrégulière
    if data["avg_meals"] == 0:
        risk_score += 3
        conditions.append("Aucun repas enregistré")
        recommendations.append(
            "Ne sautez pas les repas, essayez de manger 3 fois par jour.")

    elif data["avg_meals"] == 1:
        risk_score += 2
        conditions.append("Alimentation insuffisante")
        recommendations.append(
            "Augmentez votre apport alimentaire pour maintenir votre énergie.")

    # --- Détermination du niveau de risque ---
    if risk_score >= 7:
        risk_level = "Élevé"
    elif 4 <= risk_score < 7:
        risk_level = "Modéré"
    else:
        risk_level = "Faible"

    # S'assurer qu'il y a au moins une condition affichée
    if not conditions:
        conditions.append("Aucune anomalie détectée")
        recommendations.append(
            "Continuez vos bonnes habitudes de vie.")

    return {
        "risk_level": risk_level,
        "potential_conditions": conditions,
        "recommendations": " ".join(recommendations)
    }
