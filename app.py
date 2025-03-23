from flask import Flask, render_template, request, jsonify, url_for
import pandas as pd
import random
import os

app = Flask(__name__)

# Load the CSV file
data = pd.read_csv("words_set3.csv", delimiter=";") 

@app.route("/")
def home():
    if "category" not in data.columns:
        return "Error: 'category' column not found in dataset", 500

    categorys = data['category'].unique().tolist()
    return render_template("index.html", categorys=categorys)

@app.route("/get_question", methods=["POST"])
def get_question():
    selected_category = request.json.get("category")
    mode = request.json.get("mode")

    category = data[data['category'] == selected_category]
    if category.empty:
        return jsonify({"error": "No words found for this category"}), 400

    word = category.sample(1).iloc[0]
    correct_answer = word["nederlands_woord"]

    # Generate multiple-choice answers
    wrong_answers = category[category["nederlands_woord"] != correct_answer] \
                        .sample(min(3, len(category) - 1))["nederlands_woord"].tolist()
    choices = wrong_answers + [correct_answer]
    random.shuffle(choices)

    # Get the audio file (if any), handle missing or NaN values
    audio_file = word.get("audio_file", None)

    # Check if 'audio_file' exists and is a valid string
    if isinstance(audio_file, str) and audio_file.strip():  # Ensure it's a non-empty string
        audio_file_path = os.path.join("static", "audio", audio_file)
        if os.path.exists(audio_file_path):
            audio_url = url_for('static', filename=f"audio/{audio_file}")
        else:
            audio_url = None  # Audio file doesn't exist
    else:
        audio_url = None  # No valid audio file

    # If the mode is "listen_and_choose", return audio and choices
    if mode == "listen_and_choose" and audio_url:
        return jsonify({
            "audio": audio_url,  # Provide the audio file URL
            "choices": choices,
            "correct_translation": correct_answer
        })

    # Return the word's translation if it's not "listen_and_choose"
    return jsonify({
        "afghan_word": word["afghaans_woord"],  
        "choices": choices,
        "correct_translation": correct_answer
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
