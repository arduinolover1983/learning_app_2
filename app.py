from flask import Flask, render_template, request, jsonify, url_for, redirect
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import pandas as pd
import random
import os
from datetime import datetime, timedelta
from sqlalchemy import distinct, func
from models import db, User, QuizAttempt, ProgressRecord, WordToRepeat

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///learning_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Load the CSV file
data = pd.read_csv("words_set3.csv", delimiter=";")


def get_word_by_id(word_id, expected_category=None):
    """Look up a word by its CSV row index and optionally validate its category."""
    try:
        word_index = int(word_id)
    except (TypeError, ValueError):
        return None

    if word_index not in data.index:
        return None

    word = data.loc[word_index]
    if expected_category and word["category"] != expected_category:
        return None

    return word


def refresh_progress(user_id, category):
    """Recalculate progress from recorded attempts instead of raw submission counts."""
    progress = ProgressRecord.query.filter_by(
        user_id=user_id,
        category=category
    ).first()

    if not progress:
        progress = ProgressRecord(user_id=user_id, category=category)
        db.session.add(progress)

    words_completed = db.session.query(func.count(distinct(QuizAttempt.word_id))).filter(
        QuizAttempt.user_id == user_id,
        QuizAttempt.category == category
    ).scalar() or 0

    words_learned = db.session.query(func.count(distinct(QuizAttempt.word_id))).filter(
        QuizAttempt.user_id == user_id,
        QuizAttempt.category == category,
        QuizAttempt.is_correct.is_(True)
    ).scalar() or 0

    progress.words_completed = words_completed
    progress.words_learned = words_learned
    return progress

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ==================== Authentication Routes ====================

@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.json.get("username")
        email = request.json.get("email")
        password = request.json.get("password")
        
        # Validation
        if not username or not email or not password:
            return jsonify({"error": "Missing fields"}), 400
        
        if User.query.filter_by(username=username).first():
            return jsonify({"error": "Username already exists"}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email already exists"}), 400
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        return jsonify({"success": True, "message": "Registration successful"}), 201
    
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == "POST":
        username = request.json.get("username")
        password = request.json.get("password")
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            return jsonify({"success": True, "redirect": url_for('dashboard')}), 200
        
        return jsonify({"error": "Invalid username or password"}), 401
    
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ==================== Dashboard & Progress ====================

@app.route("/dashboard")
@login_required
def dashboard():
    """Show user dashboard with progress and stats"""
    total_score = current_user.get_total_score()
    weekly_score = current_user.get_weekly_score()
    
    categories = data['category'].unique().tolist()
    progress_data = ProgressRecord.query.filter_by(user_id=current_user.id).all()
    
    return render_template("dashboard.html", 
                         total_score=total_score,
                         weekly_score=weekly_score,
                         categories=categories,
                         progress_data=progress_data)

@app.route("/api/get_progress")
@login_required
def get_progress():
    """API endpoint to get user progress"""
    category = request.args.get("category")
    
    progress = ProgressRecord.query.filter_by(
        user_id=current_user.id,
        category=category
    ).first()
    
    if not progress:
        return jsonify({"words_learned": 0, "words_completed": 0})
    
    return jsonify({
        "words_learned": progress.words_learned,
        "words_completed": progress.words_completed
    })

# ==================== Quiz Routes ====================

@app.route("/quiz")
@login_required
def quiz():
    """Load quiz page"""
    categorys = data['category'].unique().tolist()
    return render_template("quiz.html", categorys=categorys)

@app.route("/get_question", methods=["POST"])
@login_required
def get_question():
    """Get a quiz question (with smart repeat logic)"""
    selected_category = request.json.get("category")
    mode = request.json.get("mode")
    include_repeats = request.json.get("include_repeats", True)
    
    category_data = data[data['category'] == selected_category]
    if category_data.empty:
        return jsonify({"error": "No words found for this category"}), 400
    
    # Check if user has words to repeat
    words_to_repeat = WordToRepeat.query.filter_by(
        user_id=current_user.id,
        category=selected_category
    ).all()
    
    # Prioritize words to repeat
    if include_repeats and words_to_repeat:
        # 70% chance to show a word to repeat, 30% chance normal word
        if random.random() < 0.7:
            repeat_word = random.choice(words_to_repeat)
            repeated_word = get_word_by_id(repeat_word.word_id, selected_category)
            if repeated_word is not None:
                word = repeated_word
            else:
                word = category_data.sample(1).iloc[0]
        else:
            word = category_data.sample(1).iloc[0]
    else:
        word = category_data.sample(1).iloc[0]
    
    correct_answer = word["nederlands_woord"]
    word_id = str(word.name)  # Index from CSV
    
    # Generate multiple-choice answers
    wrong_answers = category_data[category_data["nederlands_woord"] != correct_answer] \
                        .sample(min(3, len(category_data) - 1))["nederlands_woord"].tolist()
    choices = wrong_answers + [correct_answer]
    random.shuffle(choices)
    
    # Handle audio
    audio_file = word.get("audio_file", None)
    audio_url = None
    if isinstance(audio_file, str) and audio_file.strip():
        audio_file_path = os.path.join("static", "audio", audio_file)
        if os.path.exists(audio_file_path):
            audio_url = url_for('static', filename=f"audio/{audio_file}")
    
    if mode == "listen_and_choose" and audio_url:
        return jsonify({
            "audio": audio_url,
            "choices": choices,
            "word_id": word_id,
            "afghan_word": word["afghaans_woord"]
        })
    
    return jsonify({
        "afghan_word": word["afghaans_woord"],
        "choices": choices,
        "word_id": word_id
    })

@app.route("/submit_answer", methods=["POST"])
@login_required
def submit_answer():
    """Submit and grade a quiz answer"""
    data_json = request.json
    category = data_json.get("category")
    word_id = data_json.get("word_id")
    user_answer = data_json.get("user_answer", "").strip().lower()
    word = get_word_by_id(word_id, category)

    if not category or word is None:
        return jsonify({"error": "Invalid question payload"}), 400

    correct_answer = str(word["nederlands_woord"]).strip().lower()
    
    is_correct = user_answer == correct_answer
    
    # Record the attempt
    attempt = QuizAttempt(
        user_id=current_user.id,
        category=category,
        word_id=word_id,
        correct_answer=correct_answer,
        user_answer=user_answer,
        is_correct=is_correct
    )
    db.session.add(attempt)
    
    # Update progress from authoritative quiz history.
    refresh_progress(current_user.id, category)
    
    # Handle word repeat tracking
    repeat_entry = WordToRepeat.query.filter_by(
        user_id=current_user.id,
        word_id=word_id,
        category=category
    ).first()
    
    if not is_correct:
        if not repeat_entry:
            new_repeat = WordToRepeat(
                user_id=current_user.id,
                word_id=word_id,
                category=category
            )
            db.session.add(new_repeat)
        else:
            repeat_entry.attempt_count += 1
    else:
        # Remove from repeat list if they got it right
        if repeat_entry:
            db.session.delete(repeat_entry)
    
    db.session.commit()
    
    return jsonify({
        "is_correct": is_correct,
        "message": "Correct!" if is_correct else f"Incorrect. The answer was: {correct_answer}",
        "total_score": current_user.get_total_score()
    })

# ==================== Leaderboard Routes ====================

@app.route("/leaderboard")
@login_required
def leaderboard():
    """Show leaderboard"""
    return render_template("leaderboard.html")

@app.route("/api/leaderboard/weekly")
@login_required
def api_leaderboard_weekly():
    """Get weekly leaderboard"""
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    # Query all users with their weekly scores
    users_scores = []
    users = User.query.all()
    
    for user in users:
        attempts = QuizAttempt.query.filter(
            QuizAttempt.user_id == user.id,
            QuizAttempt.created_at >= week_ago,
            QuizAttempt.is_correct == True
        ).count()
        
        if attempts > 0:
            users_scores.append({
                "username": user.username,
                "score": attempts,
                "is_current_user": user.id == current_user.id
            })
    
    # Sort by score descending
    users_scores.sort(key=lambda x: x["score"], reverse=True)
    
    # Add rank
    for i, entry in enumerate(users_scores, 1):
        entry["rank"] = i
    
    return jsonify(users_scores)

@app.route("/api/leaderboard/alltime")
@login_required
def api_leaderboard_alltime():
    """Get all-time leaderboard"""
    users_scores = []
    users = User.query.all()
    
    for user in users:
        score = user.get_total_score()
        if score > 0:
            users_scores.append({
                "username": user.username,
                "score": score,
                "is_current_user": user.id == current_user.id
            })
    
    # Sort by score descending
    users_scores.sort(key=lambda x: x["score"], reverse=True)
    
    # Add rank
    for i, entry in enumerate(users_scores, 1):
        entry["rank"] = i
    
    return jsonify(users_scores)

@app.route("/api/words_to_repeat")
@login_required
def api_words_to_repeat():
    """Get words user needs to repeat"""
    category = request.args.get("category")
    
    words_to_repeat = WordToRepeat.query.filter_by(
        user_id=current_user.id,
        category=category
    ).all()
    
    return jsonify({
        "total": len(words_to_repeat),
        "words": [{"word_id": w.word_id, "attempts": w.attempt_count} for w in words_to_repeat]
    })

# ==================== Error Handlers ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)
