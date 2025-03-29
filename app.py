from flask import Flask, render_template, request, redirect, url_for, session
from models.models import db, User, Subject, Chapter, Quiz, Question, Score
import os
from datetime import datetime
import json

app = Flask(__name__)

# Database Path Setup
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "instance/quiz_master.db")

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'  # /// means use absolute path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False            # Modification to objects not tracked
app.config['SECRET_KEY'] = 'secret'                             # Used for session

db.init_app(app)  # Database is initialized

# Function to check admin authentication
def admin_required():
    return "user_id" in session and session["role"] == "admin"

# ====================== ADMIN USER INITIALIZATION ====================

def initialize_admin():
    with app.app_context():
        db.create_all()  # Create database tables
        print("Database Tables Created")
        
        # Check if an admin user exists
        existing_admin = User.query.filter_by(role='admin').first()
        
        if not existing_admin:
            admin_user = User(
                email='admin@example.com',
                password='admin123',  # Change this password in production
                full_name='Admin',
                role='admin'
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created successfully!")


# ====================== LOGIN/REGISTER ======================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        full_name = request.form["full_name"]
        qualification = request.form["qualification"]
        dob = request.form["dob"]

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return f"<script>alert('Email already registered!'); window.location.href='{url_for('register')}';</script>"

        new_user = User(email=email, password=password, full_name=full_name,
                        qualification=qualification, dob=dob, role="user")
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and user.password == password:
            session["user_id"] = user.id
            session["role"] = user.role

            return redirect(url_for("admin_dashboard") if user.role == "admin" else url_for("user_dashboard"))
        else:
            return f"<script>alert('Incorrect Details'); window.location.href='{url_for('login')}';</script>"

    return render_template("login.html")

# ====================== DASHBOARDS ======================

@app.route("/admin_dashboard")
def admin_dashboard():
    if not admin_required():
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])
    return render_template("admin_dashboard.html", user=user)

@app.route("/user_dashboard")
def user_dashboard():
    if "user_id" not in session or session["role"] != "user":
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])
    subjects = Subject.query.all()
    return render_template("user_dashboard.html", user=user, subjects=subjects)

# ====================== ADMIN CRUD FOR SUBJECTS, CHAPTERS AND QUIZZES ======================

# Manage Subjects
@app.route("/admin/subjects", methods=["GET", "POST"])
def manage_subjects():
    if not admin_required():
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        new_subject = Subject(name=name, description=description)
        db.session.add(new_subject)
        db.session.commit()

    subjects = Subject.query.all()
    return render_template("manage_subjects.html", subjects=subjects)

# Delete Subject
@app.route("/admin/subjects/delete/<int:subject_id>")
def delete_subject(subject_id):
    if not admin_required():
        return redirect(url_for("login"))

    subject = Subject.query.get(subject_id)
    db.session.delete(subject)
    db.session.commit()
    return redirect(url_for("manage_subjects"))

# Manage Chapters
@app.route("/admin/chapters/<int:subject_id>", methods=["GET", "POST"])
def manage_chapters(subject_id):
    if not admin_required():
        return redirect(url_for("login"))

    subject = Subject.query.get(subject_id)
    
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        new_chapter = Chapter(subject_id=subject_id, name=name, description=description)
        db.session.add(new_chapter)
        db.session.commit()

    chapters = Chapter.query.filter_by(subject_id=subject_id).all()
    return render_template("manage_chapters.html", subject=subject, chapters=chapters)

# Delete Chapter
@app.route("/admin/chapters/delete/<int:chapter_id>")
def delete_chapter(chapter_id):
    if not admin_required():
        return redirect(url_for("login"))

    chapter = Chapter.query.get(chapter_id)
    db.session.delete(chapter)
    db.session.commit()
    return redirect(url_for("manage_subjects"))

# Manage Quizzes
@app.route("/admin/quizzes/<int:chapter_id>", methods=["GET", "POST"])
def manage_quizzes(chapter_id):
    if not admin_required():
        return redirect(url_for("login"))

    chapter = Chapter.query.get(chapter_id)

    if request.method == "POST":
        date_of_quiz_str = request.form["date_of_quiz"]  # Get date as string
        remarks = request.form["remarks"]

        try:
            # Convert string to datetime.date object
            date_of_quiz = datetime.strptime(date_of_quiz_str, "%Y-%m-%d").date()
        except ValueError:
            return redirect(url_for("manage_quizzes", chapter_id=chapter_id))

        new_quiz = Quiz(chapter_id=chapter_id, date_of_quiz=date_of_quiz, remarks=remarks)
        db.session.add(new_quiz)
        db.session.commit()

    quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()
    return render_template("manage_quizzes.html", chapter=chapter, quizzes=quizzes)

# Delete Quiz
@app.route("/admin/quizzes/delete/<int:quiz_id>")
def delete_quiz(quiz_id):
    if not admin_required():
        return redirect(url_for("login"))

    quiz = Quiz.query.get(quiz_id)
    db.session.delete(quiz)
    db.session.commit()
    return redirect(url_for("manage_subjects"))

# Manage Questions
@app.route("/admin/questions/<int:quiz_id>", methods=["GET", "POST"])
def manage_questions(quiz_id):
    if not admin_required():
        return redirect(url_for("login"))

    quiz = Quiz.query.get(quiz_id)

    if request.method == "POST":
        question_statement = request.form["question_statement"]
        option1 = request.form["option1"]
        option2 = request.form["option2"]
        option3 = request.form["option3"]
        option4 = request.form["option4"]
        correct_option = int(request.form["correct_option"])

        new_question = Question(
            quiz_id=quiz_id,
            question_statement=question_statement,
            option1=option1,
            option2=option2,
            option3=option3,
            option4=option4,
            correct_option=correct_option
        )
        db.session.add(new_question)
        db.session.commit()

    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    return render_template("manage_questions.html", quiz=quiz, questions=questions)

# Delete Question
@app.route("/admin/questions/delete/<int:question_id>")
def delete_question(question_id):
    if not admin_required():
        return redirect(url_for("login"))

    question = Question.query.get(question_id)
    db.session.delete(question)
    db.session.commit()
    return redirect(url_for("manage_questions", quiz_id=question.quiz_id))

# Edit Subject
@app.route("/admin/subjects/edit/<int:subject_id>", methods=["GET", "POST"])
def edit_subject(subject_id):
    if not admin_required():
        return redirect(url_for("login"))

    subject = Subject.query.get(subject_id)
    if not subject:
        return redirect(url_for("manage_subjects"))

    if request.method == "POST":
        subject.name = request.form["name"]
        subject.description = request.form["description"]
        db.session.commit()
        return redirect(url_for("manage_subjects"))

    return render_template("edit_subject.html", subject=subject)

# Edit Chapter
@app.route("/admin/chapters/edit/<int:chapter_id>", methods=["GET", "POST"])
def edit_chapter(chapter_id):
    if not admin_required():
        return redirect(url_for("login"))

    chapter = Chapter.query.get(chapter_id)
    if not chapter:
        return redirect(url_for("manage_subjects"))

    if request.method == "POST":
        chapter.name = request.form["name"]
        chapter.description = request.form["description"]
        db.session.commit()
        return redirect(url_for("manage_chapters", subject_id=chapter.subject_id))

    return render_template("edit_chapter.html", chapter=chapter)


# Edit Quiz
@app.route("/admin/quizzes/edit/<int:quiz_id>", methods=["GET", "POST"])
def edit_quiz(quiz_id):
    if not admin_required():
        return redirect(url_for("login"))

    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return redirect(url_for("manage_subjects"))

    if request.method == "POST":
        quiz.date_of_quiz = datetime.strptime(request.form["date_of_quiz"], "%Y-%m-%d")
        quiz.remarks = request.form["remarks"]
        db.session.commit()
        return redirect(url_for("manage_quizzes", chapter_id=quiz.chapter_id))

    return render_template("edit_quiz.html", quiz=quiz)

# Edit Question
@app.route("/admin/questions/edit/<int:question_id>", methods=["GET", "POST"])
def edit_question(question_id):
    if not admin_required():
        return redirect(url_for("login"))

    question = Question.query.get(question_id)
    if not question:
        return redirect(url_for("manage_questions", quiz_id=question.quiz_id))

    if request.method == "POST":
        question.question_statement = request.form["question_statement"]
        question.option1 = request.form["option1"]
        question.option2 = request.form["option2"]
        question.option3 = request.form["option3"]
        question.option4 = request.form["option4"]
        question.correct_option = int(request.form["correct_option"])
        db.session.commit()
        return redirect(url_for("manage_questions", quiz_id=question.quiz_id))

    return render_template("edit_question.html", question=question)



# View Users
@app.route("/admin/users")
def view_users():
    if not admin_required():
        return redirect(url_for("login"))

    users = User.query.all()
    for user in users:
        quiz_attempts = Score.query.filter_by(user_id=user.id).all()   # Object with all quiz attemts of this user
        total_score = sum(attempt.total_scored for attempt in quiz_attempts) # Total correct questions
        total_questions = sum(attempt.total_questions for attempt in quiz_attempts) # Total no. of questions
        
        if total_questions > 0:
            user.total_percentage = (total_score / total_questions) * 100
        else:
            user.total_percentage = None  # No attempts yet

    return render_template("view_users.html", users=users)

#================================= LOGOUT ========================================

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

#============================= USER ROUTES ========================================

# View Quizzes
@app.route("/view_quizzes/<int:subject_id>")
def view_quizzes(subject_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    subject = Subject.query.get(subject_id)

    if not subject:
        return "Subject not found", 404

    chapters = Chapter.query.filter_by(subject_id=subject_id).all()

    quizzes_by_chapter = {} # Object to store individual quiz data
    now = datetime.now() # To know if quiz should be attemptable
    user_scores = {}  # Object to store user scores for each quiz

    for chapter in chapters:
        quizzes = Quiz.query.filter(
            Quiz.chapter_id == chapter.id,
        ).all()
        quizzes_by_chapter[chapter.id] = quizzes

        # Fetch scores for each quiz for the current user
        for quiz in quizzes:
            score_record = Score.query.filter_by(user_id=user_id, quiz_id=quiz.id).order_by(Score.time_stamp_of_attempt.desc()).first()
            user_scores[quiz.id] = score_record.total_scored if score_record else None # Object storing User scores for each quiz

    return render_template("view_quizzes.html", subject=subject, chapters=chapters, quizzes_by_chapter=quizzes_by_chapter, user_scores=user_scores,now=now)

# Attempt Quiz
@app.route("/attempt_quiz/<int:quiz_id>", methods=["GET", "POST"])
def attempt_quiz(quiz_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return redirect(url_for("user_dashboard"))

    questions = Question.query.filter_by(quiz_id=quiz_id).all()

    if request.method == "POST":
        user_id = session["user_id"]
        total_questions = len(questions)
        correct_answers = 0
        selected_answers = {}  # Object to store user answers

        for question in questions:
            user_answer = request.form.get(f"question_{question.id}")
            if user_answer:
                user_answer = int(user_answer)
                selected_answers[str(question.id)] = user_answer  # Store selected answer
                if user_answer == question.correct_option:
                    correct_answers += 1

        # Convert selected answers to JSON format
        selected_answers_str = json.dumps(selected_answers)

        # Check if the user already has a score for this quiz
        existing_score = Score.query.filter_by(user_id=user_id, quiz_id=quiz_id).first()

        if existing_score:
            # Update existing score with the latest attempt
            existing_score.total_scored = correct_answers
            existing_score.total_questions = total_questions
            existing_score.selected_answers = selected_answers_str
            existing_score.time_stamp_of_attempt = datetime.utcnow()
        else:
            # Create a new score record
            new_score = Score(
                user_id=user_id,
                quiz_id=quiz_id,
                total_scored=correct_answers,
                total_questions=total_questions,
                selected_answers=selected_answers_str
            )
            db.session.add(new_score)

        db.session.commit()

        return redirect(url_for("quiz_results", quiz_id=quiz_id))

    return render_template("attempt_quiz.html", quiz=quiz, questions=questions, chapter=quiz.chapter)

# Quiz Results
@app.route("/quiz_results/<int:quiz_id>")
def quiz_results(quiz_id):
    if "user_id" not in session or session["role"] != "user":
        return redirect(url_for("login"))

    user_id = session["user_id"]
    
    # Fetch the user's latest score for this quiz
    score_record = Score.query.filter_by(user_id=user_id, quiz_id=quiz_id).order_by(Score.time_stamp_of_attempt.desc()).first()

    if not score_record:
        return redirect(url_for("view_quizzes"))

    quiz = Quiz.query.get(quiz_id)
    selected_answers = score_record.get_selected_answers()  # Retrieve JSON-stored answers

    return render_template(
        "quiz_results.html", 
        quiz=quiz, 
        score=score_record.total_scored, 
        total_questions=score_record.total_questions,
        selected_answers=selected_answers
    )

# Quiz Summary
@app.route("/quiz_summary")
def quiz_summary():
    if "user_id" not in session or session["role"] != "user":
        return redirect(url_for("login"))

    user_id = session["user_id"]

    # Get all scores for this user
    scores = Score.query.filter_by(user_id=user_id).all()

    # Organize scores by chapter
    summary = {}
    for score in scores:
        quiz = Quiz.query.get(score.quiz_id)
        chapter = Chapter.query.get(quiz.chapter_id)

        if chapter.id not in summary:
            summary[chapter.id] = {
                "chapter_name": chapter.name,
                "total_score": 0,
                "total_questions": 0
            }

        summary[chapter.id]["total_score"] += score.total_scored
        summary[chapter.id]["total_questions"] += score.total_questions

    return render_template("quiz_summary.html", summary=summary)

# Search as User
@app.route("/user_search", methods=["GET"])
def user_search():
    if "user_id" not in session or session["role"] != "user":
        return redirect(url_for("login"))

    query = request.args.get("query", "").strip()

    if not query:
        return redirect(url_for("user_dashboard"))

    # Search for subjects based on name
    subjects = Subject.query.filter(Subject.name.ilike(f"%{query}%")).all()

    # Search for quizzes based on description
    quizzes = Quiz.query.filter(Quiz.remarks.ilike(f"%{query}%")).all()

    return render_template("user_search_results.html", subjects=subjects, quizzes=quizzes)


#=========================== ADDITIONAL ADMIN ROUTES ==============================

# Search as Admin
@app.route("/admin_search", methods=["GET"])
def admin_search():
    if not admin_required():
        return redirect(url_for("login"))

    query = request.args.get("query", "").strip()

    if not query:
        return redirect(url_for("admin_dashboard"))

    # Search users by name or email
    users = User.query.filter(User.full_name.ilike(f"%{query}%") | User.email.ilike(f"%{query}%")).all()

    # Search subjects
    subjects = Subject.query.filter(Subject.name.ilike(f"%{query}%")).all()

    # Search chapters
    chapters = Chapter.query.filter(Chapter.name.ilike(f"%{query}%")).all()

    # Search quizzes by description
    quizzes = Quiz.query.filter(Quiz.remarks.ilike(f"%{query}%")).all()

    # Search questions by question statement
    questions = Question.query.filter(Question.question_statement.ilike(f"%{query}%")).all()

    return render_template("admin_search_results.html", users=users, subjects=subjects, chapters=chapters, quizzes=quizzes, questions=questions)

# Delete User as Admin
@app.route("/admin/users/delete/<int:user_id>")
def delete_user(user_id):
    if "user_id" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    user = User.query.get(user_id)

    if not user:
        return redirect(url_for("admin_dashboard"))

    # Delete related scores 
    Score.query.filter_by(user_id=user_id).delete()

    # Delete user
    db.session.delete(user)
    db.session.commit()

    return redirect(url_for("admin_dashboard"))




# ====================== MAIN =======================
if __name__ == "__main__":   # Application only runs when app.py is directly executed
    initialize_admin()  # Ensure admin is created before running
    app.run(debug=True)
    