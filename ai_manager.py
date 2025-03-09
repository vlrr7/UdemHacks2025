from google import genai
import streamlit as st

# Configure the API key globally
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

def gemini_predict(data):
    """
    Calls Google Gemini API to predict risk level, potential conditions, and recommendations.
    """
    model = genai.GenerativeModel("gemini-1.5-flash")  # Ensure you use the correct model version
    response = model.generate_content(f"""{str(data)}. These are the user's data for an application that tracks
        their routine and health conditions and predicts their risk level for potential conditions.
        
        Réponds uniquement avec les résultats demandés, sans aucun texte avant ou après la réponse. 
        Formate la réponse exactement comme ceci (Attention aux fautes de frappe, et aux retour à la ligne):
        
        Niveau de risque: (Faible, Modéré, Élevé)
        Conditions potentiels: (Liste des conditions possibles)
        Recommandations: (Conseils à suivre)
        
        Ne dis rien d'autre.
    """)

    # Extract the response text correctly
    return response.text if response and hasattr(response, 'text') else "Erreur: Réponse invalide"

