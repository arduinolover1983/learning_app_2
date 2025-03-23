from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User account model"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    quiz_attempts = db.relationship('QuizAttempt', backref='user', lazy=True, cascade='all, delete-orphan')
    progress_records = db.relationship('ProgressRecord', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and store password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def get_total_score(self):
        """Calculate total score from all quiz attempts"""
        attempts = QuizAttempt.query.filter_by(user_id=self.id).all()
        return sum(1 for attempt in attempts if attempt.is_correct)
    
    def get_weekly_score(self):
        """Calculate score from the last 7 days"""
        week_ago = datetime.utcnow() - timedelta(days=7)
        attempts = QuizAttempt.query.filter(
            QuizAttempt.user_id == self.id,
            QuizAttempt.created_at >= week_ago
        ).all()
        return sum(1 for attempt in attempts if attempt.is_correct)


class QuizAttempt(db.Model):
    """Track each quiz attempt"""
    __tablename__ = 'quiz_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    category = db.Column(db.String(50), nullable=False)
    word_id = db.Column(db.String(100), nullable=False)  # CSV row number or identifier
    correct_answer = db.Column(db.String(255), nullable=False)
    user_answer = db.Column(db.String(255), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<QuizAttempt {self.user_id} - {self.word_id}>'


class ProgressRecord(db.Model):
    """Track learning progress"""
    __tablename__ = 'progress_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    category = db.Column(db.String(50), nullable=False)
    words_learned = db.Column(db.Integer, default=0)
    words_completed = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'category', name='unique_user_category'),)


class WordToRepeat(db.Model):
    """Track words that user got wrong (needs to be repeated)"""
    __tablename__ = 'words_to_repeat'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    word_id = db.Column(db.String(100), nullable=False)  # CSV row number
    category = db.Column(db.String(50), nullable=False)
    attempt_count = db.Column(db.Integer, default=1)
    last_attempted = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'word_id', name='unique_user_word'),)