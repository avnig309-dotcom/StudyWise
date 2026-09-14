from datetime import date

def calculate_priority(exam_date, difficulty, confidence):
    today = date.today()
    days_left = (exam_date - today).days

    if days_left <= 2:
        urgency = 40
    elif days_left <= 5:
        urgency = 30
    elif days_left <= 10:
        urgency = 20
    else:
        urgency = 10

    difficulty_score = {
        "Easy" : 5,
        "Medium" : 10,
        "Hard" : 20
    }

    confidence_score = {
        "High" : 5,
        "Medium" : 15,
        "Low" : 25
    }

    score = (
        urgency 
        + difficulty_score[difficulty]
        + confidence_score[confidence]
    )

    return min(score, 100)