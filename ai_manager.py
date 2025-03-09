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
