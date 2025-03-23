from flask import Flask, render_template, request, redirect, url_for, session, flash
from models.models import db, User, Subject, Chapter, Quiz, Question
import os
from datetime import datetime


app = Flask(__name__)

# Database Path Setup
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "instance/quiz_master.db")

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'secret'

db.init_app(app)

# Function to check admin authentication
def admin_required():
    return "user_id" in session and session["role"] == "admin"

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

# ====================== MAIN ======================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
