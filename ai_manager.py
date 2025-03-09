from google import genai
import streamlit as st


def generate_content(data):

    client = genai.Client(api_key= st.secrets.GEMINI_API_KEY)
    response = client.models.generate_content(
        model="gemini-2.0-flash", contents=f"""{str(data)}. These are the user's data for an application that tracks
        their routine and health conditions and predicts their risk level for potential conditions.
        
        Respond only with the requested results, without any text before or after the answer.
        Format the response exactly like this (pay attention to spaces and line breaks):
        
        Niveau de risque: (Faible, Modéré, Élevé)
        Conditions potentiels: (Liste des conditions possibles, détaille)
        Recommandations générales: (Conseils à suivre généraux [overview])
        Recommandations particulieres: (Conseils à suivre plus précis et détaillé. Exemples : un plan d'entrainement complet pour une semaine ou un mois, ou changer les repas / les boissons, comment gerer le temps de sommeil, etc. Ne choisi que la plus pertinente !)


        Don't say anything else. Use bullet points if possible. Answer in French.
    """
    )
    print(response.text)
    return response.text
