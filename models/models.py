from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

#Set database path inside `instance/`
BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # models folder path
DB_PATH = os.path.join(BASE_DIR, "../instance/quiz_master.db")  # Go up one level and then enter instance folder

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'secret'

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)  # Used for login
    password = db.Column(db.String(60), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    qualification = db.Column(db.String(100), nullable=True)
    dob = db.Column(db.String(10), nullable=True)  # Format: YYYY-MM-DD
    role = db.Column(db.String(10), nullable=False, default='user')

# Subject Table
class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)

# Chapter Table
class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)

# Quiz Table
class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    date_of_quiz = db.Column(db.DateTime)
    remarks = db.Column(db.Text, nullable=True)

# Question Table
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    question_statement = db.Column(db.Text, nullable=False)
    option1 = db.Column(db.String(255), nullable=False)
    option2 = db.Column(db.String(255), nullable=False)
    option3 = db.Column(db.String(255), nullable=False)
    option4 = db.Column(db.String(255), nullable=False)
    correct_option = db.Column(db.Integer, nullable=False)  # 1, 2, 3, 4

# Score Table
class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    time_stamp_of_attempt = db.Column(db.DateTime)
    total_scored = db.Column(db.Integer, nullable=False)

# Function to Initialize Database
def initialize_database():
    with app.app_context():
        print("Creating database tables")
        try:
            db.create_all()
            print("Tables created successfully!")

            # Create Admin User if they don't exist
            if not User.query.filter_by(role='admin').first():
                admin_user = User(
                    email='admin@example.com',
                    password='admin123',
                    full_name='Admin',
                    role='admin'
                )
                db.session.add(admin_user)
                db.session.commit()
                print("Admin user created successfully!")
        except Exception as e:
            print(f"Error creating database: {e}")

if __name__ == "__main__":
    initialize_database()
