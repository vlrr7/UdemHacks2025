from google import genai


def generateContent(input_text):

    client = genai.Client(api_key="YOUR_API_KEY")
    response = client.models.generate_content(
        model="gemini-2.0-flash", contents=[{"text": input_text}])
    return response.text
