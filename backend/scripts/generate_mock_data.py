"""Deterministic mock data for the campus and campus_auth schemas, with planted demo patterns."""

import json
import logging
import random
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from statistics import mean
from typing import Any

import mysql.connector
from faker import Faker

from app.access.loader import load_policy, read_policy
from app.access.service import hash_password
from app.config import BACKEND_ROOT, CURRENT_ACADEMIC_YEAR, Settings, get_settings

logger = logging.getLogger("generate_mock_data")

SEED = 42
LABEL_SEED = 7
BATCH_SIZE = 5000
LABELS_PATH = BACKEND_ROOT / "evals" / "datasets" / "tagging_labels.json"

DEPARTMENTS = (
    (1, "CSE", "Computer Science and Engineering", "CS"),
    (2, "ECE", "Electronics and Communication Engineering", "EC"),
    (3, "ME", "Mechanical Engineering", "ME"),
    (4, "CE", "Civil Engineering", "CE"),
)
CSE, ECE, ME = 1, 2, 3
ADMISSION_YEARS = (2023, 2024, 2025, 2026)
CURRENT_SEMESTER_BY_YEAR = {2023: 7, 2024: 5, 2025: 3, 2026: 1}
CURRENT_SEMESTERS = (1, 3, 5, 7)
SECTIONS = ("A", "B")
STUDENTS_PER_SECTION = 25
STUDENTS_PER_BATCH = STUDENTS_PER_SECTION * len(SECTIONS)
FEMALE_SHARE = 0.25
HOSTELLER_SHARE = 0.6

FACULTY_PER_DEPT = 15
FACULTY_FEMALE_SHARE = 0.3
HOD_INDEX = 0
ADVISOR_INDEXES = (0, 1, 2, 3)
FACULTY1_INDEX = 5
FACULTY2_INDEX = 7
ADVISOR1_INDEX = 1
DESIGNATIONS = ("Professor",) * 3 + ("Associate Professor",) * 4 + ("Assistant Professor",) * 8
DOCTOR_SHARE_ASSISTANT = 0.5
TEACHING_LOADS = (3,) * 10 + (2,) * 5
PLANNED_CLASSES_RANGE = (56, 60)
CORE_CREDIT_SUBJECTS = 3
CORE_CREDITS, ELECTIVE_CREDITS = 4, 3

SUBJECT_NAMES: dict[str, tuple[tuple[str, ...], ...]] = {
    "CSE": (
        (
            "Programming for Problem Solving",
            "Engineering Mathematics I",
            "Engineering Physics",
            "Basic Electrical Engineering",
            "Engineering Graphics",
        ),
        (
            "Data Structures",
            "Engineering Mathematics II",
            "Digital Logic Design",
            "Object Oriented Programming",
            "Environmental Science",
        ),
        (
            "Discrete Mathematics",
            "Computer Organization and Architecture",
            "Design and Analysis of Algorithms",
            "Probability and Statistics",
            "Python Programming",
        ),
        (
            "Microprocessors and Interfacing",
            "Web Technologies",
            "Advanced Java Programming",
            "Numerical Methods",
            "Software Design Patterns",
        ),
        (
            "Database Management Systems",
            "Operating Systems",
            "Computer Networks",
            "Theory of Computation",
            "Software Engineering",
        ),
        (
            "Compiler Design",
            "Machine Learning",
            "Computer Graphics",
            "Information Security",
            "Distributed Systems",
        ),
        (
            "Artificial Intelligence",
            "Cloud Computing",
            "Big Data Analytics",
            "Cryptography and Network Security",
            "Internet of Things",
        ),
        (
            "Deep Learning",
            "Natural Language Processing",
            "Blockchain Technology",
            "Project Management",
            "Human Computer Interaction",
        ),
    ),
    "ECE": (
        (
            "Engineering Mathematics I",
            "Engineering Physics",
            "Basic Electronics",
            "Programming in C",
            "Engineering Graphics",
        ),
        (
            "Engineering Mathematics II",
            "Network Analysis",
            "Electronic Devices",
            "Engineering Chemistry",
            "Communication Skills",
        ),
        (
            "Analog Circuits",
            "Digital Electronics",
            "Signals and Systems",
            "Electromagnetic Theory",
            "Engineering Mathematics III",
        ),
        (
            "Analog Communication",
            "Linear Integrated Circuits",
            "Control Systems",
            "Microprocessors",
            "Probability and Random Processes",
        ),
        (
            "Digital Communication",
            "Digital Signal Processing",
            "VLSI Design",
            "Microcontrollers and Embedded Systems",
            "Antenna and Wave Propagation",
        ),
        (
            "Wireless Communication",
            "Optical Communication",
            "Computer Networks",
            "Microwave Engineering",
            "Information Theory and Coding",
        ),
        (
            "Mobile Communication",
            "Satellite Communication",
            "Embedded System Design",
            "Radar Engineering",
            "Internet of Things",
        ),
        (
            "Advanced VLSI",
            "Image Processing",
            "5G Networks",
            "Professional Ethics",
            "Project Management",
        ),
    ),
    "ME": (
        (
            "Engineering Mathematics I",
            "Engineering Physics",
            "Engineering Mechanics",
            "Programming in C",
            "Engineering Graphics",
        ),
        (
            "Engineering Mathematics II",
            "Engineering Chemistry",
            "Basic Electrical Engineering",
            "Workshop Practice",
            "Environmental Science",
        ),
        (
            "Thermodynamics",
            "Strength of Materials",
            "Material Science",
            "Manufacturing Processes",
            "Engineering Mathematics III",
        ),
        (
            "Fluid Mechanics",
            "Theory of Machines",
            "Applied Thermodynamics",
            "Machine Drawing",
            "Metrology and Measurements",
        ),
        (
            "Heat and Mass Transfer",
            "Design of Machine Elements",
            "Dynamics of Machinery",
            "Machining Science",
            "Industrial Engineering",
        ),
        (
            "Internal Combustion Engines",
            "Finite Element Analysis",
            "Refrigeration and Air Conditioning",
            "CAD CAM",
            "Operations Research",
        ),
        (
            "Automobile Engineering",
            "Mechatronics",
            "Power Plant Engineering",
            "Robotics",
            "Computational Fluid Dynamics",
        ),
        (
            "Additive Manufacturing",
            "Renewable Energy Systems",
            "Industrial Safety",
            "Total Quality Management",
            "Project Management",
        ),
    ),
    "CE": (
        (
            "Engineering Mathematics I",
            "Engineering Physics",
            "Engineering Mechanics",
            "Programming in C",
            "Engineering Graphics",
        ),
        (
            "Engineering Mathematics II",
            "Engineering Chemistry",
            "Building Materials",
            "Surveying I",
            "Environmental Science",
        ),
        (
            "Strength of Materials",
            "Fluid Mechanics",
            "Surveying II",
            "Building Construction",
            "Engineering Geology",
        ),
        (
            "Structural Analysis I",
            "Hydraulics",
            "Concrete Technology",
            "Geotechnical Engineering I",
            "Transportation Engineering I",
        ),
        (
            "Structural Analysis II",
            "Design of Concrete Structures",
            "Geotechnical Engineering II",
            "Water Resources Engineering",
            "Environmental Engineering",
        ),
        (
            "Design of Steel Structures",
            "Transportation Engineering II",
            "Estimation and Costing",
            "Foundation Engineering",
            "Hydrology",
        ),
        (
            "Prestressed Concrete",
            "Construction Management",
            "Bridge Engineering",
            "Earthquake Engineering",
            "Remote Sensing and GIS",
        ),
        (
            "Advanced Structural Design",
            "Pavement Design",
            "Green Buildings",
            "Professional Practice",
            "Project Management",
        ),
    ),
}
DBMS_NAME = "Database Management Systems"
OS_NAME = "Operating Systems"

STUDENT1_ROLL = "24CSE012"
STUDENT2_ROLL = "25ECE037"
FORCED_GENDER = {STUDENT1_ROLL: "M"}
FORCED_HOSTELLER = {STUDENT1_ROLL: True, STUDENT2_ROLL: False}

DBMS_SECTION = (CSE, 5, "A")
ECE_DROP_SECTION = (ECE, 3, "B")
FORCED_APPROVED_SECTIONS = (DBMS_SECTION, ECE_DROP_SECTION)
DBMS_LOW_COUNT = 10
OS_LOW_ATTENDANCE_COUNT = 4
ECE_DROP_RISK_COUNT = 9
SGPA_DROP_COUNT = 3
SGPA_DROP_DEPTS = (ECE, ME, 4)
SGPA_DROP_SEMESTERS = (5, 7)

APPROVED_SHARE, PENDING_SHARE = 0.95, 0.04
REQUEST_DAY_RANGE = (6, 18)
DECISION_DELAY_DAYS = (1, 4)
TERM_YEAR = 2026

TERM_START = date(2026, 7, 21)
DROP_START = date(2026, 9, 14)
HOLIDAYS = (date(2026, 8, 28), date(2026, 10, 2), date(2026, 10, 20))
WEEKDAY_PATTERNS = ((0, 2, 4), (1, 3, 4), (0, 1, 3), (1, 2, 4))
CANCEL_SHARE = 0.03
BASE_ATTENDANCE = (0.80, 0.97)
LOW_ATTENDANCE = (0.60, 0.70)
STABLE_BEFORE, STABLE_AFTER = (0.92, 0.98), (0.65, 0.72)
RISK_BEFORE, RISK_AFTER = (0.80, 0.90), (0.40, 0.50)

MARK_COMPONENTS = (("mid1", 20), ("mid2", 20), ("assignment", 10))
BASE_INTERNAL = (0.53, 0.92)
DBMS_PASSING_INTERNAL = (0.50, 0.60)
LOW_INTERNAL = (0.20, 0.33)
COMPONENT_NOISE = 0.04
MARK_STEP = 2

ABILITY_MEAN, ABILITY_SD = 7.6, 0.75
ABILITY_MIN, ABILITY_MAX = 5.9, 9.3
SGPA_NOISE = 0.35
SGPA_DROP = (1.2, 1.6)
SGPA_MIN, SGPA_MAX = 4.0, 10.0
BACKLOG_SGPA = 5.8
BACKLOG_RANGE = (1, 2)
ME_HOSTELLER_OFFSET, ME_DAY_OFFSET = -0.25, 0.15

TUITION_FEE, EXAM_FEE, HOSTEL_FEE, MESS_FEE = 75000, 2000, 30000, 18000
PAYMENT_MODES = ("upi", "netbanking", "card", "cash")
PAYMENT_MODE_WEIGHTS = (50, 25, 15, 10)
EARLY_PAYMENT_DAYS = (1, 25)
LATE_PAYMENT_SHARE = 0.04
LATE_PAYMENT_DAYS = (3, 30)
INSTALLMENT_SHARE = 0.1
BOYS_B_DEFAULT_RATE = 0.24
OTHER_DEFAULT_RATE = 0.08
UNPAID_SHARE = 0.5
PARTIAL_PAID_RANGE = (0.3, 0.7)
ROUNDING_RUPEES = 1000
OVERPAID_COUNT = 6
OVERPAY_RANGE = (1, 10)
OVERPAY_STEP = 500
OLD_PENDING_COUNT = 5

HOSTELS = (
    (1, "Boys Hostel A", "M", "A"),
    (2, "Boys Hostel B", "M", "B"),
    (3, "Girls Hostel", "F", "G"),
)
BOYS_A, BOYS_B, GIRLS = 1, 2, 3
ROOM_CAPACITIES = (2, 3)
ROOMS_PER_FLOOR = 20
ROOM_HEADROOM = 1.15
HOSTEL_JOIN_DAYS = (15, 25)

MESSES = ((1, "Mess 1", "veg"), (2, "Mess 2", "veg"), (3, "Mess 3", "nonveg"))
MESS_2 = 2
NONVEG_MESS = 3
VEG_MESSES = (1, 2)
NONVEG_SHARE = 0.4
MESS_MONTHS = ("2026-07", "2026-08", "2026-09", "2026-10", "2026-11")
MESS_CHANGE_COUNT = 40
MESS_CHANGE_STATUS_WEIGHTS = (("approved", 0.6), ("rejected", 0.25), ("pending", 0.15))
LAST_REQUEST_DAY = 10

EXAM_START, EXAM_END = date(2026, 11, 24), date(2026, 12, 10)
SUNDAY = 6
FRIDAY = 4

FEEDBACK_PER_OFFERING = (5, 10)
DBMS_FEEDBACK_COUNT = 16
FEEDBACK_START = datetime(2026, 8, 1)
FEEDBACK_END = datetime(2026, 11, 10, 22, 0)
HINGLISH_SHARE = 0.45
SHORT_COMMENT_SHARE = 0.12
MIXED_COMMENT_SHARE = 0.25
SECOND_THEME_SHARE = 0.3
CLOSER_SHARE = 0.2
FACULTY_PROFILES = {
    "strong": (0.65, 0.2, 0.15),
    "average": (0.4, 0.35, 0.25),
    "weak": (0.2, 0.3, 0.5),
}
FACULTY_PROFILE_WEIGHTS = (0.35, 0.45, 0.2)
DBMS_SENTIMENT_WEIGHTS = (0.05, 0.15, 0.8)
SENTIMENTS = ("positive", "neutral", "negative")
RATINGS = {"positive": (4, 5), "neutral": (3,), "negative": (1, 2)}

COMPLAINT_COUNT = 300
COMPLAINT_START = datetime(2026, 7, 25)
COMPLAINT_END = datetime(2026, 11, 10, 22, 0)
COMPLAINT_CATEGORY_WEIGHTS = (
    ("mess", 0.45),
    ("hostel", 0.33),
    ("infrastructure", 0.14),
    ("other", 0.08),
)
NOVEMBER = "2026-11"
PLANTED_HYGIENE_DATES = (
    date(2026, 9, 9),
    date(2026, 9, 23),
    date(2026, 10, 14),
    date(2026, 10, 28),
    date(2026, 11, 3),
    date(2026, 11, 5),
    date(2026, 11, 9),
    date(2026, 11, 10),
)
STUDENT1_COMPLAINT_AT = datetime(2026, 10, 21, 21, 15)
FRESH_COMPLAINT_DAYS = 3
OLD_COMPLAINT_DAYS = 21
MAX_RESOLUTION_DAYS = 12
COMPLAINT_STATUS_WEIGHTS = {
    "fresh": (("open", 0.7), ("in_progress", 0.3), ("resolved", 0.0)),
    "recent": (("open", 0.25), ("in_progress", 0.3), ("resolved", 0.45)),
    "old": (("open", 0.15), ("in_progress", 0.1), ("resolved", 0.75)),
}
MESS_THEMES = ("food_quality", "hygiene", "menu_variety", "mess_timing")
HOSTEL_THEMES = (
    "room_maintenance",
    "water_supply",
    "electricity",
    "wifi",
    "security",
    "cleanliness",
)
INFRA_THEMES = ("wifi", "electricity", "water_supply", "cleanliness", "other")
CAMPUS_PLACES = (
    "Lecture Hall 1",
    "Lecture Hall 3",
    "Central Library",
    "CSE Lab 2",
    "ECE Lab 1",
    "Academic Block B",
    "Central Workshop",
)

LABEL_FEEDBACK_COUNT, LABEL_COMPLAINT_COUNT = 40, 20
LABEL_PLANTED_FEEDBACK, LABEL_PLANTED_COMPLAINTS = 4, 3

DEMO_PASSWORD = "demo123"
EXAM_CELL_GROUP = "Exam Cell – CSE"

AT_RISK_SQL = """
SELECT COUNT(DISTINCT student_id) FROM (
  SELECT a.student_id FROM attendance_summary a
  JOIN course_offerings co ON co.id = a.offering_id
  WHERE co.academic_year = %s AND a.attended * 100 < 75 * a.held
  UNION
  SELECT m.student_id FROM marks m
  JOIN course_offerings co ON co.id = m.offering_id
  WHERE co.academic_year = %s AND m.component <> 'end_sem'
  GROUP BY m.student_id, m.offering_id
  HAVING SUM(m.marks_obtained) * 100 < 40 * SUM(m.max_marks)
  UNION
  SELECT last.student_id FROM results last
  JOIN results prev ON prev.student_id = last.student_id AND prev.semester = last.semester - 1
  JOIN students st ON st.id = last.student_id AND last.semester = st.current_semester - 1
  WHERE prev.sgpa - last.sgpa >= 1.0
) at_risk
"""

TABLE_COLUMNS: dict[str, tuple[str, ...]] = {
    "departments": ("id", "code", "name"),
    "faculty": ("id", "name", "dept_id", "designation", "is_advisor", "is_hod"),
    "students": (
        "id",
        "roll_no",
        "name",
        "gender",
        "dept_id",
        "admission_year",
        "current_semester",
        "section",
        "advisor_id",
        "is_hosteller",
    ),
    "subjects": ("id", "code", "name", "dept_id", "semester", "credits"),
    "course_offerings": (
        "id",
        "subject_id",
        "faculty_id",
        "dept_id",
        "academic_year",
        "semester",
        "section",
        "planned_classes",
    ),
    "registrations": (
        "id",
        "student_id",
        "offering_id",
        "status",
        "approved_by",
        "requested_at",
        "decided_at",
    ),
    "class_sessions": ("id", "offering_id", "held_on"),
    "attendance": ("session_id", "student_id", "present"),
    "attendance_summary": ("student_id", "offering_id", "held", "attended"),
    "attendance_weekly": (
        "offering_id",
        "week_start",
        "sessions",
        "present_count",
        "possible_count",
    ),
    "marks": ("student_id", "offering_id", "component", "max_marks", "marks_obtained"),
    "results": (
        "student_id",
        "academic_year",
        "semester",
        "sgpa",
        "cgpa",
        "backlogs",
        "result_status",
    ),
    "fee_dues": (
        "id",
        "student_id",
        "academic_year",
        "semester",
        "fee_type",
        "amount_due",
        "due_date",
    ),
    "fee_payments": ("id", "fee_due_id", "amount_paid", "paid_on", "mode"),
    "exams": ("id", "offering_id", "exam_type", "exam_date"),
    "hostels": ("id", "name", "gender", "capacity"),
    "rooms": ("id", "hostel_id", "room_no", "capacity"),
    "hostel_allocations": ("student_id", "room_id", "from_date", "to_date"),
    "messes": ("id", "name", "type"),
    "mess_allocations": ("student_id", "mess_id", "month"),
    "mess_change_requests": (
        "id",
        "student_id",
        "from_mess_id",
        "to_mess_id",
        "status",
        "requested_at",
    ),
    "feedback": (
        "id",
        "offering_id",
        "faculty_id",
        "dept_id",
        "semester",
        "section",
        "rating",
        "comment",
        "submitted_at",
    ),
    "complaints": (
        "id",
        "student_id",
        "category",
        "mess_id",
        "hostel_id",
        "text",
        "status",
        "created_at",
        "resolved_at",
    ),
}

Templates = dict[str, tuple[str, ...]]

FEEDBACK_TEMPLATES: dict[str, dict[str, Templates]] = {
    "pace": {
        "positive": {
            "en": (
                "The pace of teaching is just right and easy to follow.",
                "{hon} covers topics at a comfortable speed and gives us time to take notes.",
            ),
            "hi": (
                "{hon} ki teaching speed ekdum sahi hai, sab follow ho jata hai.",
                "Padhane ki speed perfect hai, notes banane ka time mil jata hai.",
            ),
        },
        "neutral": {
            "en": (
                "Pace is okay most of the time, a few lectures felt rushed.",
                "Speed of teaching is average, sometimes a little fast.",
            ),
            "hi": (
                "Speed theek hai, kabhi kabhi thoda fast ho jata hai.",
                "Pace normal hai, bas numericals mein thoda fast lagta hai.",
            ),
        },
        "negative": {
            "en": (
                "{hon} teaches way too fast, we cannot keep up.",
                "The pace is too fast, topics are rushed and nobody understands.",
                "Lectures are rushed. Please slow down, half the class is lost.",
            ),
            "hi": (
                "{hon} bahut fast padhat{v} hain, kuch samajh nahi aata.",
                "Itni speed mein padhat{v} hain ki notes bhi nahi ban pate, thoda slow kijiye.",
                "Class bahut rush hoti hai, ek topic khatam nahi hota aur doosra shuru.",
            ),
        },
    },
    "clarity": {
        "positive": {
            "en": (
                "Concepts are explained very clearly with good examples.",
                "{hon} explains even difficult topics in a simple way.",
            ),
            "hi": (
                "{hon} concepts bahut acche se samjhat{v} hain.",
                "Har topic example ke saath clear ho jata hai, maza aata hai.",
            ),
        },
        "neutral": {
            "en": (
                "Explanations are fine but some topics could be clearer.",
                "Clarity is average, most of it makes sense after revising.",
            ),
            "hi": (
                "Explanation theek hai, par kuch topics clear nahi hote.",
                "Zyada tar samajh aa jata hai, bas derivations mein dikkat hoti hai.",
            ),
        },
        "negative": {
            "en": (
                "Explanations are confusing and jump between topics.",
                "Most of the concepts taught in class went over my head.",
            ),
            "hi": (
                "Concepts bilkul samajh nahi aate, explanation bahut confusing hai.",
                "Kuch bhi clear nahi hota, bas board pe likh ke chhod diya jaata hai.",
            ),
        },
    },
    "doubt_solving": {
        "positive": {
            "en": (
                "{hon} patiently clears every doubt, even after class.",
                "Doubt sessions are really helpful before exams.",
            ),
            "hi": (
                "Doubt poochne pe {hon} bahut patiently samjhat{v} hain.",
                "Class ke baad bhi doubts clear kar det{v} hain, bahut helpful.",
            ),
        },
        "neutral": {
            "en": (
                "Doubts are answered, but there is rarely time for them.",
                "Doubt solving is okay.",
            ),
            "hi": (
                "Doubts clear ho jaate hain par time kam milta hai.",
                "Doubt session theek thaak hai.",
            ),
        },
        "negative": {
            "en": (
                "Doubts are ignored in class and we are told to read the book.",
                "Asking a doubt feels pointless, it never gets answered properly.",
            ),
            "hi": (
                "Doubt poocho to bas 'book padh lo' bol diya jaata hai.",
                "Doubts kabhi clear nahi hote, poochne mein bhi darr lagta hai.",
            ),
        },
    },
    "punctuality": {
        "positive": {
            "en": (
                "Classes always start and end on time.",
                "{hon} is very punctual and never wastes class time.",
            ),
            "hi": (
                "{hon} hamesha time pe aat{v} hain, ek bhi class miss nahi hui.",
                "Class time pe start hoti hai, bahut disciplined.",
            ),
        },
        "neutral": {
            "en": ("Mostly on time, a few classes started late.", "Punctuality is fine."),
            "hi": (
                "Zyada tar class time pe hoti hai, kabhi kabhi 10 min late.",
                "Timing theek hai.",
            ),
        },
        "negative": {
            "en": (
                "Classes often start 15-20 minutes late.",
                "Many classes were cancelled without any notice.",
            ),
            "hi": (
                "Class hamesha late start hoti hai, aadha time waste.",
                "Bina bataye class cancel ho jaati hai, bahut problem hoti hai.",
            ),
        },
    },
    "syllabus_coverage": {
        "positive": {
            "en": (
                "The whole syllabus was covered well before the exams.",
                "Every unit is covered properly with revision at the end.",
            ),
            "hi": (
                "Syllabus time se pehle khatam ho gaya, revision bhi hua.",
                "Saare units properly cover hue, exam ki tension nahi.",
            ),
        },
        "neutral": {
            "en": (
                "Most of the syllabus is covered, the last unit is still pending.",
                "Syllabus coverage is on track so far.",
            ),
            "hi": ("Syllabus theek chal raha hai, last unit baaki hai.", "Coverage average hai."),
        },
        "negative": {
            "en": (
                "Half the syllabus is still not covered and exams are near.",
                "Important units were skipped completely.",
            ),
            "hi": (
                "Exam paas hai aur aadha syllabus baaki hai.",
                "Kai important topics skip kar diye, ab khud padhna padega.",
            ),
        },
    },
    "teaching_material": {
        "positive": {
            "en": (
                "Notes and slides shared are excellent for exam prep.",
                "Good reference material and lab manuals are provided.",
            ),
            "hi": (
                "Notes bahut acche hain, exam ke liye kaafi hain.",
                "{hon} ke slides aur PDFs bahut helpful hain.",
            ),
        },
        "neutral": {
            "en": (
                "Slides are okay, but more worked examples would help.",
                "Material is average, we mostly use YouTube.",
            ),
            "hi": ("Notes theek hain, aur examples hote to better hota.", "Material average hai."),
        },
        "negative": {
            "en": (
                "No notes or slides are shared, we depend on seniors.",
                "The slides are outdated and full of errors.",
            ),
            "hi": (
                "Koi notes nahi milte, seniors ke notes se padhte hain.",
                "Slides purane hain aur galtiyon se bhare hue hain.",
            ),
        },
    },
    "approachability": {
        "positive": {
            "en": (
                "{hon} is very approachable and friendly.",
                "Easy to talk to about anything, even career advice.",
            ),
            "hi": (
                "{hon} bahut friendly hain, kuch bhi pooch sakte hain.",
                "Cabin mein jaake baat karna easy hai, hamesha help kart{v} hain.",
            ),
        },
        "neutral": {
            "en": (
                "Approachable but hard to find outside class hours.",
                "Neither too strict nor too friendly.",
            ),
            "hi": (
                "Baat kar sakte hain par cabin mein milna mushkil hai.",
                "Theek hain, na zyada strict na zyada friendly.",
            ),
        },
        "negative": {
            "en": (
                "Very strict and not approachable at all.",
                "Students are scared to talk to {hon}.",
            ),
            "hi": (
                "Bahut strict hain, koi baat karne se darta hai.",
                "{hon} se kuch poochna matlab daant khana.",
            ),
        },
    },
    "assessment_fairness": {
        "positive": {
            "en": (
                "Evaluation is fair and answer sheets are shown to us.",
                "Marking is transparent and the mid-sem papers are fair.",
            ),
            "hi": (
                "Marking bilkul fair hai, copies bhi dikhayi jaati hain.",
                "Paper syllabus ke andar se hi aata hai, fair hai.",
            ),
        },
        "neutral": {
            "en": (
                "Marking is a bit strict but okay.",
                "Assignments are fine, the mid-sem paper was lengthy.",
            ),
            "hi": (
                "Marking thodi strict hai par theek hai.",
                "Mid-sem paper lamba tha, baaki theek.",
            ),
        },
        "negative": {
            "en": (
                "Marking is unfair, mid-sem questions were out of syllabus.",
                "Assignment marks are given randomly without checking.",
            ),
            "hi": (
                "Paper out of syllabus aaya aur marking bhi bahut strict thi.",
                "Assignment ke marks bina check kiye de diye.",
            ),
        },
    },
}
CORE_THEMES = tuple(FEEDBACK_TEMPLATES)
SHORT_COMMENTS: dict[str, Templates] = {
    "positive": {
        "en": ("Great class!", "Best teacher this semester.", "Very good."),
        "hi": ("Bahut badhiya class.", "Mast padhat{v} hain."),
    },
    "neutral": {
        "en": ("Okay.", "Nothing much to say.", "Average class."),
        "hi": ("Theek hai.", "Thik thak."),
    },
    "negative": {
        "en": ("Not good.", "Needs a lot of improvement."),
        "hi": ("Bilkul accha nahi.", "Bekar class."),
    },
}
CLOSERS: dict[str, Templates] = {
    "positive": {
        "en": ("Thank you {hon}!", "Keep it up."),
        "hi": ("Thank you {hon}!", "Aise hi padhate rahiye."),
    },
    "neutral": {"en": ("Overall okay.",), "hi": ("Overall theek hai.",)},
    "negative": {
        "en": ("Please look into this.", "Hope this improves next semester."),
        "hi": ("Please isko improve kijiye.", "Next sem se sudhar ho please."),
    },
}
CONTRAST = {"en": "However, ", "hi": "Lekin "}

NEGATIVE, NEUTRAL = "negative", "neutral"
COMPLAINT_TEMPLATES: dict[str, dict[str, tuple[tuple[str, str], ...]]] = {
    "food_quality": {
        "en": (
            ("Food in {place} is often stale and undercooked.", NEGATIVE),
            ("Dal in {place} is watery every day and the rotis are hard.", NEGATIVE),
            ("Rice was half-cooked again at {place} lunch today.", NEGATIVE),
        ),
        "hi": (
            ("{place} ka khana bilkul bekar hai, roti kacchi hoti hai.", NEGATIVE),
            ("Aaj phir {place} mein sabzi mein namak hi nahi tha.", NEGATIVE),
            ("Khana thanda milta hai {place} mein, taste bhi nahi.", NEGATIVE),
        ),
    },
    "hygiene": {
        "en": (
            ("Plates in {place} are not washed properly, very unhygienic.", NEGATIVE),
            ("Saw cockroaches near the serving counter in {place}. Hygiene is terrible.", NEGATIVE),
            ("Kitchen area of {place} is dirty and there are flies everywhere.", NEGATIVE),
        ),
        "hi": (
            ("{place} mein plates gandi milti hain, hygiene ka koi dhyan nahi.", NEGATIVE),
            ("Khane mein keeda mila aaj {place} mein, kitchen bahut ganda hai.", NEGATIVE),
            ("{place} ke counter pe cockroach ghoom rahe the, safai bilkul nahi hoti.", NEGATIVE),
        ),
    },
    "menu_variety": {
        "en": (
            ("Same menu repeats in {place} every week, please add variety.", NEGATIVE),
            ("Request to add more fruits and a weekly special in {place}.", NEUTRAL),
            ("Paneer is on the menu but never served in {place}.", NEGATIVE),
        ),
        "hi": (
            ("{place} mein roz wahi aloo ki sabzi, menu change karo please.", NEGATIVE),
            ("{place} mein Sunday ko kuch special add kar sakte hain kya?", NEUTRAL),
        ),
    },
    "mess_timing": {
        "en": (
            ("Breakfast in {place} closes at 8:30, students with 8 AM labs miss it.", NEGATIVE),
            ("Please extend dinner timing in {place} till 10 PM during exams.", NEUTRAL),
        ),
        "hi": (
            (
                "{place} mein dinner 9 baje hi band ho jata hai, lab se aake khana nahi milta.",
                NEGATIVE,
            ),
            ("Nashte ka time bahut kam hai {place} mein.", NEGATIVE),
        ),
    },
    "room_maintenance": {
        "en": (
            ("Fan in room {room} of {place} has not worked for a week.", NEGATIVE),
            (
                "Cupboard door in room {room} is broken, {place} maintenance has not come yet.",
                NEGATIVE,
            ),
            ("Window glass of room {room} in {place} is broken.", NEGATIVE),
        ),
        "hi": (
            ("Room {room} ka fan kharab hai, complaint ke baad bhi koi nahi aaya.", NEGATIVE),
            ("{place} room {room} mein seepage ho raha hai, deewar geeli hai.", NEGATIVE),
        ),
    },
    "water_supply": {
        "en": (
            ("No water in the bathrooms of {place} since morning.", NEGATIVE),
            ("Water cooler near {place} is not working.", NEGATIVE),
            ("Hot water is not available in {place} in the mornings.", NEGATIVE),
        ),
        "hi": (
            ("{place} mein subah se paani nahi aa raha.", NEGATIVE),
            ("Water cooler kharab hai {place} mein, peene ka paani nahi milta.", NEGATIVE),
        ),
    },
    "electricity": {
        "en": (
            ("Power cuts in {place} every evening and the backup does not work.", NEGATIVE),
            ("Power socket near my seat in {place} gives sparks, it is dangerous.", NEGATIVE),
        ),
        "hi": (
            ("{place} mein raat ko light chali jaati hai, padhai nahi ho paati.", NEGATIVE),
            ("Inverter backup kaam nahi karta {place} mein.", NEGATIVE),
        ),
    },
    "wifi": {
        "en": (
            ("WiFi in {place} is extremely slow after 10 PM.", NEGATIVE),
            ("Cannot connect to the WiFi in {place} for 3 days now.", NEGATIVE),
        ),
        "hi": (
            ("{place} ka wifi bilkul nahi chalta, online submissions miss ho rahe hain.", NEGATIVE),
            ("Wifi raat ko bahut slow ho jaata hai {place} mein.", NEGATIVE),
        ),
    },
    "security": {
        "en": (
            ("Main gate of {place} is left unattended at night.", NEGATIVE),
            ("Outsiders were seen roaming inside {place} late at night.", NEGATIVE),
        ),
        "hi": (
            ("{place} ke gate pe raat ko guard nahi hota.", NEGATIVE),
            ("Cycle chori ho gayi {place} se, CCTV kaam nahi kar raha.", NEGATIVE),
        ),
    },
    "cleanliness": {
        "en": (
            ("Washrooms in {place} are not cleaned for days.", NEGATIVE),
            ("Garbage is piling up in the corridor of {place}.", NEGATIVE),
        ),
        "hi": (
            ("{place} ke washroom ki safai nahi hoti, bahut badbu aati hai.", NEGATIVE),
            ("Corridor mein kachra pada rehta hai {place} mein.", NEGATIVE),
        ),
    },
    "other": {
        "en": (
            ("Projector in {place} has not worked for two weeks.", NEGATIVE),
            ("Several benches in {place} are broken.", NEGATIVE),
            ("Please keep {place} open till midnight during exams.", NEUTRAL),
        ),
        "hi": (
            ("{place} mein projector kharab hai, padhai mein dikkat.", NEGATIVE),
            ("{place} mein benches toote hue hain.", NEGATIVE),
        ),
    },
}


@dataclass(frozen=True)
class Faculty:
    id: int
    name: str
    dept_id: int
    designation: str
    is_advisor: bool
    is_hod: bool
    honorific: str
    verb_ending: str
    profile: str


@dataclass(frozen=True)
class Student:
    id: int
    roll_no: str
    name: str
    gender: str
    dept_id: int
    admission_year: int
    current_semester: int
    section: str
    advisor_id: int
    is_hosteller: bool


@dataclass(frozen=True)
class Offering:
    id: int
    subject_id: int
    subject_name: str
    faculty_id: int
    dept_id: int
    semester: int
    section: str
    planned_classes: int

    @property
    def cohort(self) -> tuple[int, int, str]:
        return (self.dept_id, self.semester, self.section)


@dataclass
class Planted:
    dbms_offering_id: int = 0
    os_offering_id: int = 0
    dbms_low: list[int] = field(default_factory=list)
    os_low: list[int] = field(default_factory=list)
    ece_drop_risk: list[int] = field(default_factory=list)
    sgpa_drop: list[int] = field(default_factory=list)


@dataclass
class Dataset:
    tables: dict[str, list[tuple[Any, ...]]] = field(default_factory=lambda: defaultdict(list))
    faculty: list[Faculty] = field(default_factory=list)
    students: list[Student] = field(default_factory=list)
    offerings: list[Offering] = field(default_factory=list)
    approved: dict[int, list[int]] = field(default_factory=lambda: defaultdict(list))
    hostel_of: dict[int, int] = field(default_factory=dict)
    room_of: dict[int, str] = field(default_factory=dict)
    mess_of: dict[tuple[int, str], int] = field(default_factory=dict)
    planted: Planted = field(default_factory=Planted)
    feedback_items: list[dict[str, Any]] = field(default_factory=list)
    complaint_items: list[dict[str, Any]] = field(default_factory=list)
    officials: dict[str, str] = field(default_factory=dict)

    def student_by_roll(self, roll_no: str) -> Student:
        return next(s for s in self.students if s.roll_no == roll_no)


def faculty_id_for(dept_id: int, index: int) -> int:
    return (dept_id - 1) * FACULTY_PER_DEPT + index + 1


def academic_year_label(year: int) -> str:
    return f"{year}-{(year + 1) % 100:02d}"


def random_datetime(rng: random.Random, start: datetime, end: datetime) -> datetime:
    return start + timedelta(seconds=rng.randint(0, int((end - start).total_seconds())))


def weighted_choice(rng: random.Random, weighted: tuple[tuple[str, float], ...]) -> str:
    names, weights = zip(*weighted, strict=True)
    return rng.choices(names, weights=weights)[0]


def round_to_step(value: float, step: int) -> float:
    return round(value * step) / step


def build_departments(dataset: Dataset) -> None:
    dataset.tables["departments"] = [
        (dept_id, code, name) for dept_id, code, name, _ in DEPARTMENTS
    ]


def make_faculty(rng: random.Random, fake: Faker, dept_id: int, index: int) -> Faculty:
    female = rng.random() < FACULTY_FEMALE_SHARE
    first = fake.first_name_female() if female else fake.first_name_male()
    designation = DESIGNATIONS[index]
    doctor = designation != "Assistant Professor" or rng.random() < DOCTOR_SHARE_ASSISTANT
    name = f"{'Dr. ' if doctor else ''}{first} {fake.last_name()}"
    profile = rng.choices(tuple(FACULTY_PROFILES), weights=FACULTY_PROFILE_WEIGHTS)[0]
    return Faculty(
        id=faculty_id_for(dept_id, index),
        name=name,
        dept_id=dept_id,
        designation=designation,
        is_advisor=index in ADVISOR_INDEXES,
        is_hod=index == HOD_INDEX,
        honorific="Ma'am" if female else "Sir",
        verb_ending="i" if female else "e",
        profile=profile,
    )


def build_faculty(rng: random.Random, fake: Faker, dataset: Dataset) -> None:
    for dept_id, *_ in DEPARTMENTS:
        for index in range(FACULTY_PER_DEPT):
            dataset.faculty.append(make_faculty(rng, fake, dept_id, index))
    dataset.tables["faculty"] = [
        (f.id, f.name, f.dept_id, f.designation, f.is_advisor, f.is_hod) for f in dataset.faculty
    ]


def make_student(
    rng: random.Random, fake: Faker, student_id: int, dept: tuple[int, str], year: int, serial: int
) -> Student:
    dept_id, code = dept
    roll_no = f"{year % 100:02d}{code}{serial:03d}"
    gender = "F" if rng.random() < FEMALE_SHARE else "M"
    gender = FORCED_GENDER.get(roll_no, gender)
    hosteller = FORCED_HOSTELLER.get(roll_no, rng.random() < HOSTELLER_SHARE)
    first = fake.first_name_female() if gender == "F" else fake.first_name_male()
    advisor_index = ADVISOR_INDEXES[ADMISSION_YEARS.index(year)]
    return Student(
        id=student_id,
        roll_no=roll_no,
        name=f"{first} {fake.last_name()}",
        gender=gender,
        dept_id=dept_id,
        admission_year=year,
        current_semester=CURRENT_SEMESTER_BY_YEAR[year],
        section=SECTIONS[(serial - 1) // STUDENTS_PER_SECTION],
        advisor_id=faculty_id_for(dept_id, advisor_index),
        is_hosteller=hosteller,
    )


def build_students(rng: random.Random, fake: Faker, dataset: Dataset) -> None:
    for dept_id, code, *_ in DEPARTMENTS:
        for year in ADMISSION_YEARS:
            for serial in range(1, STUDENTS_PER_BATCH + 1):
                student_id = len(dataset.students) + 1
                student = make_student(rng, fake, student_id, (dept_id, code), year, serial)
                dataset.students.append(student)
    dataset.tables["students"] = [
        (
            s.id,
            s.roll_no,
            s.name,
            s.gender,
            s.dept_id,
            s.admission_year,
            s.current_semester,
            s.section,
            s.advisor_id,
            s.is_hosteller,
        )
        for s in dataset.students
    ]


def build_subjects(dataset: Dataset) -> dict[tuple[int, int], list[tuple[int, str]]]:
    by_semester: dict[tuple[int, int], list[tuple[int, str]]] = {}
    rows = []
    for dept_id, code, _, prefix in DEPARTMENTS:
        for semester, names in enumerate(SUBJECT_NAMES[code], start=1):
            by_semester[(dept_id, semester)] = []
            for index, name in enumerate(names):
                subject_id = len(rows) + 1
                credits = CORE_CREDITS if index < CORE_CREDIT_SUBJECTS else ELECTIVE_CREDITS
                rows.append(
                    (
                        subject_id,
                        f"{prefix}{semester}0{index + 1}",
                        name,
                        dept_id,
                        semester,
                        credits,
                    )
                )
                by_semester[(dept_id, semester)].append((subject_id, name))
    dataset.tables["subjects"] = rows
    return by_semester


def teaching_slots(
    subjects: dict[tuple[int, int], list[tuple[int, str]]], dept_id: int
) -> list[tuple[int, str, int, str]]:
    return [
        (subject_id, name, semester, section)
        for semester in CURRENT_SEMESTERS
        for subject_id, name in subjects[(dept_id, semester)]
        for section in SECTIONS
    ]


def assign_teachers(rng: random.Random, slot_count: int, dept_id: int) -> list[int]:
    teachers = [faculty_id_for(dept_id, index) for index in range(FACULTY_PER_DEPT)]
    rng.shuffle(teachers)
    loads = list(TEACHING_LOADS)
    rng.shuffle(loads)
    owners = [teacher for teacher, load in zip(teachers, loads, strict=True) for _ in range(load)]
    return owners[:slot_count]


def give_slot(owners: list[int], slot: int, faculty_id: int, keep: set[int]) -> None:
    previous = owners[slot]
    if previous == faculty_id:
        return
    spare = next(i for i, owner in enumerate(owners) if owner == faculty_id and i not in keep)
    owners[spare] = previous
    owners[slot] = faculty_id


def pin_faculty1_slots(slots: list[tuple[int, str, int, str]], owners: list[int]) -> None:
    wanted = [
        index
        for index, (_, name, semester, section) in enumerate(slots)
        if semester == DBMS_SECTION[1]
        and section == DBMS_SECTION[2]
        and name in (DBMS_NAME, OS_NAME)
    ]
    for slot in wanted:
        give_slot(owners, slot, faculty_id_for(CSE, FACULTY1_INDEX), set(wanted))


def offering_row(o: Offering) -> tuple[Any, ...]:
    return (
        o.id,
        o.subject_id,
        o.faculty_id,
        o.dept_id,
        CURRENT_ACADEMIC_YEAR,
        o.semester,
        o.section,
        o.planned_classes,
    )


def build_offerings(
    rng: random.Random, dataset: Dataset, subjects: dict[tuple[int, int], list[tuple[int, str]]]
) -> None:
    for dept_id, *_ in DEPARTMENTS:
        slots = teaching_slots(subjects, dept_id)
        owners = assign_teachers(rng, len(slots), dept_id)
        if dept_id == CSE:
            pin_faculty1_slots(slots, owners)
        planned = {subject_id: rng.randint(*PLANNED_CLASSES_RANGE) for subject_id, *_ in slots}
        for (subject_id, name, semester, section), faculty_id in zip(slots, owners, strict=True):
            offering_id = len(dataset.offerings) + 1
            fields = (subject_id, name, faculty_id, dept_id, semester, section, planned[subject_id])
            dataset.offerings.append(Offering(offering_id, *fields))
    dataset.tables["course_offerings"] = [offering_row(o) for o in dataset.offerings]


def registration_status(rng: random.Random, cohort: tuple[int, int, str]) -> str:
    if cohort in FORCED_APPROVED_SECTIONS:
        return "approved"
    roll = rng.random()
    if roll < APPROVED_SHARE:
        return "approved"
    return "pending" if roll < APPROVED_SHARE + PENDING_SHARE else "rejected"


def build_registrations(rng: random.Random, dataset: Dataset) -> None:
    by_cohort: dict[tuple[int, int, str], list[Offering]] = defaultdict(list)
    for offering in dataset.offerings:
        by_cohort[offering.cohort].append(offering)
    rows = dataset.tables["registrations"]
    for student in dataset.students:
        cohort = (student.dept_id, student.current_semester, student.section)
        requested = datetime(TERM_YEAR, 7, rng.randint(*REQUEST_DAY_RANGE), rng.randint(9, 20))
        for offering in by_cohort[cohort]:
            status = registration_status(rng, cohort)
            decided = (
                None
                if status == "pending"
                else requested
                + timedelta(days=rng.randint(*DECISION_DELAY_DAYS), hours=rng.randint(0, 6))
            )
            approver = None if status == "pending" else student.advisor_id
            rows.append(
                (len(rows) + 1, student.id, offering.id, status, approver, requested, decided)
            )
            if status == "approved":
                dataset.approved[offering.id].append(student.id)


def cohort_students(dataset: Dataset, cohort: tuple[int, int, str]) -> list[Student]:
    return [s for s in dataset.students if (s.dept_id, s.current_semester, s.section) == cohort]


def offering_named(dataset: Dataset, cohort: tuple[int, int, str], name: str) -> Offering:
    return next(o for o in dataset.offerings if o.cohort == cohort and o.subject_name == name)


def sample_with(rng: random.Random, pool: list[int], forced: int | None, count: int) -> list[int]:
    others = [student_id for student_id in pool if student_id != forced]
    picked = rng.sample(others, count - (forced is not None))
    return sorted(([forced] if forced is not None else []) + picked)


def choose_planted(rng: random.Random, dataset: Dataset) -> None:
    planted = dataset.planted
    planted.dbms_offering_id = offering_named(dataset, DBMS_SECTION, DBMS_NAME).id
    planted.os_offering_id = offering_named(dataset, DBMS_SECTION, OS_NAME).id
    dbms_pool = [s.id for s in cohort_students(dataset, DBMS_SECTION)]
    student1 = dataset.student_by_roll(STUDENT1_ROLL).id
    planted.dbms_low = sample_with(rng, dbms_pool, student1, DBMS_LOW_COUNT)
    os_pool = [i for i in dbms_pool if i not in planted.dbms_low]
    planted.os_low = sample_with(rng, os_pool, None, OS_LOW_ATTENDANCE_COUNT)
    ece_pool = [s.id for s in cohort_students(dataset, ECE_DROP_SECTION)]
    student2 = dataset.student_by_roll(STUDENT2_ROLL).id
    planted.ece_drop_risk = sample_with(rng, ece_pool, student2, ECE_DROP_RISK_COUNT)
    drop_pool = [
        s.id
        for s in dataset.students
        if s.dept_id in SGPA_DROP_DEPTS and s.current_semester in SGPA_DROP_SEMESTERS
    ]
    planted.sgpa_drop = sample_with(rng, drop_pool, None, SGPA_DROP_COUNT)


def session_dates(rng: random.Random, offering: Offering, today: date) -> list[date]:
    pattern = WEEKDAY_PATTERNS[offering.id % len(WEEKDAY_PATTERNS)]
    dates = []
    day = TERM_START
    while day <= today:
        if day.weekday() in pattern and day not in HOLIDAYS and rng.random() >= CANCEL_SHARE:
            dates.append(day)
        day += timedelta(days=1)
    return dates


def attendance_rates(
    rng: random.Random, student_id: int, offering: Offering, planted: Planted
) -> tuple[float, float]:
    if offering.id == planted.os_offering_id and student_id in planted.os_low:
        rate = rng.uniform(*LOW_ATTENDANCE)
        return rate, rate
    if offering.cohort == ECE_DROP_SECTION and student_id in planted.ece_drop_risk:
        return rng.uniform(*RISK_BEFORE), rng.uniform(*RISK_AFTER)
    if offering.cohort == ECE_DROP_SECTION:
        return rng.uniform(*STABLE_BEFORE), rng.uniform(*STABLE_AFTER)
    rate = rng.uniform(*BASE_ATTENDANCE)
    return rate, rate


def absent_indexes(rng: random.Random, dates: list[date], rates: tuple[float, float]) -> set[int]:
    before = [i for i, day in enumerate(dates) if day < DROP_START]
    after = [i for i, day in enumerate(dates) if day >= DROP_START]
    absent: set[int] = set()
    for indexes, rate in ((before, rates[0]), (after, rates[1])):
        absent.update(rng.sample(indexes, round((1 - rate) * len(indexes))))
    return absent


def build_sessions(rng: random.Random, dataset: Dataset, today: date) -> dict[int, list[date]]:
    dates_by_offering = {}
    rows = dataset.tables["class_sessions"]
    for offering in dataset.offerings:
        dates_by_offering[offering.id] = session_dates(rng, offering, today)
        start = len(rows)
        rows.extend(
            [
                (start + i + 1, offering.id, day)
                for i, day in enumerate(dates_by_offering[offering.id])
            ]
        )
    return dates_by_offering


def build_attendance(rng: random.Random, dataset: Dataset, today: date) -> None:
    dates_by_offering = build_sessions(rng, dataset, today)
    session_id = 0
    for offering in dataset.offerings:
        dates = dates_by_offering[offering.id]
        weekly: dict[date, list[int]] = defaultdict(lambda: [0, 0])
        for student_id in dataset.approved[offering.id]:
            rates = attendance_rates(rng, student_id, offering, dataset.planted)
            absent = absent_indexes(rng, dates, rates)
            add_student_attendance(dataset, session_id, student_id, len(dates), absent)
            dataset.tables["attendance_summary"].append(
                (student_id, offering.id, len(dates), len(dates) - len(absent))
            )
            for index, day in enumerate(dates):
                weekly[day - timedelta(days=day.weekday())][index not in absent] += 1
        add_weekly_rows(dataset, offering, dates, weekly)
        session_id += len(dates)


def add_student_attendance(
    dataset: Dataset, first_session: int, student_id: int, count: int, absent: set[int]
) -> None:
    dataset.tables["attendance"].extend(
        (first_session + index + 1, student_id, index not in absent) for index in range(count)
    )


def add_weekly_rows(
    dataset: Dataset, offering: Offering, dates: list[date], weekly: dict[date, list[int]]
) -> None:
    students = len(dataset.approved[offering.id])
    sessions_per_week: dict[date, int] = defaultdict(int)
    for day in dates:
        sessions_per_week[day - timedelta(days=day.weekday())] += 1
    dataset.tables["attendance_weekly"].extend(
        (offering.id, week, sessions, weekly[week][1], sessions * students)
        for week, sessions in sorted(sessions_per_week.items())
    )


def internal_target(
    rng: random.Random, student_id: int, offering_id: int, planted: Planted
) -> float:
    if offering_id != planted.dbms_offering_id:
        return rng.uniform(*BASE_INTERNAL)
    if student_id in planted.dbms_low:
        return rng.uniform(*LOW_INTERNAL)
    return rng.uniform(*DBMS_PASSING_INTERNAL)


def build_marks(rng: random.Random, dataset: Dataset) -> None:
    rows = dataset.tables["marks"]
    for offering in dataset.offerings:
        for student_id in dataset.approved[offering.id]:
            target = internal_target(rng, student_id, offering.id, dataset.planted)
            for component, maximum in MARK_COMPONENTS:
                share = target + rng.uniform(-COMPONENT_NOISE, COMPONENT_NOISE)
                obtained = round_to_step(min(max(share, 0.0), 1.0) * maximum, MARK_STEP)
                rows.append((student_id, offering.id, component, maximum, obtained))


def ability_offset(dept_id: int, is_hosteller: bool) -> float:
    if dept_id != ME:
        return 0.0
    return ME_HOSTELLER_OFFSET if is_hosteller else ME_DAY_OFFSET


def student_abilities(rng: random.Random, students: list[Student]) -> dict[int, float]:
    raw = {s.id: rng.gauss(ABILITY_MEAN, ABILITY_SD) for s in students}
    groups: dict[tuple[int, int, bool], list[int]] = defaultdict(list)
    for s in students:
        groups[(s.dept_id, s.admission_year, s.is_hosteller)].append(s.id)
    abilities = {}
    for (dept_id, _, is_hosteller), ids in groups.items():
        shift = ABILITY_MEAN + ability_offset(dept_id, is_hosteller) - mean(raw[i] for i in ids)
        abilities.update({i: min(max(raw[i] + shift, ABILITY_MIN), ABILITY_MAX) for i in ids})
    return abilities


def semester_sgpas(
    rng: random.Random, student: Student, ability: float, drops: bool
) -> list[float]:
    sgpas = [
        ability + rng.uniform(-SGPA_NOISE, SGPA_NOISE) for _ in range(student.current_semester - 1)
    ]
    if drops and len(sgpas) > 1:
        sgpas[-1] = sgpas[-2] - rng.uniform(*SGPA_DROP)
    return [round(min(max(value, SGPA_MIN), SGPA_MAX), 2) for value in sgpas]


def build_results(rng: random.Random, dataset: Dataset) -> None:
    abilities = student_abilities(rng, dataset.students)
    rows = dataset.tables["results"]
    for student in dataset.students:
        drops = student.id in dataset.planted.sgpa_drop
        sgpas = semester_sgpas(rng, student, abilities[student.id], drops)
        for semester, sgpa in enumerate(sgpas, start=1):
            year = student.admission_year + (semester - 1) // 2
            cgpa = round(mean(sgpas[:semester]), 2)
            backlogs = rng.randint(*BACKLOG_RANGE) if sgpa < BACKLOG_SGPA else 0
            status = "fail" if backlogs else "pass"
            rows.append(
                (student.id, academic_year_label(year), semester, sgpa, cgpa, backlogs, status)
            )


def due_dates(year: int, semester: int) -> tuple[date, date]:
    if semester % 2:
        return date(year, 8, 14), date(year, 10, 31)
    return date(year + 1, 1, 14), date(year + 1, 3, 31)


def student_dues(student: Student) -> list[tuple[str, int, str, int, date]]:
    dues = []
    for semester in range(1, student.current_semester + 1):
        year = student.admission_year + (semester - 1) // 2
        label = academic_year_label(year)
        main_due, exam_due = due_dates(year, semester)
        dues.append((label, semester, "tuition", TUITION_FEE, main_due))
        dues.append((label, semester, "exam", EXAM_FEE, exam_due))
        if student.is_hosteller:
            dues.append((label, semester, "hostel", HOSTEL_FEE, main_due))
            dues.append((label, semester, "mess", MESS_FEE, main_due))
    return dues


def pick_defaulters(rng: random.Random, dataset: Dataset) -> set[int]:
    groups: dict[int, list[int]] = defaultdict(list)
    for student in dataset.students:
        groups[dataset.hostel_of.get(student.id, 0)].append(student.id)
    student1 = dataset.student_by_roll(STUDENT1_ROLL).id
    defaulters: set[int] = set()
    for hostel_id in sorted(groups):
        rate = BOYS_B_DEFAULT_RATE if hostel_id == BOYS_B else OTHER_DEFAULT_RATE
        forced = student1 if hostel_id == BOYS_B else None
        defaulters.update(
            sample_with(rng, groups[hostel_id], forced, round(rate * len(groups[hostel_id])))
        )
    return defaulters


def pick_fee_specials(rng: random.Random, dataset: Dataset, defaulters: set[int]) -> dict[int, str]:
    payers = [s.id for s in dataset.students if s.id not in defaulters]
    overpaid = rng.sample(payers, OVERPAID_COUNT)
    seniors = [
        s.id
        for s in dataset.students
        if s.id not in defaulters
        and s.id not in overpaid
        and not s.is_hosteller
        and s.current_semester > 1
    ]
    specials = {student_id: "overpaid" for student_id in overpaid}
    specials.update(
        {student_id: "old_pending" for student_id in rng.sample(seniors, OLD_PENDING_COUNT)}
    )
    specials.update({student_id: "defaulter" for student_id in sorted(defaulters)})
    return specials


def payment_mode(rng: random.Random) -> str:
    return rng.choices(PAYMENT_MODES, weights=PAYMENT_MODE_WEIGHTS)[0]


def paid_date(rng: random.Random, due_date: date, today: date) -> date:
    if rng.random() < LATE_PAYMENT_SHARE:
        return min(due_date + timedelta(days=rng.randint(*LATE_PAYMENT_DAYS)), today)
    return due_date - timedelta(days=rng.randint(*EARLY_PAYMENT_DAYS))


def full_payment(
    rng: random.Random, amount: int, due_date: date, today: date
) -> list[tuple[int, date, str]]:
    paid_on = paid_date(rng, due_date, today)
    if rng.random() >= INSTALLMENT_SHARE:
        return [(amount, paid_on, payment_mode(rng))]
    first = amount // 2
    earlier = paid_on - timedelta(days=rng.randint(*EARLY_PAYMENT_DAYS))
    return [(first, earlier, payment_mode(rng)), (amount - first, paid_on, payment_mode(rng))]


def partial_payment(rng: random.Random, amount: int, due_date: date) -> list[tuple[int, date, str]]:
    if rng.random() < UNPAID_SHARE:
        return []
    paid = round(amount * rng.uniform(*PARTIAL_PAID_RANGE) / ROUNDING_RUPEES) * ROUNDING_RUPEES
    return [
        (
            max(paid, ROUNDING_RUPEES),
            due_date - timedelta(days=rng.randint(*EARLY_PAYMENT_DAYS)),
            payment_mode(rng),
        )
    ]


def short_dues(
    rng: random.Random, kind: str | None, dues: list[tuple[str, int, str, int, date]]
) -> set[int]:
    if kind == "defaulter":
        current = [i for i, due in enumerate(dues) if due[0] == CURRENT_ACADEMIC_YEAR]
        return set(rng.sample(current, rng.randint(1, 2)))
    if kind == "old_pending":
        old = [
            i for i, due in enumerate(dues) if due[0] != CURRENT_ACADEMIC_YEAR and due[2] == "exam"
        ]
        return {rng.choice(old)}
    return set()


def due_payments(
    rng: random.Random,
    kind: str | None,
    flags: tuple[bool, bool],
    due: tuple[int, date],
    today: date,
) -> list[tuple[int, date, str]]:
    amount, due_date = due
    is_short, is_last = flags
    if is_short:
        return partial_payment(rng, amount, due_date)
    payments = full_payment(rng, amount, due_date, today)
    if kind == "overpaid" and is_last:
        extra = rng.randint(*OVERPAY_RANGE) * OVERPAY_STEP
        payments.append((extra, due_date, payment_mode(rng)))
    return payments


def build_fees(rng: random.Random, dataset: Dataset, today: date) -> None:
    specials = pick_fee_specials(rng, dataset, pick_defaulters(rng, dataset))
    dues_rows, payment_rows = dataset.tables["fee_dues"], dataset.tables["fee_payments"]
    for student in dataset.students:
        kind = specials.get(student.id)
        dues = student_dues(student)
        short = short_dues(rng, kind, dues)
        for index, (label, semester, fee_type, amount, due_date) in enumerate(dues):
            due_id = len(dues_rows) + 1
            dues_rows.append((due_id, student.id, label, semester, fee_type, amount, due_date))
            flags = (index in short, index == len(dues) - 1)
            payments = due_payments(rng, kind, flags, (amount, due_date), today)
            start = len(payment_rows)
            payment_rows.extend([(start + i + 1, due_id, *p) for i, p in enumerate(payments)])


def assign_hostels(rng: random.Random, dataset: Dataset) -> dict[int, list[int]]:
    occupants: dict[int, list[int]] = defaultdict(list)
    student1 = dataset.student_by_roll(STUDENT1_ROLL).id
    for student in dataset.students:
        if not student.is_hosteller:
            continue
        if student.gender == "F":
            occupants[GIRLS].append(student.id)
        elif student.id == student1:
            occupants[BOYS_B].append(student.id)
        else:
            occupants[rng.choice((BOYS_A, BOYS_B))].append(student.id)
    return occupants


def make_rooms(
    rng: random.Random, hostel: tuple[int, str], needed_beds: float, first_id: int
) -> list[tuple[int, int, str, int]]:
    hostel_id, prefix = hostel
    rooms: list[tuple[int, int, str, int]] = []
    beds = 0
    while beds < needed_beds:
        index = len(rooms)
        capacity = rng.choice(ROOM_CAPACITIES)
        room_no = f"{prefix}-{index // ROOMS_PER_FLOOR + 1}{index % ROOMS_PER_FLOOR + 1:02d}"
        rooms.append((first_id + index, hostel_id, room_no, capacity))
        beds += capacity
    return rooms


def allocate_rooms(
    rng: random.Random,
    dataset: Dataset,
    rooms: list[tuple[int, int, str, int]],
    occupants: list[int],
) -> None:
    queue = rng.sample(occupants, len(occupants))
    beds = [
        (room_id, hostel_id, room_no)
        for room_id, hostel_id, room_no, size in rooms
        for _ in range(size)
    ]
    years = {s.id: s.admission_year for s in dataset.students}
    for (room_id, hostel_id, room_no), student_id in zip(beds, queue, strict=False):
        joined = date(years[student_id], 7, rng.randint(*HOSTEL_JOIN_DAYS))
        dataset.tables["hostel_allocations"].append((student_id, room_id, joined, None))
        dataset.hostel_of[student_id] = hostel_id
        dataset.room_of[student_id] = room_no


def build_hostels(rng: random.Random, dataset: Dataset) -> None:
    occupants = assign_hostels(rng, dataset)
    for hostel_id, name, gender, prefix in HOSTELS:
        first_id = len(dataset.tables["rooms"]) + 1
        rooms = make_rooms(
            rng, (hostel_id, prefix), len(occupants[hostel_id]) * ROOM_HEADROOM, first_id
        )
        dataset.tables["rooms"].extend(rooms)
        dataset.tables["hostels"].append((hostel_id, name, gender, sum(room[3] for room in rooms)))
        allocate_rooms(rng, dataset, rooms, occupants[hostel_id])


def initial_mess(rng: random.Random) -> int:
    return NONVEG_MESS if rng.random() < NONVEG_SHARE else rng.choice(VEG_MESSES)


def request_time(rng: random.Random, month_index: int) -> datetime:
    year, month = (int(part) for part in MESS_MONTHS[month_index].split("-"))
    last_day = LAST_REQUEST_DAY if month_index == len(MESS_MONTHS) - 1 else 25
    return datetime(year, month, rng.randint(1, last_day), rng.randint(8, 22), rng.randint(0, 59))


def mess_change(rng: random.Random, plan: list[int]) -> tuple[int, int, str, datetime]:
    month_index = rng.randrange(len(MESS_MONTHS))
    from_mess = plan[month_index]
    to_mess = rng.choice([mess_id for mess_id, *_ in MESSES if mess_id != from_mess])
    last_month = month_index == len(MESS_MONTHS) - 1
    status = "pending" if last_month else weighted_choice(rng, MESS_CHANGE_STATUS_WEIGHTS)
    if status == "approved":
        plan[month_index + 1 :] = [to_mess] * (len(MESS_MONTHS) - month_index - 1)
    return from_mess, to_mess, status, request_time(rng, month_index)


def build_messes(rng: random.Random, dataset: Dataset) -> None:
    dataset.tables["messes"] = list(MESSES)
    hostellers = [s.id for s in dataset.students if s.is_hosteller]
    plans = {student_id: [initial_mess(rng)] * len(MESS_MONTHS) for student_id in hostellers}
    requests = [
        (student_id, *mess_change(rng, plans[student_id]))
        for student_id in rng.sample(hostellers, MESS_CHANGE_COUNT)
    ]
    requests.sort(key=lambda request: request[-1])
    dataset.tables["mess_change_requests"] = [
        (i + 1, *request) for i, request in enumerate(requests)
    ]
    for student_id, plan in plans.items():
        for month, mess_id in zip(MESS_MONTHS, plan, strict=True):
            dataset.tables["mess_allocations"].append((student_id, mess_id, month))
            dataset.mess_of[(student_id, month)] = mess_id


def exam_days() -> list[date]:
    span = (EXAM_END - EXAM_START).days + 1
    days = (EXAM_START + timedelta(days=offset) for offset in range(span))
    return [day for day in days if day.weekday() != SUNDAY]


def build_exams(rng: random.Random, dataset: Dataset) -> None:
    subjects_by_term: dict[tuple[int, int], list[int]] = defaultdict(list)
    for offering in dataset.offerings:
        term = subjects_by_term[(offering.dept_id, offering.semester)]
        if offering.subject_id not in term:
            term.append(offering.subject_id)
    schedule = {}
    for subject_ids in subjects_by_term.values():
        dates = sorted(rng.sample(exam_days(), len(subject_ids)))
        schedule.update(zip(subject_ids, dates, strict=True))
    dataset.tables["exams"] = [
        (index + 1, offering.id, "end_sem", schedule[offering.subject_id])
        for index, offering in enumerate(dataset.offerings)
    ]


def pick_language(rng: random.Random) -> str:
    return "hi" if rng.random() < HINGLISH_SHARE else "en"


def contrast_comment(rng: random.Random, lang: str) -> tuple[str, list[str]]:
    good, bad = rng.sample(CORE_THEMES, 2)
    first = rng.choice(FEEDBACK_TEMPLATES[good]["positive"][lang])
    second = rng.choice(FEEDBACK_TEMPLATES[bad]["negative"][lang])
    return f"{first} {CONTRAST[lang]}{second[0].lower()}{second[1:]}", [good, bad]


def compose_feedback(
    rng: random.Random, sentiment: str, lang: str, forced_theme: str | None
) -> tuple[str, list[str]]:
    if forced_theme is None and rng.random() < SHORT_COMMENT_SHARE:
        return rng.choice(SHORT_COMMENTS[sentiment][lang]), ["other"]
    if forced_theme is None and sentiment == NEUTRAL and rng.random() < MIXED_COMMENT_SHARE:
        return contrast_comment(rng, lang)
    themes = [forced_theme or rng.choice(CORE_THEMES)]
    if rng.random() < SECOND_THEME_SHARE:
        themes.append(rng.choice([theme for theme in CORE_THEMES if theme != themes[0]]))
    parts = [rng.choice(FEEDBACK_TEMPLATES[theme][sentiment][lang]) for theme in themes]
    if rng.random() < CLOSER_SHARE:
        parts.append(rng.choice(CLOSERS[sentiment][lang]))
    return " ".join(parts), themes


def make_feedback(
    rng: random.Random, offering: Offering, faculty: Faculty, planted: bool
) -> dict[str, Any]:
    weights = DBMS_SENTIMENT_WEIGHTS if planted else FACULTY_PROFILES[faculty.profile]
    sentiment = rng.choices(SENTIMENTS, weights=weights)[0]
    lang = pick_language(rng)
    forced_theme = "pace" if planted and sentiment == NEGATIVE else None
    template, themes = compose_feedback(rng, sentiment, lang, forced_theme)
    return {
        "row": (
            offering.id,
            faculty.id,
            offering.dept_id,
            offering.semester,
            offering.section,
            rng.choice(RATINGS[sentiment]),
            template.format(hon=faculty.honorific, v=faculty.verb_ending),
            random_datetime(rng, FEEDBACK_START, FEEDBACK_END),
        ),
        "sentiment": sentiment,
        "themes": themes,
        "lang": lang,
        "planted": planted,
    }


def build_feedback(rng: random.Random, dataset: Dataset) -> None:
    faculty = {f.id: f for f in dataset.faculty}
    items = []
    for offering in dataset.offerings:
        planted = offering.id == dataset.planted.dbms_offering_id
        count = DBMS_FEEDBACK_COUNT if planted else rng.randint(*FEEDBACK_PER_OFFERING)
        items.extend(
            make_feedback(rng, offering, faculty[offering.faculty_id], planted)
            for _ in range(count)
        )
    items.sort(key=lambda item: item["row"][-1])
    for index, item in enumerate(items, start=1):
        item["id"] = index
        dataset.tables["feedback"].append((index, *item["row"]))
    dataset.feedback_items = items


def complaint_status(
    rng: random.Random, created_at: datetime, today: date
) -> tuple[str, datetime | None]:
    age = (today - created_at.date()).days
    bucket = (
        "fresh" if age <= FRESH_COMPLAINT_DAYS else "recent" if age <= OLD_COMPLAINT_DAYS else "old"
    )
    status = weighted_choice(rng, COMPLAINT_STATUS_WEIGHTS[bucket])
    if status != "resolved":
        return status, None
    hours = rng.uniform(FRESH_COMPLAINT_DAYS, min(age, MAX_RESOLUTION_DAYS) * 24)
    return status, min(
        created_at + timedelta(hours=hours), datetime.combine(today, datetime.min.time())
    )


def complaint_item(
    rng: random.Random,
    target: tuple[int, int | None, int | None, str, str],
    category: str,
    theme: str,
    created_at: datetime,
    today: date,
) -> dict[str, Any]:
    student_id, mess_id, hostel_id, place, room = target
    lang = pick_language(rng)
    template, sentiment = rng.choice(COMPLAINT_TEMPLATES[theme][lang])
    status, resolved_at = complaint_status(rng, created_at, today)
    text = template.format(place=place, room=room)
    return {
        "row": (student_id, category, mess_id, hostel_id, text, status, created_at, resolved_at),
        "category": category,
        "sentiment": sentiment,
        "themes": [theme],
        "lang": lang,
        "planted": False,
    }


def complaint_target(
    rng: random.Random, dataset: Dataset, category: str, created_at: datetime
) -> tuple[int, int | None, int | None, str, str]:
    if category == "mess":
        student_id = rng.choice(sorted(dataset.hostel_of))
        mess_id = dataset.mess_of[(student_id, created_at.strftime("%Y-%m"))]
        return student_id, mess_id, None, MESSES[mess_id - 1][1], ""
    if category == "hostel":
        student_id = rng.choice(sorted(dataset.hostel_of))
        hostel_id = dataset.hostel_of[student_id]
        return student_id, None, hostel_id, HOSTELS[hostel_id - 1][1], dataset.room_of[student_id]
    return rng.choice(dataset.students).id, None, None, rng.choice(CAMPUS_PLACES), ""


def complaint_theme(rng: random.Random, category: str, created_at: datetime) -> str:
    if category == "mess" and created_at.strftime("%Y-%m") == NOVEMBER:
        return rng.choice([theme for theme in MESS_THEMES if theme != "hygiene"])
    if category == "mess":
        return rng.choice(MESS_THEMES)
    if category == "hostel":
        return rng.choice(HOSTEL_THEMES)
    return rng.choice(INFRA_THEMES) if category == "infrastructure" else "other"


def planted_complaints(rng: random.Random, dataset: Dataset, today: date) -> list[dict[str, Any]]:
    items = []
    for day in PLANTED_HYGIENE_DATES:
        month = day.strftime("%Y-%m")
        members = sorted(
            sid for (sid, m), mess in dataset.mess_of.items() if m == month and mess == MESS_2
        )
        created = datetime.combine(day, datetime.min.time()) + timedelta(
            minutes=rng.randint(480, 1320)
        )
        target = (rng.choice(members), MESS_2, None, MESSES[MESS_2 - 1][1], "")
        items.append(
            complaint_item(rng, target, "mess", "hygiene", created, today) | {"planted": True}
        )
    student1 = dataset.student_by_roll(STUDENT1_ROLL).id
    target = (student1, None, BOYS_B, HOSTELS[BOYS_B - 1][1], dataset.room_of[student1])
    items.append(
        complaint_item(rng, target, "hostel", "water_supply", STUDENT1_COMPLAINT_AT, today)
    )
    return items


def build_complaints(rng: random.Random, dataset: Dataset, today: date) -> None:
    items = planted_complaints(rng, dataset, today)
    while len(items) < COMPLAINT_COUNT:
        category = weighted_choice(rng, COMPLAINT_CATEGORY_WEIGHTS)
        created_at = random_datetime(rng, COMPLAINT_START, COMPLAINT_END)
        target = complaint_target(rng, dataset, category, created_at)
        theme = complaint_theme(rng, category, created_at)
        items.append(complaint_item(rng, target, category, theme, created_at, today))
    items.sort(key=lambda item: item["row"][6])
    for index, item in enumerate(items, start=1):
        item["id"] = index
        dataset.tables["complaints"].append((index, *item["row"]))
    dataset.complaint_items = items


def pick_labels(
    rng: random.Random,
    items: list[dict[str, Any]],
    counts: tuple[int, int],
    group_fields: tuple[str, ...],
) -> list[dict[str, Any]]:
    total, planted_quota = counts
    chosen = rng.sample([item for item in items if item["planted"]], planted_quota)
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        if not item["planted"]:
            groups[tuple(item[name] for name in group_fields)].append(item)
    queues = [rng.sample(groups[key], len(groups[key])) for key in sorted(groups)]
    while len(chosen) < total:
        for queue in queues:
            if queue and len(chosen) < total:
                chosen.append(queue.pop())
    return sorted(chosen, key=lambda item: item["id"])


def label_entry(item: dict[str, Any], text_index: int) -> dict[str, Any]:
    return {
        "id": item["id"],
        "text": item["row"][text_index],
        "sentiment": item["sentiment"],
        "themes": item["themes"],
    }


def write_labels(dataset: Dataset) -> None:
    rng = random.Random(LABEL_SEED)
    feedback = pick_labels(
        rng,
        dataset.feedback_items,
        (LABEL_FEEDBACK_COUNT, LABEL_PLANTED_FEEDBACK),
        ("sentiment", "lang"),
    )
    complaints = pick_labels(
        rng,
        dataset.complaint_items,
        (LABEL_COMPLAINT_COUNT, LABEL_PLANTED_COMPLAINTS),
        ("category", "sentiment", "lang"),
    )
    labels = {
        "feedback": [
            label_entry(item, TABLE_COLUMNS["feedback"].index("comment") - 1) for item in feedback
        ],
        "complaints": [
            label_entry(item, TABLE_COLUMNS["complaints"].index("text") - 1) for item in complaints
        ],
    }
    LABELS_PATH.parent.mkdir(parents=True, exist_ok=True)
    LABELS_PATH.write_text(json.dumps(labels, ensure_ascii=False, indent=2) + "\n")
    logger.info(
        "Wrote %d feedback and %d complaint labels to %s",
        len(feedback),
        len(complaints),
        LABELS_PATH,
    )


def build_dataset(today: date) -> Dataset:
    rng = random.Random(SEED)
    fake = Faker("en_IN")
    fake.seed_instance(SEED)
    dataset = Dataset()
    build_departments(dataset)
    build_faculty(rng, fake, dataset)
    build_students(rng, fake, dataset)
    build_offerings(rng, dataset, build_subjects(dataset))
    build_registrations(rng, dataset)
    choose_planted(rng, dataset)
    build_attendance(rng, dataset, today)
    build_marks(rng, dataset)
    build_results(rng, dataset)
    build_exams(rng, dataset)
    build_hostels(rng, dataset)
    build_messes(rng, dataset)
    build_fees(rng, dataset, today)
    build_feedback(rng, dataset)
    build_complaints(rng, dataset, today)
    dataset.officials = {
        key: f"{fake.first_name()} {fake.last_name()}" for key in ("dean", "admin", "admin2")
    }
    return dataset


@dataclass(frozen=True)
class SeededUser:
    username: str
    display_name: str
    password: str
    roles: tuple[str, ...]
    student_id: int | None = None
    faculty_id: int | None = None
    dept_id: int | None = None
    groups: tuple[str, ...] = ()
    is_platform_admin: bool = False


def student_user(username: str, student: Student) -> SeededUser:
    return SeededUser(
        username,
        student.name,
        DEMO_PASSWORD,
        ("student",),
        student_id=student.id,
        dept_id=student.dept_id,
    )


def faculty_user(
    username: str, faculty: Faculty, roles: tuple[str, ...], groups: tuple[str, ...] = ()
) -> SeededUser:
    return SeededUser(
        username,
        faculty.name,
        DEMO_PASSWORD,
        roles,
        faculty_id=faculty.id,
        dept_id=faculty.dept_id,
        groups=groups,
    )


def seeded_users(dataset: Dataset, settings: Settings) -> list[SeededUser]:
    faculty = {f.id: f for f in dataset.faculty}
    cse = {index: faculty[faculty_id_for(CSE, index)] for index in range(FACULTY_PER_DEPT)}
    names = dataset.officials
    return [
        student_user("student1", dataset.student_by_roll(STUDENT1_ROLL)),
        student_user("student2", dataset.student_by_roll(STUDENT2_ROLL)),
        faculty_user("faculty1", cse[FACULTY1_INDEX], ("faculty",)),
        faculty_user("faculty2", cse[FACULTY2_INDEX], ("faculty",), (EXAM_CELL_GROUP,)),
        faculty_user("advisor1", cse[ADVISOR1_INDEX], ("faculty", "advisor")),
        faculty_user("hod_cse", cse[HOD_INDEX], ("faculty", "advisor", "hod")),
        SeededUser("dean", f"Dr. {names['dean']}", DEMO_PASSWORD, ("dean",)),
        SeededUser("admin", names["admin"], DEMO_PASSWORD, ("admin",)),
        SeededUser("admin2", names["admin2"], DEMO_PASSWORD, ("admin",)),
        SeededUser(
            "platform_admin",
            "Platform Admin",
            settings.platform_admin_password,
            (),
            is_platform_admin=True,
        ),
    ]


def connect(settings: Settings, database: str) -> Any:
    return mysql.connector.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user="root",
        password=settings.root_password,
        database=database,
        autocommit=False,
    )


def wipe_schema(cursor: Any, schema: str) -> None:
    cursor.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = %s AND table_type = 'BASE TABLE'",
        (schema,),
    )
    for (table,) in cursor.fetchall():
        cursor.execute(f"TRUNCATE TABLE `{schema}`.`{table}`")


def insert_rows(cursor: Any, table: str, rows: list[tuple[Any, ...]]) -> None:
    columns = TABLE_COLUMNS[table]
    placeholders = ", ".join(["%s"] * len(columns))
    sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
    for start in range(0, len(rows), BATCH_SIZE):
        cursor.executemany(sql, rows[start : start + BATCH_SIZE])


def load_campus(settings: Settings, dataset: Dataset) -> None:
    connection = connect(settings, settings.mysql_db)
    try:
        cursor = connection.cursor()
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        wipe_schema(cursor, settings.mysql_db)
        for table in TABLE_COLUMNS:
            insert_rows(cursor, table, dataset.tables[table])
            logger.info("%-22s %7d rows", table, len(dataset.tables[table]))
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        connection.commit()
    finally:
        connection.close()


def insert_user(
    cursor: Any, user: SeededUser, role_ids: dict[str, int], group_ids: dict[str, int]
) -> None:
    cursor.execute(
        "INSERT INTO users (username, display_name, password_hash, is_platform_admin, student_id, "
        "faculty_id, dept_id) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (
            user.username,
            user.display_name,
            hash_password(user.password),
            user.is_platform_admin,
            user.student_id,
            user.faculty_id,
            user.dept_id,
        ),
    )
    user_id = cursor.lastrowid
    for role in user.roles:
        cursor.execute(
            "INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)", (user_id, role_ids[role])
        )
    for group in user.groups:
        cursor.execute(
            "INSERT INTO group_members (group_id, user_id) VALUES (%s, %s)",
            (group_ids[group], user_id),
        )


def load_auth(settings: Settings, users: list[SeededUser]) -> None:
    connection = connect(settings, settings.mysql_auth_db)
    try:
        cursor = connection.cursor()
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        wipe_schema(cursor, settings.mysql_auth_db)
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        load_policy(cursor, read_policy())
        cursor.execute("SELECT name, id FROM roles")
        role_ids = dict(cursor.fetchall())
        cursor.execute("SELECT name, id FROM user_groups")
        group_ids = dict(cursor.fetchall())
        for user in users:
            insert_user(cursor, user, role_ids, group_ids)
        connection.commit()
        logger.info("Loaded access policy and %d seeded users", len(users))
    finally:
        connection.close()


def log_at_risk(settings: Settings) -> None:
    connection = connect(settings, settings.mysql_db)
    try:
        cursor = connection.cursor()
        cursor.execute(AT_RISK_SQL, (CURRENT_ACADEMIC_YEAR, CURRENT_ACADEMIC_YEAR))
        logger.info("At-risk students: %d", cursor.fetchone()[0])
    finally:
        connection.close()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = get_settings()
    dataset = build_dataset(settings.app_today)
    load_campus(settings, dataset)
    load_auth(settings, seeded_users(dataset, settings))
    write_labels(dataset)
    log_at_risk(settings)


if __name__ == "__main__":
    main()
