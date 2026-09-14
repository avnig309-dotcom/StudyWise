# StudyWise

Have you ever looked at your syllabus, realized you have five things to study and absolutely no idea where to start, and then somehow ended up doing none of them?

I built StudyWise to make that problem a little easier.

Instead of giving you another boring to-do list, StudyWise looks at your exam dates, how difficult each subject feels, and how confident you are in it, then figures out where to start.

---

## What is StudyWise?

StudyWise is an adaptive study planner that takes takes all your subjects, deadlines, and free time and puts them together into a study plan that you can follow.
You tell it:

* What you're studying
* When your exams are
* How confident you feel about each subject
* How difficult each subject is
* How much time you actually have

StudyWise then turns all of that into a personalized study plan.


## The idea behind it

The system gives every subject a priority score based on what's most important when you're studying:

```text
Priority =
Exam Urgency
+ Difficulty
+ Weakness
+ Topic Importance
```

So if you have:

**DSA** → exam in 3 days + hard + low confidence

and

**Python** → exam in 10 days + easy + high confidence

StudyWise knows that DSA probably shouldn't be sitting quietly at the bottom of your to-do list. 😭

The scoring system is intentionally simple and explainable — no mysterious black-box decisions. You can see *why* something was given a higher priority.

---

## What it can do

### Tells you what to focus on

Instead of treating every subject equally, StudyWise ranks them based on urgency, difficulty, and how comfortable you are with them.

### Turn free time into an actual plan

Tell StudyWise you have 3 hours today, and it'll divide that time between your highest-priority subjects.

### 📈 Keep track of your progress

See how much you've completed, what you've been neglecting, and how your study time is changing over the week.

### Adjust according to your behaviour

Over time, the goal is for StudyWise to notice patterns and give suggestions like:

> *"You seem to get more difficult subjects done in the evening."*

or:

> *"You've been putting off Maths for three days. Maybe it's time to give it some attention."*

---

## Built With

| Part            | Technology                |
| --------------- | ------------------------- |
| Interface       | Streamlit                 |
| Main Logic      | Python                    |
| Data            | SQLite + Pandas           |
| Visualizations  | Plotly                    |
| Recommendations | Custom priority algorithm |
| Future ML       | Scikit-learn              |


This is also a project where I get to bring together things I'm learning — Python, data handling, algorithms, UI development, and turn them into something I'd actually want to use myself.
