from google import genai
import streamlit as st


def generate_content(data):

    client = genai.Client(api_key= st.secrets.GEMINI_API_KEY)
    response = client.models.generate_content(
        model="gemini-2.0-flash", contents=f"""{str(data)}. These are the user's data for an application that tracks
        their routine and health conditions and predicts their risk level for potential conditions.
        
        Réponds uniquement avec les résultats demandés, sans aucun texte avant ou après la réponse. 
        Formate la réponse exactement comme ceci :
        
        Niveau de risque: (Faible, Modéré, Élevé)
        Conditions potentiels: (Liste des conditions possibles)
        Recommandations: (Conseils à suivre)
        
        Ne dis rien d'autre.
    """
    )
    return response.text
