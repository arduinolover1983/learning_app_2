from flask import Flask, render_template, request, jsonify, url_for, redirect
import pandas as pd
import random
import os
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    progress = db.Column(db.JSON)  # { "begroeting": 8/10, "eten": 3/5, ... }

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create tables
with app.app_context():
    db.create_all()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        user = User(username=username, password=password, progress={})
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return '''
    <form method="post">
        Username: <input name="username"><br>
        Password: <input type="password" name="password"><br>
        <button>Register</button>
    </form>
    '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('home'))
    return '''
    <form method="post">
        Username: <input name="username"><br>
        Password: <input type="password" name="password"><br>
        <button>Login</button>
    </form>
    '''

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))



# Load the CSV file
data = pd.read_csv("words_set3.csv", delimiter=";") 

@app.route("/")
@login_required  # Now requires login
def home():
    progress = current_user.progress or {}
    if "category" not in data.columns:
        return "Error: 'category' column not found in dataset", 500

    categorys = data['category'].unique().tolist()
    return render_template("index.html", categorys=categorys, progress=progress)

# In get_question, track progress
@app.route("/get_question", methods=["POST"])
@login_required
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
