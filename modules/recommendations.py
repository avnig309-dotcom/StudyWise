def get_recommendation(subjects):
    if not subjects:
        return "Add some subjects to get personalized recommendations."

    highest = max(subjects, key = lambda x: x["priority"])

    if highest["priority"] >= 70:
        return (
            f"Focus on {highest['name']} first. "
            "It has a high priority."
        )

    elif highest["priority"] >= 45:
        return (
            f"Give extra attention to {highest['name']} "
            "while maintaining other subjects."
        )

    else:
        return (
            "Your subjects are currently balanced. "
            "Try maintaining a consistent study schedule."
        )