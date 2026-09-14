from flask import Flask, request, redirect, session, send_from_directory
from datetime import datetime, date
import os
import sys

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

from modules.priority import calculate_priority
from modules.planner import create_plan
from modules.recommendations import get_recommendation


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "studywise-secret-key")


@app.route("/", methods=["GET", "POST"])
def home():

    if "subjects" not in session:
        session["subjects"] = []

    if request.method == "POST":

        subject_name = request.form.get("subject_name", "").strip()
        exam_date = request.form.get("exam_date", "")
        difficulty = request.form.get("difficulty", "Medium")
        confidence = request.form.get("confidence", "Medium")
        available_hours = request.form.get("available_hours", "3")

        if subject_name and exam_date:

            try:
                priority = calculate_priority(
                    exam_date,
                    difficulty,
                    confidence
                )
            except Exception:
                priority = 50

            subjects = session["subjects"]

            subjects.append({
                "name": subject_name,
                "exam_date": exam_date,
                "difficulty": difficulty,
                "confidence": confidence,
                "priority": priority
            })

            session["subjects"] = subjects
            session.modified = True

        return redirect("/")

    subjects = session.get("subjects", [])

    subjects = sorted(
        subjects,
        key=lambda x: x.get("priority", 0),
        reverse=True
    )

    try:
        available_hours = float(
            request.args.get("hours", 3)
        )
    except ValueError:
        available_hours = 3

    try:
        plan = create_plan(subjects, available_hours)
    except Exception:
        plan = []

    try:
        recommendation = get_recommendation(subjects)
    except Exception:
        recommendation = "Focus on your highest-priority subject first."

    return send_from_directory(
        ROOT_DIR,
        "index.html"
    )


@app.route("/add", methods=["POST"])
def add_subject():

    if "subjects" not in session:
        session["subjects"] = []

    subject_name = request.form.get("subject_name", "").strip()
    exam_date = request.form.get("exam_date", "")
    difficulty = request.form.get("difficulty", "Medium")
    confidence = request.form.get("confidence", "Medium")

    try:
        available_hours = float(
            request.form.get("available_hours", 3)
        )
    except ValueError:
        available_hours = 3

    if subject_name and exam_date:

        try:
            priority = calculate_priority(
                exam_date,
                difficulty,
                confidence
            )
        except Exception:
            priority = 50

        subjects = session["subjects"]

        subjects.append({
            "name": subject_name,
            "exam_date": exam_date,
            "difficulty": difficulty,
            "confidence": confidence,
            "priority": priority
        })

        session["subjects"] = subjects
        session.modified = True

    return redirect(f"/?hours={available_hours}")


@app.route("/clear", methods=["POST"])
def clear():

    session["subjects"] = []
    session.modified = True

    return redirect("/")


@app.route("/data")
def data():

    subjects = session.get("subjects", [])

    subjects = sorted(
        subjects,
        key=lambda x: x.get("priority", 0),
        reverse=True
    )

    try:
        available_hours = float(
            request.args.get("hours", 3)
        )
    except ValueError:
        available_hours = 3

    try:
        plan = create_plan(subjects, available_hours)
    except Exception:
        plan = []

    try:
        recommendation = get_recommendation(subjects)
    except Exception:
        recommendation = "Focus on your highest-priority subject first."

    return {
        "subjects": subjects,
        "plan": plan,
        "recommendation": recommendation,
        "available_hours": available_hours
    }


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )