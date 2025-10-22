# This will be the main file - code follows here


import os
import google.generativeai as genai
#DUMMYCODE! TESTING ONLY - AI GENERATED
# API-Key aus Umgebungsvariable
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# Einfacher Thought-Action-Observation Loop
while True:
    thought = input("Thought (Was willst du tun?): ")
    if thought.lower() in ["exit", "quit"]:
        break

    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(thought)
    print("Observation:", response.text)
