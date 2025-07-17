import os
import json
from flask import Flask, jsonify, request
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env file for local development
# In production, variables should be set directly in the environment
load_dotenv()

app = Flask(__name__)

# Configure the Gemini API
try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")
    genai.configure(api_key=api_key)
    # Initialize the model
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    print("Gemini API configured successfully with model 'gemini-1.5-flash-latest'.")
except Exception as e:
    print(f"Error configuring Gemini API: {e}")
    model = None

@app.route('/')
def hello_world():
    return 'Hello, VibeSync Backend! Gemini model is {}.'.format('configured' if model else 'not configured')

@app.route('/api/party/suggestions', methods=['POST'])
def get_party_suggestions():
    """
    Generates food and drink suggestions for a party using the Gemini API.
    Expects a JSON body with 'theme', 'guest_count', and 'occasion'.
    """
    if not model:
        return jsonify({"error": "Gemini API not configured"}), 500

    # Get data from the request
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        party_theme = data.get('theme', 'a casual get-together')
        guest_count = data.get('guest_count', 10)
        occasion = data.get('occasion', 'a friendly party')

    except Exception as e:
        return jsonify({"error": "Invalid request body"}), 400

    # Construct the prompt for Gemini
    prompt = f"""
    You are a creative event planner. Generate food and drink suggestions for a party.
    The party details are as follows:
    - Occasion: {occasion}
    - Theme: {party_theme}
    - Number of Guests: {guest_count}

    Please provide a list of 3-5 food suggestions and 2-3 drink suggestions (including at least one non-alcoholic option).
    For each suggestion, provide a brief, fun description.

    Return the response as a JSON object with two keys: "food_suggestions" and "drink_suggestions".
    Each key should have a value of a list of objects, where each object has "name" and "description" keys.
    For example:
    {{
        "food_suggestions": [
            {{"name": "Taco Bar", "description": "A build-your-own taco station..."}}
        ],
        "drink_suggestions": [
            {{"name": "Margaritas", "description": "Classic lime margaritas..."}}
        ]
    }}
    """

    try:
        # Call the Gemini API
        response = model.generate_content(prompt)

        # Clean up the response from markdown/code blocks if present
        cleaned_response_text = response.text.strip().replace('```json', '').replace('```', '').strip()

        # Parse the JSON string from the response into a Python dict
        parsed_suggestions = json.loads(cleaned_response_text)

        # Return the parsed dictionary as a JSON response
        return jsonify(parsed_suggestions)

    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        print(f"Raw Gemini Response was: {response.text}")
        return jsonify({"error": "AI model returned malformed JSON"}), 500
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        # It's useful to see the raw response if it fails to parse
        try:
            print(f"Raw Gemini Response: {response.text}")
        except:
            pass
        return jsonify({"error": "Failed to get suggestions from AI model"}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
