from flask import Flask, render_template, request, redirect, url_for, session
from models.models import db, User
import os

app = Flask(__name__)

# Database Path Setup
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "instance/quiz_master.db")

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'secret'

db.init_app(app)

# User Registration Route
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        full_name = request.form["full_name"]
        qualification = request.form["qualification"]
        dob = request.form["dob"]

        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return "Email already registered"

        # Create New User
        new_user = User(email=email, password=password, full_name=full_name,
                        qualification=qualification, dob=dob, role="user")
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))  # Redirect to Login Page

    return render_template("register.html")

# Login Route (Using Email)
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and user.password == password:  # Checking if user exists and password matches
            session["user_id"] = user.id
            session["role"] = user.role

            if user.role == "admin":
                return redirect(url_for("admin_dashboard"))
            else:
                return redirect(url_for("user_dashboard"))

    return render_template("login.html")

# Admin Dashboard Route
@app.route("/admin_dashboard")
def admin_dashboard():
    if "user_id" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])  # Fetch logged-in admin
    return render_template("admin_dashboard.html", user=user)

# User Dashboard Route
@app.route("/user_dashboard")
def user_dashboard():
    if "user_id" not in session or session["role"] != "user":
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])  # Fetch logged-in user
    return render_template("user_dashboard.html", user=user)

# Logout Route
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
