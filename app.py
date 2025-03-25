from flask import Flask, render_template, request, redirect, url_for, session, flash
from models.models import db, User, Subject, Chapter, Quiz, Question, Score
import os
from datetime import datetime

app = Flask(__name__)

# Database Path Setup
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "instance/quiz_master.db")

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'secret'

db.init_app(app)  # <-- Now db is properly initialized

# Function to check admin authentication
def admin_required():
    return "user_id" in session and session["role"] == "admin"

# ====================== ADMIN USER INITIALIZATION ======================

def initialize_admin():
    with app.app_context():
        db.create_all()  # Ensure tables exist
        
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


# ====================== AUTH ROUTES ======================

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
            flash("Email already registered", "danger")
            return redirect(url_for("register"))

        new_user = User(email=email, password=password, full_name=full_name,
                        qualification=qualification, dob=dob, role="user")
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
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

        flash("Invalid credentials", "danger")

    return render_template("login.html")

# ====================== DASHBOARD ROUTES ======================

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

# ====================== ADMIN FUNCTIONALITIES ======================

# ✅ Manage Subjects (Create, Read, Delete)
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
        flash("Subject added successfully!", "success")

    subjects = Subject.query.all()
    return render_template("manage_subjects.html", subjects=subjects)

@app.route("/admin/subjects/delete/<int:subject_id>")
def delete_subject(subject_id):
    if not admin_required():
        return redirect(url_for("login"))

    subject = Subject.query.get(subject_id)
    db.session.delete(subject)
    db.session.commit()
    flash("Subject deleted!", "danger")
    return redirect(url_for("manage_subjects"))

# ✅ Manage Chapters (Create, Read, Delete)
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
        flash("Chapter added successfully!", "success")

    chapters = Chapter.query.filter_by(subject_id=subject_id).all()
    return render_template("manage_chapters.html", subject=subject, chapters=chapters)

@app.route("/admin/chapters/delete/<int:chapter_id>")
def delete_chapter(chapter_id):
    if not admin_required():
        return redirect(url_for("login"))

    chapter = Chapter.query.get(chapter_id)
    db.session.delete(chapter)
    db.session.commit()
    flash("Chapter deleted!", "danger")
    return redirect(url_for("manage_subjects"))


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
            flash("Invalid date format. Please use YYYY-MM-DD.", "danger")
            return redirect(url_for("manage_quizzes", chapter_id=chapter_id))

        new_quiz = Quiz(chapter_id=chapter_id, date_of_quiz=date_of_quiz, remarks=remarks)
        db.session.add(new_quiz)
        db.session.commit()
        flash("Quiz added successfully!", "success")

    quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()
    return render_template("manage_quizzes.html", chapter=chapter, quizzes=quizzes)


@app.route("/admin/quizzes/delete/<int:quiz_id>")
def delete_quiz(quiz_id):
    if not admin_required():
        return redirect(url_for("login"))

    quiz = Quiz.query.get(quiz_id)
    db.session.delete(quiz)
    db.session.commit()
    flash("Quiz deleted!", "danger")
    return redirect(url_for("manage_subjects"))

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
        flash("Question added successfully!", "success")

    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    return render_template("manage_questions.html", quiz=quiz, questions=questions)

@app.route("/admin/questions/delete/<int:question_id>")
def delete_question(question_id):
    if not admin_required():
        return redirect(url_for("login"))

    question = Question.query.get(question_id)
    db.session.delete(question)
    db.session.commit()
    flash("Question deleted!", "danger")
    return redirect(url_for("manage_questions", quiz_id=question.quiz_id))

# ====================== EDIT FUNCTIONALITIES ======================

@app.route("/admin/subjects/edit/<int:subject_id>", methods=["GET", "POST"])
def edit_subject(subject_id):
    if not admin_required():
        return redirect(url_for("login"))

    subject = Subject.query.get(subject_id)
    if not subject:
        flash("Subject not found!", "danger")
        return redirect(url_for("manage_subjects"))

    if request.method == "POST":
        subject.name = request.form["name"]
        subject.description = request.form["description"]
        db.session.commit()
        flash("Subject updated successfully!", "success")
        return redirect(url_for("manage_subjects"))

    return render_template("edit_subject.html", subject=subject)



# Edit Chapter
@app.route("/admin/chapters/edit/<int:chapter_id>", methods=["GET", "POST"])
def edit_chapter(chapter_id):
    if not admin_required():
        return redirect(url_for("login"))

    chapter = Chapter.query.get(chapter_id)
    if not chapter:
        flash("Chapter not found!", "danger")
        return redirect(url_for("manage_subjects"))

    if request.method == "POST":
        chapter.name = request.form["name"]
        chapter.description = request.form["description"]
        db.session.commit()
        flash("Chapter updated successfully!", "success")
        return redirect(url_for("manage_chapters", subject_id=chapter.subject_id))

    return render_template("edit_chapter.html", chapter=chapter)


# Edit Quiz
@app.route("/admin/quizzes/edit/<int:quiz_id>", methods=["GET", "POST"])
def edit_quiz(quiz_id):
    if not admin_required():
        return redirect(url_for("login"))

    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        flash("Quiz not found!", "danger")
        return redirect(url_for("manage_subjects"))

    if request.method == "POST":
        from datetime import datetime

        quiz.date_of_quiz = datetime.strptime(request.form["date_of_quiz"], "%Y-%m-%d")
        quiz.remarks = request.form["remarks"]
        db.session.commit()
        flash("Quiz updated successfully!", "success")
        return redirect(url_for("manage_quizzes", chapter_id=quiz.chapter_id))

    return render_template("edit_quiz.html", quiz=quiz)

@app.route("/admin/questions/edit/<int:question_id>", methods=["GET", "POST"])
def edit_question(question_id):
    if not admin_required():
        return redirect(url_for("login"))

    question = Question.query.get(question_id)
    if not question:
        flash("Question not found!", "danger")
        return redirect(url_for("manage_questions", quiz_id=question.quiz_id))

    if request.method == "POST":
        question.question_statement = request.form["question_statement"]
        question.option1 = request.form["option1"]
        question.option2 = request.form["option2"]
        question.option3 = request.form["option3"]
        question.option4 = request.form["option4"]
        question.correct_option = int(request.form["correct_option"])
        db.session.commit()
        flash("Question updated successfully!", "success")
        return redirect(url_for("manage_questions", quiz_id=question.quiz_id))

    return render_template("edit_question.html", question=question)



# ✅ View Users (Display all users with details)
@app.route("/admin/users")
def view_users():
    if not admin_required():
        return redirect(url_for("login"))

    users = User.query.all()
    return render_template("view_users.html", users=users)

# Logout Route
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/view_quizzes/<int:subject_id>")
def view_quizzes(subject_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    subject = Subject.query.get(subject_id)

    if not subject:
        return "Subject not found", 404

    chapters = Chapter.query.filter_by(subject_id=subject_id).all()

    quizzes_by_chapter = {}
    user_scores = {}  # Dictionary to store user scores for each quiz

    for chapter in chapters:
        quizzes = Quiz.query.filter_by(chapter_id=chapter.id).all()
        quizzes_by_chapter[chapter.id] = quizzes

        # Fetch scores for each quiz for the current user
        for quiz in quizzes:
            score_record = Score.query.filter_by(user_id=user_id, quiz_id=quiz.id).order_by(Score.time_stamp_of_attempt.desc()).first()
            user_scores[quiz.id] = score_record.total_scored if score_record else None

    return render_template("view_quizzes.html", subject=subject, chapters=chapters, quizzes_by_chapter=quizzes_by_chapter, user_scores=user_scores)

@app.route("/attempt_quiz/<int:quiz_id>", methods=["GET", "POST"])
def attempt_quiz(quiz_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        flash("Quiz not found", "danger")
        return redirect(url_for("user_dashboard"))

    questions = Question.query.filter_by(quiz_id=quiz_id).all()

    if request.method == "POST":
        user_id = session["user_id"]
        total_questions = len(questions)
        correct_answers = 0
        selected_answers = {}  # Dictionary to store user answers

        for question in questions:
            user_answer = request.form.get(f"question_{question.id}")
            if user_answer:
                user_answer = int(user_answer)
                selected_answers[str(question.id)] = user_answer  # Store selected answer
                if user_answer == question.correct_option:
                    correct_answers += 1

        # Convert selected answers to JSON format
        import json
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

@app.route("/submit_quiz/<int:quiz_id>", methods=["POST"])
def submit_quiz(quiz_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    quiz = Quiz.query.get(quiz_id)

    if not quiz:
        flash("Quiz not found", "danger")
        return redirect(url_for("user_dashboard"))

    total_questions = len(quiz.questions)
    correct_answers = 0
    selected_answers = {}  # Dictionary to store user-selected answers

    for question in quiz.questions:
        user_answer = request.form.get(f"question_{question.id}")

        if user_answer:
            user_answer = int(user_answer)
            selected_answers[str(question.id)] = user_answer  # Store answer
            if user_answer == question.correct_option:
                correct_answers += 1

    # Convert selected answers dictionary to string (JSON format)
    import json
    selected_answers_str = json.dumps(selected_answers)

    # Check if the user already has a score for this quiz
    existing_score = Score.query.filter_by(user_id=user_id, quiz_id=quiz_id).first()

    if existing_score:
        # Update the existing score with the latest attempt
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



@app.route("/quiz_results/<int:quiz_id>")
def quiz_results(quiz_id):
    if "user_id" not in session or session["role"] != "user":
        return redirect(url_for("login"))

    user_id = session["user_id"]
    
    # Fetch the user's latest score for this quiz
    score_record = Score.query.filter_by(user_id=user_id, quiz_id=quiz_id).order_by(Score.time_stamp_of_attempt.desc()).first()

    if not score_record:
        flash("You have not attempted this quiz!", "danger")
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


# ====================== MAIN =======================
if __name__ == "__main__":
    initialize_admin()  # Ensure admin is created before running
    app.run(debug=True)

