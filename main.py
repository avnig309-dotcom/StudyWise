from flask import Flask, request, jsonify, send_from_directory, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import sqlite3
import os
import sys

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

from modules.priority import calculate_priority
from modules.planner import create_plan
from modules.recommendations import get_recommendation


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "studywise-secret-key")

DATABASE = os.path.join(ROOT_DIR, "studywise.db")


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            daily_hours REAL DEFAULT 3,
            start_time TEXT DEFAULT '09:00',
            session_length INTEGER DEFAULT 60,
            break_length INTEGER DEFAULT 15,
            streak INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            exam_date TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            confidence TEXT NOT NULL,
            priority REAL DEFAULT 50,
            completed INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject_id INTEGER,
            task_name TEXT NOT NULL,
            task_time TEXT,
            completed INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(subject_id) REFERENCES subjects(id)
        )
    """)

    conn.commit()
    conn.close()


init_db()

def current_user():
    user_id = session.get("user_id")

    if not user_id:
        return None

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()
    conn.close()

    return user


def get_user_subjects(user_id):
    conn = get_db()

    subjects = conn.execute("""
        SELECT *
        FROM subjects
        WHERE user_id = ?
        ORDER BY priority DESC
    """, (user_id,)).fetchall()

    conn.close()

    return [dict(subject) for subject in subjects]


def calculate_subject_priority(exam_date, difficulty, confidence):
    try:
        return calculate_priority(
            exam_date,
            difficulty,
            confidence
        )
    except Exception:
        return 50

@app.route("/")
def index():
    return send_from_directory(ROOT_DIR, "index.html")


@app.route("/api/signup", methods=["POST"])
def signup():

    data = request.get_json() or {}

    username = data.get("username", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not username or not email or not password:
        return jsonify({
            "success": False,
            "message": "Please fill in all fields."
        }), 400

    if len(password) < 6:
        return jsonify({
            "success": False,
            "message": "Password must be at least 6 characters."
        }), 400

    conn = get_db()

    existing = conn.execute(
        "SELECT id FROM users WHERE email = ?",
        (email,)
    ).fetchone()

    if existing:
        conn.close()
        return jsonify({
            "success": False,
            "message": "An account with this email already exists."
        }), 400

    password_hash = generate_password_hash(password)

    cursor = conn.execute("""
        INSERT INTO users (username, email, password)
        VALUES (?, ?, ?)
    """, (username, email, password_hash))

    user_id = cursor.lastrowid

    conn.commit()
    conn.close()

    session["user_id"] = user_id

    return jsonify({
        "success": True,
        "message": "Account created successfully.",
        "user": {
            "username": username,
            "email": email
        }
    })


@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json() or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE email = ?",
        (email,)
    ).fetchone()

    conn.close()

    if not user or not check_password_hash(
        user["password"],
        password
    ):
        return jsonify({
            "success": False,
            "message": "Incorrect email or password."
        }), 401

    session["user_id"] = user["id"]

    return jsonify({
        "success": True,
        "message": "Welcome back!",
        "user": {
            "username": user["username"],
            "email": user["email"]
        }
    })


@app.route("/api/logout", methods=["POST"])
def logout():

    session.clear()

    return jsonify({
        "success": True
    })


@app.route("/api/me")
def me():

    user = current_user()

    if not user:
        return jsonify({
            "logged_in": False
        })

    return jsonify({
        "logged_in": True,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "daily_hours": user["daily_hours"],
            "start_time": user["start_time"],
            "session_length": user["session_length"],
            "break_length": user["break_length"],
            "streak": user["streak"]
        }
    })


@app.route("/api/subjects", methods=["GET"])
def get_subjects():

    user = current_user()

    if not user:
        return jsonify({
            "success": False,
            "message": "Please sign in."
        }), 401

    subjects = get_user_subjects(user["id"])

    return jsonify({
        "success": True,
        "subjects": subjects
    })


@app.route("/api/subjects", methods=["POST"])
def add_subject():

    user = current_user()

    if not user:
        return jsonify({
            "success": False,
            "message": "Please sign in."
        }), 401

    data = request.get_json() or {}

    name = data.get("name", "").strip()
    exam_date = data.get("exam_date", "")
    difficulty = data.get("difficulty", "Medium")
    confidence = data.get("confidence", "Medium")

    if not name or not exam_date:
        return jsonify({
            "success": False,
            "message": "Subject name and exam date are required."
        }), 400

    priority = calculate_subject_priority(
        exam_date,
        difficulty,
        confidence
    )

    conn = get_db()

    cursor = conn.execute("""
        INSERT INTO subjects
        (user_id, name, exam_date, difficulty, confidence, priority)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user["id"],
        name,
        exam_date,
        difficulty,
        confidence,
        priority
    ))

    subject_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "subject_id": subject_id
    })


@app.route("/api/subjects/<int:subject_id>", methods=["PUT"])
def edit_subject(subject_id):

    user = current_user()

    if not user:
        return jsonify({
            "success": False,
            "message": "Please sign in."
        }), 401

    data = request.get_json() or {}

    name = data.get("name", "").strip()
    exam_date = data.get("exam_date", "")
    difficulty = data.get("difficulty", "Medium")
    confidence = data.get("confidence", "Medium")

    if not name or not exam_date:
        return jsonify({
            "success": False,
            "message": "Please fill in all fields."
        }), 400

    priority = calculate_subject_priority(
        exam_date,
        difficulty,
        confidence
    )

    conn = get_db()

    result = conn.execute("""
        UPDATE subjects
        SET name = ?,
            exam_date = ?,
            difficulty = ?,
            confidence = ?,
            priority = ?
        WHERE id = ?
        AND user_id = ?
    """, (
        name,
        exam_date,
        difficulty,
        confidence,
        priority,
        subject_id,
        user["id"]
    ))

    conn.commit()
    conn.close()

    if result.rowcount == 0:
        return jsonify({
            "success": False,
            "message": "Subject not found."
        }), 404

    return jsonify({
        "success": True
    })


@app.route("/api/subjects/<int:subject_id>", methods=["DELETE"])
def delete_subject(subject_id):

    user = current_user()

    if not user:
        return jsonify({
            "success": False,
            "message": "Please sign in."
        }), 401

    conn = get_db()

    conn.execute("""
        DELETE FROM subjects
        WHERE id = ?
        AND user_id = ?
    """, (subject_id, user["id"]))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True
    })


@app.route("/api/subjects/<int:subject_id>/complete", methods=["POST"])
def complete_subject(subject_id):

    user = current_user()

    if not user:
        return jsonify({
            "success": False,
            "message": "Please sign in."
        }), 401

    data = request.get_json() or {}
    completed = 1 if data.get("completed") else 0

    conn = get_db()

    conn.execute("""
        UPDATE subjects
        SET completed = ?
        WHERE id = ?
        AND user_id = ?
    """, (
        completed,
        subject_id,
        user["id"]
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True
    })


@app.route("/api/settings", methods=["PUT"])
def update_settings():

    user = current_user()

    if not user:
        return jsonify({
            "success": False,
            "message": "Please sign in."
        }), 401

    data = request.get_json() or {}

    try:
        daily_hours = float(data.get("daily_hours", 3))
    except:
        daily_hours = 3

    start_time = data.get("start_time", "09:00")

    try:
        session_length = int(data.get("session_length", 60))
    except:
        session_length = 60

    try:
        break_length = int(data.get("break_length", 15))
    except:
        break_length = 15

    conn = get_db()

    conn.execute("""
        UPDATE users
        SET daily_hours = ?,
            start_time = ?,
            session_length = ?,
            break_length = ?
        WHERE id = ?
    """, (
        daily_hours,
        start_time,
        session_length,
        break_length,
        user["id"]
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True
    })


@app.route("/api/dashboard")
def dashboard():

    user = current_user()

    if not user:
        return jsonify({
            "success": False,
            "message": "Please sign in."
        }), 401

    subjects = get_user_subjects(user["id"])

    try:
        plan = create_plan(
            subjects,
            float(user["daily_hours"])
        )
    except Exception:
        plan = []

    try:
        recommendation = get_recommendation(subjects)
    except Exception:
        recommendation = "Focus on your highest-priority subject first."

    completed = sum(
        1 for subject in subjects
        if subject.get("completed")
    )

    total = len(subjects)

    progress = 0

    if total:
        progress = round(
            (completed / total) * 100
        )

    return jsonify({
        "success": True,
        "subjects": subjects,
        "plan": plan,
        "recommendation": recommendation,
        "progress": progress,
        "completed": completed,
        "total": total,
        "user": {
            "username": user["username"],
            "email": user["email"],
            "daily_hours": user["daily_hours"],
            "start_time": user["start_time"],
            "session_length": user["session_length"],
            "break_length": user["break_length"],
            "streak": user["streak"]
        }
    })


# run

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
