from flask import Flask, render_template, request, jsonify
import pandas as pd
import random

app = Flask(__name__)

# Load the words data
data = pd.read_csv("test_set.csv", delimiter=";")

@app.route("/")
def home():
    categories = data['categorie'].unique()
    return "<h1>Hello, Flask is working! 🚀</h1>"

@app.route("/get_question", methods=["POST"])
def get_question():
    selected_category = request.json.get("category")
    category_data = data[data['categorie'] == selected_category]

    if category_data.empty:
        return jsonify({"error": "No words found for this category"}), 400
    
    word = category_data.sample(1).iloc[0]
    return jsonify({
        "afghan_word": word["afghaans_woord"],
        "correct_translation": word["nederlands_woord"]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

