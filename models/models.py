from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()  # Not binding it to the app yet

# User Table
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)  # Used for login
    password = db.Column(db.String(60), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    qualification = db.Column(db.String(100), nullable=True)
    dob = db.Column(db.String(10), nullable=True)                   # Format: YYYY-MM-DD
    role = db.Column(db.String(10), nullable=False, default='user') # admin or user

# Subject Table
class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)

    chapters = db.relationship('Chapter', backref='subject', cascade="all, delete-orphan")

# Chapter Table
class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False) # Link to subject
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)

# Quiz Table
class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False) # Link to Chapter
    date_of_quiz = db.Column(db.DateTime, nullable=False)
    remarks = db.Column(db.String(255), nullable=True)

    # Relationship to Chapter
    chapter = db.relationship('Chapter', backref=db.backref('quizzes', lazy=True))
    questions = db.relationship('Question', backref='quiz', lazy=True)

# Question Table
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False) # Link to Quiz
    question_statement = db.Column(db.Text, nullable=False)
    option1 = db.Column(db.String(255), nullable=False)
    option2 = db.Column(db.String(255), nullable=False)
    option3 = db.Column(db.String(255), nullable=False)
    option4 = db.Column(db.String(255), nullable=False)
    correct_option = db.Column(db.Integer, nullable=False)  # 1, 2, 3, 4

# Score Table
class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False) # Link to Quiz
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Link to User
    time_stamp_of_attempt = db.Column(db.DateTime, default=datetime.utcnow)
    total_scored = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    selected_answers = db.Column(db.Text, nullable=False)  # Store answers as JSON string

    # Relationships
    user = db.relationship('User', backref=db.backref('scores', lazy=True))
    quiz = db.relationship('Quiz', backref=db.backref('scores', lazy=True))

    def set_selected_answers(self, answers):
        """ Store answers as JSON """
        self.selected_answers = json.dumps(answers)

    def get_selected_answers(self):
        """ Retrieve answers as dictionary """
        return json.loads(self.selected_answers) if self.selected_answers else {}
