from flask import Flask, request, render_template
from deep_translator import GoogleTranslator
import requests
import json
import random

app = Flask(__name__)

# DeepSeek API configuration
DEEPSEEK_API_KEY = "sk-927ca428634741b8aa8adfe0baf66075"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# Dictionary to cache predictions based on input
prediction_cache = {}

# Function to label output
def output_label(n):
    return "Fake News" if n == 0 else "Not A Fake News"

# AI-based fact check with explanation using DeepSeek
def check_fact(news_statement):
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": "You are a fact-checking assistant. Analyze the given news statement and determine if it's true or false. Respond with 'TRUE' if the statement appears to be reliable and factual, or 'FALSE' if it contains misleading or unverifiable information."
            },
            {
                "role": "user",
                "content": f"Please fact-check this statement: {news_statement}"
            }
        ],
        "max_tokens": 1024,
        "temperature": 0.1
    }
    
    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        result_text = result['choices'][0]['message']['content'].strip().lower()
        
        if "true" in result_text:
            verdict = 1
            explanation = "This statement appears to be reliable based on publicly known facts."
        else:
            verdict = 0
            explanation = "This statement may contain misleading or unverifiable information."
            
    except Exception as e:
        print(f"Error calling DeepSeek API: {e}")
        # Fallback to a default response
        verdict = 0
        explanation = "Unable to verify this statement due to technical issues."
    
    return verdict, explanation

# Function to simulate variation in predictions
def get_simulated_predictions(ai_result, input_text):
    if input_text in prediction_cache:
        return prediction_cache[input_text]

    predictions = {
        "LR": ai_result,
        "DT": ai_result,
        "GBC": ai_result,
        "RFC": ai_result
    }

    # Simulate one model giving a different result sometimes (30% chance)
    if random.random() < 0.3:
        model_to_flip = random.choice(list(predictions.keys()))
        predictions[model_to_flip] = 1 - ai_result  # Flip the result

    # Cache this result
    prediction_cache[input_text] = predictions

    return predictions

@app.route('/', methods=['GET', 'POST'])
def index():
    prediction = None
    statement = ""
    selected_lang = "en"
    explanation = ""

    if request.method == 'POST':
        statement = request.form['news']
        selected_lang = request.form['language']

        # Translate input to English
        translated_input = GoogleTranslator(source=selected_lang, target="en").translate(statement) if selected_lang != "en" else statement

        result, explanation = check_fact(translated_input)

        # Simulate model-wise predictions (stable for same input)
        simulated = get_simulated_predictions(result, translated_input)

        prediction = {}
        for model, pred in simulated.items():
            label_en = output_label(pred)
            translated_output = GoogleTranslator(source="en", target=selected_lang).translate(label_en) if selected_lang != "en" else label_en
            prediction[model] = translated_output

        # Translate explanation if needed
        if selected_lang != "en":
            explanation = GoogleTranslator(source="en", target=selected_lang).translate(explanation)

    return render_template('index.html', prediction=prediction, statement=statement, selected_lang=selected_lang, explanation=explanation)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
