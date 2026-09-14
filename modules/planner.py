def create_plan(subjects, available_hrs):
    subjects = sorted(
        subjects, 
        key = lambda x : x["priority"],
        reverse = True
    )

    total_priority = sum(subject["priority"] for subject in subjects)

    plan = []

    for subject in subjects:
        if total_priority == 0:
            continue

        study_hrs = (subject["priority"] / total_priority) * available_hrs
        study_hrs = round(study_hrs, 1)

        if study_hrs > 0:
            plan.append({
                "subject": subject["name"],
                "hours": study_hrs,
                "priority": subject["priority"]
            })

    return plan