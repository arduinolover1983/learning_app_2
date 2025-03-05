from flask import Flask, render_template, request, jsonify
import pandas as pd
import random


app = Flask(__name__)  # Start de flask web plugin

# Load your data (assuming it's in a DataFrame)
data = pd.read_csv("words_set3.csv", delimiter=";")  # Loads the CSV file into a pandas DataFrame with a custom delimiter (semicolon)
print(data)  # Prints the first few rows of the DataFrame to ensure it's loaded correctly

@app.route("/")  # This defines the route for the home page, which is the root of the web application
def home():
    # This checks if the 'category' column exists in the loaded data. If it doesn't, return an error message.
    if "category" not in data.columns:
        return "Error: 'category' column not found in dataset", 500

    # This retrieves the unique categorys from the 'category' column and converts them to a list
    categorys = data['category'].unique().tolist()

    # Renders the 'index.html' template and passes the list of categorys to it
    return render_template("index.html", categorys=categorys)

@app.route("/get_question", methods=["POST"])  # This route is for handling POST requests to fetch questions
def get_question():
    # Retrieves the selected category and mode (multiple choice or written) from the JSON body of the request
    selected_category = request.json.get("category")
    mode = request.json.get("mode")

    # Filters the DataFrame to include only the rows corresponding to the selected category
    category = data[data['category'] == selected_category]

    # If no data is found for the selected category, return an error
    if category.empty:
        return jsonify({"error": "No words found for this category"}), 400

    # Randomly selects one word from the filtered category data
    word = category.sample(1).iloc[0]
    correct_answer = word["nederlands_woord"]  # The correct translation (word in Dutch)

    # If the mode is "multiple_choice", prepare a set of choices (one correct + 3 incorrect)
    if mode == "multiple_choice":
        # Selects 3 incorrect answers by sampling from rows where the 'nederlands_woord' is not the correct answer
        wrong_answers = category[category["nederlands_woord"] != correct_answer] \
                            .sample(min(3, len(category) - 1))["nederlands_woord"].tolist()

        # Combines the incorrect answers with the correct answer, then shuffles the list to randomize order
        choices = wrong_answers + [correct_answer]
        random.shuffle(choices)

        # Returns the Afghan word, multiple choices, and the correct answer as a JSON response
        return jsonify({
            "afghan_word": word["afghaans_woord"],  # The word in Afghan language
            "choices": choices,  # List of multiple-choice options
            "correct_translation": correct_answer  # The correct translation of the Afghan word
        })

    # If the mode is not "multiple_choice", it's assumed to be "written" mode, so only the correct answer is returned
    return jsonify({
        "afghan_word": word["afghaans_woord"],  # The word in Afghan language
        "correct_translation": correct_answer  # The correct translation of the Afghan word
    })

if __name__ == "__main__":
    # Starts the Flask application on all available IPs (0.0.0.0) and port 5000, in debug mode
    app.run(host="0.0.0.0", port=5000, debug=True)
