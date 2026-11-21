STARTERS_BY_ROLE: dict[str, list[str]] = {
    "student": [
        "What's my attendance in DBMS and how many more can I skip?",
        "Mera CGPA kitna hai aur kitni fees pending hai?",
        "When is my next exam?",
        "Explain deadlock like a 5-mark answer, then give me 5 MCQs",
        "Make flashcards on normalization",
    ],
    "faculty": [
        "Which students in my OS class are below 75% attendance?",
        "What did students say about my teaching this semester?",
        "Average internal marks in each of my classes",
        "Weekly attendance trend of my classes",
    ],
    "advisor": [
        "Which of my advisees have a backlog or attendance below 75%?",
        "Pending registrations of my advisees",
    ],
    "hod": [
        "Subject-wise pass percentage in my department this semester",
        "Most common teaching feedback themes in my department",
        "Average attendance by subject in my department",
    ],
    "dean": [
        "Compare pass percentage across all departments",
        "Department-wise pending fees",
        "Average SGPA per department in the last completed semester",
    ],
    "admin": [
        "Hostel-wise fee defaulters",
        "Which mess got the most hygiene complaints this month?",
        "Compare average SGPA of hostellers vs day scholars by department",
        "Open complaints per category",
    ],
}
MAX_STARTERS = 6
ROLE_PRIORITY = ("admin", "dean", "hod", "advisor", "faculty", "student")


def starter_questions(roles: tuple[str, ...]) -> list[str]:
    questions: list[str] = []
    for role in ROLE_PRIORITY:
        if role in roles:
            questions.extend(item for item in STARTERS_BY_ROLE[role] if item not in questions)
    if not questions:
        questions = ["Explain normalization in DBMS", "Give me a 5-question quiz on sorting"]
    return questions[:MAX_STARTERS]


DEMO_ACCOUNTS: list[dict[str, str]] = [
    {"username": "student1", "role": "Student", "note": "CSE 5th sem, hosteller, pending fees"},
    {"username": "student2", "role": "Student", "note": "ECE 3rd sem B, attendance problem"},
    {"username": "faculty1", "role": "Faculty", "note": "Teaches CSE 5th-sem DBMS"},
    {"username": "faculty2", "role": "Faculty", "note": "Member of Exam Cell – CSE"},
    {"username": "advisor1", "role": "Advisor", "note": "Advises several at-risk students"},
    {"username": "hod_cse", "role": "HOD", "note": "Head of CSE"},
    {"username": "dean", "role": "Dean", "note": "College-wide academics and fees"},
    {"username": "admin", "role": "Admin", "note": "All college data"},
]
