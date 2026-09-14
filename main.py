import os
from datetime import datetime, date

from flask import Flask, request, jsonify, send_from_directory, session
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from supabase import create_client, Client

from modules.priority import calculate_priority
from modules.planner import create_plan
from modules.recommendations import get_recommendation

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.environ.get("SUPABASE_SECRET_KEY")

if not SUPABASE_URL or not SUPABASE_SECRET_KEY:
    raise RuntimeError(
        "SUPABASE_URL and SUPABASE_SECRET_KEY must be set."
    )

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SECRET_KEY
)

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "studywise-development-secret"
)

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

def current_user_id():
    return session.get("user_id")


def require_login():
    user_id = current_user_id()

    if not user_id:
        return None, jsonify({
            "success": False,
            "message": "Please log in first."
        }), 401

    return user_id, None, None


def get_user_subjects(user_id):
    response = (
        supabase
        .table("subjects")
        .select("*")
        .eq("user_id", user_id)
        .order("priority", desc=True)
        .execute()
    )

    return response.data or []


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
def home():
    return send_from_directory(
        os.path.dirname(os.path.abspath(__file__)),
        "index.html"
    )

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

    existing = (
        supabase
        .table("users")
        .select("id")
        .eq("email", email)
        .execute()
    )

    if existing.data:
        return jsonify({
            "success": False,
            "message": "An account with this email already exists."
        }), 409

    password_hash = generate_password_hash(password)

    result = (
        supabase
        .table("users")
        .insert({
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "daily_hours": 3,
            "start_time": "18:00",
            "session_length": 50,
            "break_length": 10,
            "streak": 0
        })
        .execute()
    )

    if not result.data:
        return jsonify({
            "success": False,
            "message": "Could not create account."
        }), 500

    user = result.data[0]

    session["user_id"] = user["id"]
    session["username"] = user["username"]

    return jsonify({
        "success": True,
        "message": "Account created successfully.",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"]
        }
    })


@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json() or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Please enter your email and password."
        }), 400

    result = (
        supabase
        .table("users")
        .select("*")
        .eq("email", email)
        .limit(1)
        .execute()
    )

    if not result.data:
        return jsonify({
            "success": False,
            "message": "Invalid email or password."
        }), 401

    user = result.data[0]

    if not check_password_hash(
        user["password_hash"],
        password
    ):
        return jsonify({
            "success": False,
            "message": "Invalid email or password."
        }), 401

    session["user_id"] = user["id"]
    session["username"] = user["username"]

    return jsonify({
        "success": True,
        "message": "Logged in successfully.",
        "user": {
            "id": user["id"],
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

    user_id = current_user_id()

    if not user_id:
        return jsonify({
            "logged_in": False
        })

    result = (
        supabase
        .table("users")
        .select(
            "id, username, email, daily_hours, "
            "start_time, session_length, break_length, streak"
        )
        .eq("id", user_id)
        .limit(1)
        .execute()
    )

    if not result.data:
        session.clear()

        return jsonify({
            "logged_in": False
        })

    user = result.data[0]

    return jsonify({
        "logged_in": True,
        "user": user
    })

@app.route("/api/subjects", methods=["GET"])
def get_subjects():

    user_id, error, status = require_login()

    if error:
        return error, status

    subjects = get_user_subjects(user_id)

    return jsonify({
        "success": True,
        "subjects": subjects
    })


@app.route("/api/subjects", methods=["POST"])
def add_subject():

    user_id, error, status = require_login()

    if error:
        return error, status

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

    result = (
        supabase
        .table("subjects")
        .insert({
            "user_id": user_id,
            "name": name,
            "exam_date": exam_date,
            "difficulty": difficulty,
            "confidence": confidence,
            "priority": priority,
            "completed": False
        })
        .execute()
    )

    if not result.data:
        return jsonify({
            "success": False,
            "message": "Could not add subject."
        }), 500

    return jsonify({
        "success": True,
        "subject": result.data[0]
    })


@app.route("/api/subjects/<int:subject_id>", methods=["PUT"])
def update_subject(subject_id):

    user_id, error, status = require_login()

    if error:
        return error, status

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

    result = (
        supabase
        .table("subjects")
        .update({
            "name": name,
            "exam_date": exam_date,
            "difficulty": difficulty,
            "confidence": confidence,
            "priority": priority
        })
        .eq("id", subject_id)
        .eq("user_id", user_id)
        .execute()
    )

    if not result.data:
        return jsonify({
            "success": False,
            "message": "Subject not found."
        }), 404

    return jsonify({
        "success": True,
        "subject": result.data[0]
    })


@app.route("/api/subjects/<int:subject_id>", methods=["DELETE"])
def delete_subject(subject_id):

    user_id, error, status = require_login()

    if error:
        return error, status

    result = (
        supabase
        .table("subjects")
        .delete()
        .eq("id", subject_id)
        .eq("user_id", user_id)
        .execute()
    )

    return jsonify({
        "success": True
    })


@app.route("/api/subjects/<int:subject_id>/complete", methods=["POST"])
def complete_subject(subject_id):

    user_id, error, status = require_login()

    if error:
        return error, status

    subject_result = (
        supabase
        .table("subjects")
        .select("completed")
        .eq("id", subject_id)
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if not subject_result.data:
        return jsonify({
            "success": False,
            "message": "Subject not found."
        }), 404

    current_status = subject_result.data[0]["completed"]

    result = (
        supabase
        .table("subjects")
        .update({
            "completed": not current_status
        })
        .eq("id", subject_id)
        .eq("user_id", user_id)
        .execute()
    )

    return jsonify({
        "success": True,
        "completed": not current_status
    })

@app.route("/api/settings", methods=["PUT"])
def update_settings():

    user_id, error, status = require_login()

    if error:
        return error, status

    data = request.get_json() or {}

    try:
        daily_hours = float(data.get("daily_hours", 3))
        session_length = int(data.get("session_length", 50))
        break_length = int(data.get("break_length", 10))
    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "message": "Invalid settings."
        }), 400

    start_time = data.get("start_time", "18:00")

    if daily_hours <= 0:
        daily_hours = 3

    result = (
        supabase
        .table("users")
        .update({
            "daily_hours": daily_hours,
            "start_time": start_time,
            "session_length": session_length,
            "break_length": break_length
        })
        .eq("id", user_id)
        .execute()
    )

    return jsonify({
        "success": True,
        "settings": result.data[0] if result.data else {}
    })

@app.route("/api/dashboard")
def dashboard():

    user_id, error, status = require_login()

    if error:
        return error, status

    user_result = (
        supabase
        .table("users")
        .select("*")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )

    if not user_result.data:
        return jsonify({
            "success": False,
            "message": "User not found."
        }), 404

    user = user_result.data[0]

    subjects = get_user_subjects(user_id)

    try:
        daily_hours = float(user.get("daily_hours") or 3)
    except (ValueError, TypeError):
        daily_hours = 3

    try:
        plan = create_plan(
            subjects,
            daily_hours
        )
    except Exception:
        plan = []

    try:
        recommendation = get_recommendation(
            subjects
        )
    except Exception:
        recommendation = (
            "Focus on your highest-priority subject first."
        )

    completed_count = sum(
        1 for subject in subjects
        if subject.get("completed")
    )

    total_count = len(subjects)

    if total_count:
        progress = round(
            (completed_count / total_count) * 100
        )
    else:
        progress = 0

    return jsonify({
        "success": True,
        "user": user,
        "subjects": subjects,
        "plan": plan,
        "recommendation": recommendation,
        "progress": progress,
        "completed_count": completed_count,
        "total_count": total_count
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
