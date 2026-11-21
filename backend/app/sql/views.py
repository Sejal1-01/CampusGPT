from functools import cache

from app.sql.registry import Column, LogicalView, col, view

ACADEMICS_SELF = ("academics", "self")
ACADEMICS_CLASSES = ("academics", "own_classes")
ACADEMICS_ADVISEES = ("academics", "advisees")
ACADEMICS_DEPARTMENT = ("academics", "department")
ACADEMICS_COLLEGE = ("academics", "college")

ATTENDANCE_BASE = """
SELECT a.student_id, a.offering_id, s.code AS subject_code, s.name AS subject_name,
       co.semester, co.section, co.dept_id, co.faculty_id, a.held, a.attended,
       co.planned_classes AS planned,
       ROUND(a.attended * 100 / NULLIF(a.held, 0), 2) AS attendance_percent,
       CASE WHEN GREATEST(co.planned_classes, a.held) = 0 THEN NULL
            ELSE GREATEST(co.planned_classes, a.held)
                 - CEIL(GREATEST(co.planned_classes, a.held) * 75 / 100) - (a.held - a.attended)
       END AS can_skip,
       ROUND((a.attended + GREATEST(co.planned_classes - a.held, 0)) * 100
             / NULLIF(GREATEST(co.planned_classes, a.held), 0), 2) AS best_possible_percent
FROM attendance_summary a
JOIN course_offerings co ON co.id = a.offering_id
JOIN subjects s ON s.id = co.subject_id
WHERE co.academic_year = {year}
"""

MARKS_BASE = """
SELECT mp.student_id, mp.offering_id, s.code AS subject_code, s.name AS subject_name,
       co.semester, co.section, co.dept_id, co.faculty_id,
       mp.mid1, mp.mid2, mp.assignment, mp.end_sem, mp.internal_obtained, mp.internal_max,
       ROUND(mp.internal_obtained * 100 / NULLIF(mp.internal_max, 0), 2) AS internal_percent,
       (mp.internal_obtained * 100 / NULLIF(mp.internal_max, 0) >= 40) AS internal_pass
FROM (
  SELECT m.student_id, m.offering_id,
         MAX(CASE WHEN m.component = 'mid1' THEN m.marks_obtained END) AS mid1,
         MAX(CASE WHEN m.component = 'mid2' THEN m.marks_obtained END) AS mid2,
         MAX(CASE WHEN m.component = 'assignment' THEN m.marks_obtained END) AS assignment,
         MAX(CASE WHEN m.component = 'end_sem' THEN m.marks_obtained END) AS end_sem,
         SUM(CASE WHEN m.component <> 'end_sem' THEN m.marks_obtained END) AS internal_obtained,
         SUM(CASE WHEN m.component <> 'end_sem' THEN m.max_marks END) AS internal_max
  FROM marks m
  GROUP BY m.student_id, m.offering_id
) mp
JOIN course_offerings co ON co.id = mp.offering_id
JOIN subjects s ON s.id = co.subject_id
WHERE co.academic_year = {year}
"""

REGISTRATION_BASE = """
SELECT r.student_id, r.offering_id, s.code AS subject_code, s.name AS subject_name, s.credits,
       co.semester, co.section, co.dept_id, co.faculty_id, f.name AS faculty_name, r.status,
       DATE(r.requested_at) AS requested_on, DATE(r.decided_at) AS decided_on
FROM registrations r
JOIN course_offerings co ON co.id = r.offering_id
JOIN subjects s ON s.id = co.subject_id
JOIN faculty f ON f.id = co.faculty_id
WHERE co.academic_year = {year}
"""

FEEDBACK_BASE = """
SELECT fb.id AS feedback_id, fb.offering_id, s.code AS subject_code, s.name AS subject_name,
       fb.faculty_id, f.name AS faculty_name, d.code AS dept_code, fb.semester, fb.section,
       fb.rating, fb.comment, DATE(fb.submitted_at) AS submitted_on,
       ft.sentiment, ft.summary
FROM feedback fb
JOIN course_offerings co ON co.id = fb.offering_id
JOIN subjects s ON s.id = co.subject_id
JOIN faculty f ON f.id = fb.faculty_id
JOIN departments d ON d.id = fb.dept_id
LEFT JOIN feedback_tags ft ON ft.feedback_id = fb.id
"""

FEEDBACK_THEMES_BASE = """
SELECT th.feedback_id, fb.offering_id, s.code AS subject_code, fb.faculty_id, f.name AS faculty_name,
       d.code AS dept_code, th.theme, DATE(fb.submitted_at) AS submitted_on
FROM feedback_themes th
JOIN feedback fb ON fb.id = th.feedback_id
JOIN course_offerings co ON co.id = fb.offering_id
JOIN subjects s ON s.id = co.subject_id
JOIN faculty f ON f.id = fb.faculty_id
JOIN departments d ON d.id = fb.dept_id
"""

RESULTS_BASE = """
SELECT r.student_id, st.roll_no, st.name AS student_name, d.code AS dept_code,
       r.academic_year, r.semester, r.sgpa, r.cgpa, r.backlogs, r.result_status
FROM results r
JOIN students st ON st.id = r.student_id
JOIN departments d ON d.id = st.dept_id
"""

WEEKLY_BASE = """
SELECT aw.offering_id, s.code AS subject_code, s.name AS subject_name, co.semester, co.section,
       co.dept_id, co.faculty_id, d.code AS dept_code, aw.week_start, aw.sessions,
       ROUND(aw.present_count * 100 / NULLIF(aw.possible_count, 0), 2) AS attendance_percent
FROM attendance_weekly aw
JOIN course_offerings co ON co.id = aw.offering_id
JOIN subjects s ON s.id = co.subject_id
JOIN departments d ON d.id = co.dept_id
WHERE co.academic_year = {year}
"""

FEE_STATUS_BASE = """
SELECT fd.id AS fee_due_id, fd.student_id, st.roll_no, st.name AS student_name, d.code AS dept_code,
       st.current_semester, fd.academic_year, fd.semester, fd.fee_type, fd.amount_due,
       COALESCE(p.paid, 0) AS paid,
       GREATEST(fd.amount_due - COALESCE(p.paid, 0), 0) AS pending,
       GREATEST(COALESCE(p.paid, 0) - fd.amount_due, 0) AS credit,
       fd.due_date,
       (fd.amount_due - COALESCE(p.paid, 0) > 0 AND fd.due_date < {today}) AS is_overdue
FROM fee_dues fd
JOIN students st ON st.id = fd.student_id
JOIN departments d ON d.id = st.dept_id
LEFT JOIN (SELECT fee_due_id, SUM(amount_paid) AS paid FROM fee_payments GROUP BY fee_due_id) p
  ON p.fee_due_id = fd.id
"""

COMPLAINTS_BASE = """
SELECT c.id AS complaint_id, c.student_id, st.roll_no, st.name AS student_name, d.code AS dept_code,
       c.category, c.mess_id, m.name AS mess_name, c.hostel_id, h.name AS hostel_name, c.text,
       c.status, DATE(c.created_at) AS created_on, DATE(c.resolved_at) AS resolved_on,
       ct.sentiment, ct.summary
FROM complaints c
JOIN students st ON st.id = c.student_id
JOIN departments d ON d.id = st.dept_id
LEFT JOIN messes m ON m.id = c.mess_id
LEFT JOIN hostels h ON h.id = c.hostel_id
LEFT JOIN complaint_tags ct ON ct.complaint_id = c.id
"""

STUDENT_BASE = """
SELECT st.id AS student_id, st.roll_no, st.name AS student_name, st.gender, d.code AS dept_code,
       st.admission_year, st.current_semester, st.section, adv.name AS advisor_name
FROM students st
JOIN departments d ON d.id = st.dept_id
LEFT JOIN faculty adv ON adv.id = st.advisor_id
"""


def _wrap(base: str, alias: str, where: str) -> str:
    return f"SELECT * FROM ({base}) {alias} WHERE {where}"


STUDENT_ID = col("student_id", "int", "Internal student id (join key)")
ROLL_NO = col("roll_no", "string", "Roll number, e.g. 24CSE045")
STUDENT_NAME = col("student_name", "string", "Student full name")
DEPT_CODE = col("dept_code", "string", "Department code", "CSE", "ECE", "ME", "CE")
OFFERING_ID = col("offering_id", "int", "Course offering id: one subject taught to one section")
SUBJECT_CODE = col("subject_code", "string", "Subject code, e.g. CS301")
SUBJECT_NAME = col("subject_name", "string", "Subject name, e.g. Database Management Systems")
SEMESTER = col("semester", "int", "Semester number 1-8")
SECTION = col("section", "string", "Class section", "A", "B")
FACULTY_ID = col("faculty_id", "int", "Teacher's faculty id")
FACULTY_NAME = col("faculty_name", "string", "Teacher name")

ATTENDANCE_COLUMNS = [
    OFFERING_ID,
    SUBJECT_CODE,
    SUBJECT_NAME,
    SEMESTER,
    SECTION,
    col("held", "int", "Classes held so far this semester"),
    col("attended", "int", "Classes attended so far"),
    col("planned", "int", "Total classes planned for the whole semester"),
    col("attendance_percent", "decimal", "attended / held * 100 (0-100); NULL if none held"),
    col(
        "can_skip",
        "int",
        "More classes that can be missed while finishing at >= 75%. Negative = 75% is no longer "
        "reachable (then report best_possible_percent)",
    ),
    col(
        "best_possible_percent",
        "decimal",
        "Highest final attendance % reachable by attending every remaining class",
    ),
]

MARKS_COLUMNS = [
    OFFERING_ID,
    SUBJECT_CODE,
    SUBJECT_NAME,
    SEMESTER,
    SECTION,
    col("mid1", "decimal", "Mid-semester test 1 marks, out of 20"),
    col("mid2", "decimal", "Mid-semester test 2 marks, out of 20"),
    col("assignment", "decimal", "Assignment marks, out of 10"),
    col("end_sem", "decimal", "End-semester exam marks out of 100; NULL until the exam is held"),
    col("internal_obtained", "decimal", "mid1 + mid2 + assignment"),
    col("internal_max", "decimal", "Maximum internal marks (50)"),
    col("internal_percent", "decimal", "internal_obtained / internal_max * 100"),
    col(
        "internal_pass",
        "boolean (0/1)",
        "1 if internal_percent >= 40. Pass percentage this semester = AVG(internal_pass) * 100",
    ),
]

RESULT_COLUMNS = [
    STUDENT_ID,
    ROLL_NO,
    STUDENT_NAME,
    DEPT_CODE,
    col("academic_year", "string", "Academic year, e.g. 2025-26"),
    col("semester", "int", "Semester number of this result (completed semesters only)"),
    col("sgpa", "decimal", "Semester GPA on a 10-point scale"),
    col("cgpa", "decimal", "Cumulative GPA up to this semester"),
    col("backlogs", "int", "Number of failed subjects pending in this semester"),
    col("result_status", "string", "Outcome of the semester", "pass", "fail"),
]

FEEDBACK_COLUMNS = [
    col("feedback_id", "int", "Anonymous feedback id; there is no student identity"),
    OFFERING_ID,
    SUBJECT_CODE,
    SUBJECT_NAME,
    FACULTY_ID,
    FACULTY_NAME,
    DEPT_CODE,
    SEMESTER,
    SECTION,
    col("rating", "int", "Rating 1 (poor) to 5 (excellent)"),
    col("comment", "string", "Free-text comment (English or Hinglish)"),
    col("submitted_on", "date", "Date submitted, YYYY-MM-DD"),
    col("sentiment", "string", "Tagged sentiment", "positive", "neutral", "negative"),
    col("summary", "string", "One-line tagged summary of the comment"),
]

TEACHING_THEMES = (
    "pace",
    "clarity",
    "doubt_solving",
    "punctuality",
    "syllabus_coverage",
    "teaching_material",
    "approachability",
    "assessment_fairness",
    "other",
)
COMPLAINT_THEMES = (
    "food_quality",
    "hygiene",
    "menu_variety",
    "mess_timing",
    "room_maintenance",
    "water_supply",
    "electricity",
    "wifi",
    "security",
    "cleanliness",
    "other",
)

FEEDBACK_THEME_COLUMNS = [
    col("feedback_id", "int", "Feedback id (join to the feedback view)"),
    OFFERING_ID,
    SUBJECT_CODE,
    FACULTY_ID,
    FACULTY_NAME,
    DEPT_CODE,
    col(
        "theme", "string", "One theme of the comment; a comment can have several", *TEACHING_THEMES
    ),
    col("submitted_on", "date", "Date submitted, YYYY-MM-DD"),
]

WEEKLY_COLUMNS = [
    OFFERING_ID,
    SUBJECT_CODE,
    SUBJECT_NAME,
    SEMESTER,
    SECTION,
    DEPT_CODE,
    col("week_start", "date", "Monday of the week, YYYY-MM-DD"),
    col("sessions", "int", "Classes held that week"),
    col("attendance_percent", "decimal", "Share of students present that week, 0-100"),
]

REGISTRATION_COLUMNS = [
    OFFERING_ID,
    SUBJECT_CODE,
    SUBJECT_NAME,
    col("credits", "int", "Subject credits"),
    SEMESTER,
    SECTION,
    FACULTY_NAME,
    col(
        "status",
        "string",
        "Registration status (approved by the advisor)",
        "pending",
        "approved",
        "rejected",
    ),
    col("requested_on", "date", "Date requested"),
    col("decided_on", "date", "Date approved/rejected; NULL if pending"),
]


def _student_views() -> list[LogicalView]:
    return [
        view(
            "my_profile",
            "Your own student profile: roll number, department, semester, section, advisor.",
            [ACADEMICS_SELF],
            STUDENT_BASE.replace(
                "adv.name AS advisor_name", "adv.name AS advisor_name, st.is_hosteller"
            )
            + " WHERE st.id = {student_id}",
            [
                STUDENT_ID,
                ROLL_NO,
                STUDENT_NAME,
                col("gender", "string", "Gender", "M", "F"),
                DEPT_CODE,
                col("admission_year", "int", "Year of admission"),
                col("current_semester", "int", "Current semester number"),
                SECTION,
                col("advisor_name", "string", "Faculty advisor name"),
                col("is_hosteller", "boolean (0/1)", "1 if living in a hostel"),
            ],
            [("What is my roll number?", "SELECT roll_no, student_name FROM my_profile")],
        ),
        view(
            "my_registrations",
            "Your subject registrations for the current semester and their approval status.",
            [ACADEMICS_SELF],
            _wrap(REGISTRATION_BASE, "r", "r.student_id = {student_id}"),
            [STUDENT_ID, *REGISTRATION_COLUMNS],
            [
                (
                    "Which registrations are pending?",
                    "SELECT subject_code, subject_name, status FROM my_registrations WHERE status = 'pending'",
                )
            ],
        ),
        view(
            "my_attendance",
            "Your attendance per current subject: held, attended, planned and percentage.",
            [ACADEMICS_SELF],
            _wrap(ATTENDANCE_BASE, "a", "a.student_id = {student_id}"),
            [STUDENT_ID, *ATTENDANCE_COLUMNS],
            [
                (
                    "What is my attendance in DBMS?",
                    "SELECT subject_name, held, attended, attendance_percent FROM my_attendance "
                    "WHERE subject_name LIKE '%Database%' OR subject_code LIKE '%DBMS%'",
                ),
                (
                    "How many classes can I skip in OS and stay above 75%?",
                    "SELECT subject_name, held, attended, planned, attendance_percent, can_skip, "
                    "best_possible_percent FROM my_attendance WHERE subject_name LIKE '%Operating%'",
                ),
            ],
        ),
        view(
            "my_marks",
            "Your internal marks per current subject (mid1, mid2, assignment, end_sem).",
            [ACADEMICS_SELF],
            _wrap(MARKS_BASE, "m", "m.student_id = {student_id}"),
            [STUDENT_ID, *MARKS_COLUMNS],
            [
                (
                    "Show my marks",
                    "SELECT subject_name, mid1, mid2, assignment, internal_percent FROM my_marks",
                )
            ],
        ),
        view(
            "my_results",
            "Your results for each completed semester: SGPA, CGPA, backlogs.",
            [ACADEMICS_SELF],
            _wrap(RESULTS_BASE, "r", "r.student_id = {student_id}"),
            RESULT_COLUMNS,
            [
                (
                    "What is my CGPA?",
                    "SELECT cgpa, semester FROM my_results ORDER BY semester DESC LIMIT 1",
                )
            ],
        ),
        view(
            "my_fees",
            "Your fee dues with amount paid, pending amount, due date and overdue flag.",
            [("fees", "self")],
            _wrap(FEE_STATUS_BASE, "f", "f.student_id = {student_id}"),
            _fee_status_columns(),
            [("How much fee is pending?", "SELECT SUM(pending) AS total_pending FROM my_fees")],
        ),
        view(
            "my_payments",
            "Your fee payment history.",
            [("fees", "self")],
            """
            SELECT p.id AS payment_id, p.fee_due_id, fd.fee_type, fd.academic_year, fd.semester,
                   p.amount_paid, p.paid_on, p.mode
            FROM fee_payments p JOIN fee_dues fd ON fd.id = p.fee_due_id
            WHERE fd.student_id = {student_id}
            """,
            [
                col("payment_id", "int", "Payment id"),
                col("fee_due_id", "int", "Fee due id"),
                col("fee_type", "string", "Fee type", "tuition", "hostel", "mess", "exam"),
                col("academic_year", "string", "Academic year"),
                SEMESTER,
                col("amount_paid", "decimal", "Amount paid in INR"),
                col("paid_on", "date", "Payment date"),
                col("mode", "string", "Payment mode", "upi", "netbanking", "card", "cash"),
            ],
            [
                (
                    "Fee payment history",
                    "SELECT paid_on, fee_type, amount_paid, mode FROM my_payments ORDER BY paid_on DESC",
                )
            ],
        ),
        view(
            "my_exams",
            "Your upcoming and past exams for registered subjects this semester.",
            [ACADEMICS_SELF],
            """
            SELECT e.offering_id, s.code AS subject_code, s.name AS subject_name, e.exam_type, e.exam_date
            FROM exams e
            JOIN course_offerings co ON co.id = e.offering_id
            JOIN subjects s ON s.id = co.subject_id
            JOIN registrations r ON r.offering_id = e.offering_id AND r.status = 'approved'
            WHERE r.student_id = {student_id} AND co.academic_year = {year}
            """,
            [
                OFFERING_ID,
                SUBJECT_CODE,
                SUBJECT_NAME,
                col("exam_type", "string", "Exam type", "end_sem"),
                col("exam_date", "date", "Exam date, YYYY-MM-DD"),
            ],
            [
                (
                    "When is my next exam?",
                    "SELECT subject_name, exam_date FROM my_exams WHERE exam_date >= '2026-11-11' "
                    "ORDER BY exam_date LIMIT 1",
                )
            ],
        ),
        view(
            "my_hostel",
            "Your hostel and room allocation (empty if you are a day scholar).",
            [("hostel", "self")],
            """
            SELECT h.name AS hostel_name, rm.room_no, ha.from_date, ha.to_date
            FROM hostel_allocations ha
            JOIN rooms rm ON rm.id = ha.room_id
            JOIN hostels h ON h.id = rm.hostel_id
            WHERE ha.student_id = {student_id}
            """,
            [
                col("hostel_name", "string", "Hostel name"),
                col("room_no", "string", "Room number"),
                col("from_date", "date", "Allocation start"),
                col("to_date", "date", "Allocation end; NULL means current"),
            ],
            [
                (
                    "Which room am I in?",
                    "SELECT hostel_name, room_no FROM my_hostel WHERE to_date IS NULL",
                )
            ],
        ),
        view(
            "my_mess",
            "Your mess allocation per month.",
            [("mess", "self")],
            """
            SELECT m.name AS mess_name, m.type AS mess_type, ma.month
            FROM mess_allocations ma JOIN messes m ON m.id = ma.mess_id
            WHERE ma.student_id = {student_id}
            """,
            [
                col("mess_name", "string", "Mess name"),
                col("mess_type", "string", "Mess type", "veg", "nonveg"),
                col("month", "string", "Month, YYYY-MM"),
            ],
            [
                (
                    "Which mess am I in?",
                    "SELECT mess_name, mess_type FROM my_mess ORDER BY month DESC LIMIT 1",
                )
            ],
        ),
        view(
            "my_complaints",
            "Complaints you filed, with status and tagged summary.",
            [("complaints", "self")],
            """
            SELECT c.id AS complaint_id, c.category, m.name AS mess_name, h.name AS hostel_name,
                   c.text, c.status, DATE(c.created_at) AS created_on,
                   DATE(c.resolved_at) AS resolved_on, ct.sentiment, ct.summary
            FROM complaints c
            LEFT JOIN messes m ON m.id = c.mess_id
            LEFT JOIN hostels h ON h.id = c.hostel_id
            LEFT JOIN complaint_tags ct ON ct.complaint_id = c.id
            WHERE c.student_id = {student_id}
            """,
            _complaint_columns(with_student=False),
            [
                (
                    "What's the status of my complaint?",
                    "SELECT created_on, category, summary, status FROM my_complaints ORDER BY created_on DESC",
                )
            ],
        ),
        view(
            "subjects",
            "Public subject catalogue of the college.",
            [ACADEMICS_SELF, ACADEMICS_COLLEGE],
            """
            SELECT s.code AS subject_code, s.name AS subject_name, d.code AS dept_code, s.semester, s.credits
            FROM subjects s JOIN departments d ON d.id = s.dept_id
            """,
            [SUBJECT_CODE, SUBJECT_NAME, DEPT_CODE, SEMESTER, col("credits", "int", "Credits")],
            [
                (
                    "List CSE 5th semester subjects",
                    "SELECT subject_code, subject_name FROM subjects WHERE dept_code = 'CSE' AND semester = 5",
                )
            ],
        ),
        view(
            "exam_timetable",
            "Public end-semester exam timetable for the current semester.",
            [ACADEMICS_SELF, ACADEMICS_COLLEGE],
            """
            SELECT s.code AS subject_code, s.name AS subject_name, d.code AS dept_code, co.semester,
                   co.section, e.exam_type, e.exam_date
            FROM exams e
            JOIN course_offerings co ON co.id = e.offering_id
            JOIN subjects s ON s.id = co.subject_id
            JOIN departments d ON d.id = co.dept_id
            WHERE co.academic_year = {year}
            """,
            [
                SUBJECT_CODE,
                SUBJECT_NAME,
                DEPT_CODE,
                SEMESTER,
                SECTION,
                col("exam_type", "string", "Exam type", "end_sem"),
                col("exam_date", "date", "Exam date"),
            ],
            [
                (
                    "When is the CSE 5th sem DBMS exam?",
                    "SELECT subject_name, section, exam_date FROM exam_timetable "
                    "WHERE dept_code = 'CSE' AND semester = 5 AND subject_name LIKE '%Database%'",
                )
            ],
        ),
    ]


def _fee_status_columns() -> list[Column]:
    return [
        col("fee_due_id", "int", "Fee due id"),
        STUDENT_ID,
        ROLL_NO,
        STUDENT_NAME,
        DEPT_CODE,
        col("current_semester", "int", "Student's current semester"),
        col("academic_year", "string", "Academic year of the due"),
        SEMESTER,
        col("fee_type", "string", "Fee type", "tuition", "hostel", "mess", "exam"),
        col("amount_due", "decimal", "Amount due in INR"),
        col("paid", "decimal", "Total paid towards this due in INR"),
        col("pending", "decimal", "Amount still pending in INR (0 if fully paid)"),
        col("credit", "decimal", "Overpayment in INR, shown as credit"),
        col("due_date", "date", "Due date, YYYY-MM-DD"),
        col("is_overdue", "boolean (0/1)", "1 if pending > 0 and the due date has passed"),
    ]


def _complaint_columns(with_student: bool) -> list[Column]:
    student_columns = [STUDENT_ID, ROLL_NO, STUDENT_NAME, DEPT_CODE] if with_student else []
    place_ids = [col("mess_id", "int", "Mess id"), col("hostel_id", "int", "Hostel id")]
    return [
        col("complaint_id", "int", "Complaint id"),
        *student_columns,
        col(
            "category", "string", "Complaint category", "mess", "hostel", "infrastructure", "other"
        ),
        *(place_ids if with_student else []),
        col("mess_name", "string", "Mess the complaint is about (NULL if not mess)"),
        col("hostel_name", "string", "Hostel the complaint is about (NULL if not hostel)"),
        col("text", "string", "Complaint text"),
        col("status", "string", "Status", "open", "in_progress", "resolved"),
        col("created_on", "date", "Date filed, YYYY-MM-DD"),
        col("resolved_on", "date", "Date resolved; NULL if not resolved"),
        col("sentiment", "string", "Tagged sentiment", "positive", "neutral", "negative"),
        col("summary", "string", "One-line tagged summary"),
    ]


def _student_row_columns() -> list[Column]:
    return [STUDENT_ID, ROLL_NO, STUDENT_NAME]


def _faculty_views() -> list[LogicalView]:
    own = "x.faculty_id = {faculty_id} AND x.dept_id = {dept_id}"
    student_join = (
        "SELECT x.*, st.roll_no, st.name AS student_name FROM ({base}) x "
        "JOIN students st ON st.id = x.student_id WHERE " + own
    )
    return [
        view(
            "my_classes",
            "Course offerings you teach this semester, with classes held and registered students.",
            [ACADEMICS_CLASSES],
            """
            SELECT co.id AS offering_id, s.code AS subject_code, s.name AS subject_name, co.semester,
                   co.section, co.planned_classes,
                   (SELECT COUNT(*) FROM class_sessions cs WHERE cs.offering_id = co.id) AS held_so_far,
                   (SELECT COUNT(*) FROM registrations r
                     WHERE r.offering_id = co.id AND r.status = 'approved') AS registered_students
            FROM course_offerings co JOIN subjects s ON s.id = co.subject_id
            WHERE co.academic_year = {year} AND co.faculty_id = {faculty_id} AND co.dept_id = {dept_id}
            """,
            [
                OFFERING_ID,
                SUBJECT_CODE,
                SUBJECT_NAME,
                SEMESTER,
                SECTION,
                col("planned_classes", "int", "Classes planned for the semester"),
                col("held_so_far", "int", "Classes held so far"),
                col("registered_students", "int", "Students with approved registration"),
            ],
            [
                (
                    "Which classes do I teach?",
                    "SELECT subject_name, semester, section FROM my_classes",
                )
            ],
        ),
        view(
            "my_class_students",
            "Students registered (approved) in the classes you teach.",
            [ACADEMICS_CLASSES],
            student_join.replace("{base}", REGISTRATION_BASE) + " AND x.status = 'approved'",
            [*_student_row_columns(), OFFERING_ID, SUBJECT_CODE, SUBJECT_NAME, SEMESTER, SECTION],
            [
                (
                    "How many students are in my DBMS class?",
                    "SELECT subject_name, section, COUNT(*) AS students FROM my_class_students "
                    "GROUP BY subject_name, section",
                )
            ],
        ),
        view(
            "my_class_attendance",
            "Attendance of each student in each class you teach.",
            [ACADEMICS_CLASSES],
            student_join.replace("{base}", ATTENDANCE_BASE),
            [*_student_row_columns(), *ATTENDANCE_COLUMNS],
            [
                (
                    "Which students in my OS class are below 75% attendance?",
                    "SELECT roll_no, student_name, attendance_percent FROM my_class_attendance "
                    "WHERE subject_name LIKE '%Operating%' AND attendance_percent < 75 "
                    "ORDER BY attendance_percent",
                )
            ],
        ),
        view(
            "my_class_marks",
            "Internal marks of each student in each class you teach.",
            [ACADEMICS_CLASSES],
            student_join.replace("{base}", MARKS_BASE),
            [*_student_row_columns(), *MARKS_COLUMNS],
            [
                (
                    "Average internal percent in my classes",
                    "SELECT subject_name, section, ROUND(AVG(internal_percent), 2) AS avg_internal "
                    "FROM my_class_marks GROUP BY subject_name, section",
                )
            ],
        ),
        view(
            "my_class_attendance_weekly",
            "Week-by-week attendance percentage for each class you teach.",
            [ACADEMICS_CLASSES],
            _wrap(WEEKLY_BASE, "x", own),
            WEEKLY_COLUMNS,
            [
                (
                    "Weekly attendance trend of my classes",
                    "SELECT week_start, subject_name, attendance_percent FROM my_class_attendance_weekly "
                    "ORDER BY week_start",
                )
            ],
        ),
        view(
            "my_class_feedback",
            "Anonymous student feedback on your classes, with tagged sentiment and summary.",
            [("teaching_feedback", "own_classes")],
            _wrap(
                FEEDBACK_BASE,
                "x",
                "x.faculty_id = {faculty_id} AND x.dept_code = "
                "(SELECT code FROM departments WHERE id = {dept_id})",
            ),
            FEEDBACK_COLUMNS,
            [
                (
                    "Sentiment of feedback on my classes",
                    "SELECT sentiment, COUNT(*) AS comments FROM my_class_feedback GROUP BY sentiment",
                )
            ],
        ),
        view(
            "my_class_feedback_themes",
            "Themes tagged on anonymous feedback about your classes (one row per theme).",
            [("teaching_feedback", "own_classes")],
            _wrap(
                FEEDBACK_THEMES_BASE,
                "x",
                "x.faculty_id = {faculty_id} AND x.dept_code = "
                "(SELECT code FROM departments WHERE id = {dept_id})",
            ),
            FEEDBACK_THEME_COLUMNS,
            [
                (
                    "What did students say about my teaching?",
                    "SELECT theme, COUNT(*) AS mentions FROM my_class_feedback_themes "
                    "GROUP BY theme ORDER BY mentions DESC",
                )
            ],
        ),
    ]


def _advisor_views() -> list[LogicalView]:
    advisee = (
        "x.student_id IN (SELECT id FROM students WHERE advisor_id = {faculty_id} "
        "AND dept_id = {dept_id})"
    )
    with_student = (
        "SELECT x.*, st.roll_no, st.name AS student_name FROM ({base}) x "
        "JOIN students st ON st.id = x.student_id WHERE " + advisee
    )
    return [
        view(
            "my_advisees",
            "Students you advise, with their latest CGPA and total backlogs.",
            [ACADEMICS_ADVISEES],
            """
            SELECT st.id AS student_id, st.roll_no, st.name AS student_name, st.current_semester,
                   st.section, lr.cgpa AS latest_cgpa, lr.sgpa AS latest_sgpa,
                   COALESCE(lr.total_backlogs, 0) AS total_backlogs
            FROM students st
            LEFT JOIN (
              SELECT r.student_id, r.cgpa, r.sgpa,
                     (SELECT SUM(r2.backlogs) FROM results r2 WHERE r2.student_id = r.student_id)
                       AS total_backlogs
              FROM results r
              WHERE r.semester = (SELECT MAX(r3.semester) FROM results r3
                                  WHERE r3.student_id = r.student_id)
            ) lr ON lr.student_id = st.id
            WHERE st.advisor_id = {faculty_id} AND st.dept_id = {dept_id}
            """,
            [
                *_student_row_columns(),
                col("current_semester", "int", "Current semester"),
                SECTION,
                col("latest_cgpa", "decimal", "CGPA after the latest completed semester"),
                col("latest_sgpa", "decimal", "SGPA of the latest completed semester"),
                col("total_backlogs", "int", "Total backlogs across all semesters"),
            ],
            [
                (
                    "Which of my advisees have a backlog?",
                    "SELECT roll_no, student_name, total_backlogs FROM my_advisees WHERE total_backlogs > 0",
                )
            ],
        ),
        view(
            "advisee_registrations",
            "Current-semester subject registrations of your advisees.",
            [ACADEMICS_ADVISEES],
            with_student.replace("{base}", REGISTRATION_BASE),
            [*_student_row_columns(), *REGISTRATION_COLUMNS],
            [
                (
                    "Pending registrations of my advisees",
                    "SELECT roll_no, student_name, subject_name FROM advisee_registrations "
                    "WHERE status = 'pending'",
                )
            ],
        ),
        view(
            "advisee_attendance",
            "Per-subject attendance of your advisees this semester.",
            [ACADEMICS_ADVISEES],
            with_student.replace("{base}", ATTENDANCE_BASE),
            [*_student_row_columns(), *ATTENDANCE_COLUMNS],
            [
                (
                    "Advisees below 75% in any subject",
                    "SELECT DISTINCT roll_no, student_name FROM advisee_attendance "
                    "WHERE attendance_percent < 75",
                )
            ],
        ),
        view(
            "advisee_marks",
            "Internal marks of your advisees this semester.",
            [ACADEMICS_ADVISEES],
            with_student.replace("{base}", MARKS_BASE),
            [*_student_row_columns(), *MARKS_COLUMNS],
            [
                (
                    "Advisees failing internals",
                    "SELECT roll_no, student_name, subject_name, internal_percent FROM advisee_marks "
                    "WHERE internal_pass = 0",
                )
            ],
        ),
        view(
            "advisee_results",
            "Semester results (SGPA, CGPA, backlogs) of your advisees.",
            [ACADEMICS_ADVISEES],
            _wrap(RESULTS_BASE, "x", advisee),
            RESULT_COLUMNS,
            [
                (
                    "SGPA trend of my advisees",
                    "SELECT semester, ROUND(AVG(sgpa), 2) AS avg_sgpa FROM advisee_results "
                    "GROUP BY semester ORDER BY semester",
                )
            ],
        ),
    ]


def _department_views() -> list[LogicalView]:
    in_dept = "x.dept_id = {dept_id}"
    with_student = (
        "SELECT x.*, st.roll_no, st.name AS student_name FROM ({base}) x "
        "JOIN students st ON st.id = x.student_id WHERE " + in_dept
    )
    return [
        view(
            "dept_students",
            "Students of your department.",
            [ACADEMICS_DEPARTMENT],
            STUDENT_BASE + " WHERE st.dept_id = {dept_id}",
            _student_columns(),
            [
                (
                    "How many students per semester in my department?",
                    "SELECT current_semester, COUNT(*) AS students FROM dept_students "
                    "GROUP BY current_semester ORDER BY current_semester",
                )
            ],
        ),
        view(
            "dept_faculty",
            "Faculty members of your department.",
            [ACADEMICS_DEPARTMENT],
            _faculty_template() + " WHERE f.dept_id = {dept_id}",
            _faculty_columns(),
            [
                (
                    "List advisors in my department",
                    "SELECT faculty_name, designation FROM dept_faculty WHERE is_advisor = 1",
                )
            ],
        ),
        view(
            "dept_offerings",
            "Course offerings of your department this semester.",
            [ACADEMICS_DEPARTMENT],
            _offering_template() + " AND co.dept_id = {dept_id}",
            _offering_columns(),
            [
                (
                    "Who teaches DBMS?",
                    "SELECT subject_name, section, faculty_name FROM dept_offerings "
                    "WHERE subject_name LIKE '%Database%'",
                )
            ],
        ),
        view(
            "dept_registrations",
            "Current-semester registrations of students in your department.",
            [ACADEMICS_DEPARTMENT],
            with_student.replace("{base}", REGISTRATION_BASE),
            [*_student_row_columns(), *REGISTRATION_COLUMNS],
            [
                (
                    "Pending registrations by subject",
                    "SELECT subject_name, COUNT(*) AS pending FROM dept_registrations "
                    "WHERE status = 'pending' GROUP BY subject_name",
                )
            ],
        ),
        view(
            "dept_attendance",
            "Per-student per-subject attendance in your department this semester.",
            [ACADEMICS_DEPARTMENT],
            with_student.replace("{base}", ATTENDANCE_BASE),
            [*_student_row_columns(), *ATTENDANCE_COLUMNS],
            [
                (
                    "Average attendance by subject",
                    "SELECT subject_name, section, ROUND(AVG(attendance_percent), 2) AS avg_attendance "
                    "FROM dept_attendance GROUP BY subject_name, section",
                )
            ],
        ),
        view(
            "dept_attendance_weekly",
            "Week-by-week attendance per class in your department.",
            [ACADEMICS_DEPARTMENT],
            _wrap(WEEKLY_BASE, "x", in_dept),
            WEEKLY_COLUMNS,
            [
                (
                    "Weekly attendance of 3rd sem section B",
                    "SELECT week_start, ROUND(AVG(attendance_percent), 2) AS attendance_percent "
                    "FROM dept_attendance_weekly WHERE semester = 3 AND section = 'B' "
                    "GROUP BY week_start ORDER BY week_start",
                )
            ],
        ),
        view(
            "dept_marks",
            "Internal marks per student per subject in your department this semester.",
            [ACADEMICS_DEPARTMENT],
            with_student.replace("{base}", MARKS_BASE),
            [*_student_row_columns(), *MARKS_COLUMNS],
            [
                (
                    "Subject-wise pass percentage in my department this semester",
                    "SELECT subject_name, ROUND(AVG(internal_pass) * 100, 2) AS pass_percent "
                    "FROM dept_marks GROUP BY subject_name ORDER BY pass_percent",
                )
            ],
        ),
        view(
            "dept_results",
            "Semester results of students in your department.",
            [ACADEMICS_DEPARTMENT],
            RESULTS_BASE + " WHERE st.dept_id = {dept_id}",
            RESULT_COLUMNS,
            [
                (
                    "Average SGPA by semester",
                    "SELECT semester, ROUND(AVG(sgpa), 2) AS avg_sgpa FROM dept_results "
                    "GROUP BY semester ORDER BY semester",
                )
            ],
        ),
        view(
            "dept_feedback",
            "Anonymous teaching feedback for your department, with tagged sentiment.",
            [("teaching_feedback", "department")],
            FEEDBACK_BASE + " WHERE fb.dept_id = {dept_id}",
            FEEDBACK_COLUMNS,
            [
                (
                    "Average rating per faculty",
                    "SELECT faculty_name, ROUND(AVG(rating), 2) AS avg_rating FROM dept_feedback "
                    "GROUP BY faculty_name ORDER BY avg_rating",
                )
            ],
        ),
        view(
            "dept_feedback_themes",
            "Themes tagged on teaching feedback in your department (one row per theme).",
            [("teaching_feedback", "department")],
            FEEDBACK_THEMES_BASE + " WHERE fb.dept_id = {dept_id}",
            FEEDBACK_THEME_COLUMNS,
            [
                (
                    "Most common feedback themes",
                    "SELECT theme, COUNT(*) AS mentions FROM dept_feedback_themes GROUP BY theme "
                    "ORDER BY mentions DESC",
                )
            ],
        ),
    ]


def _student_columns() -> list[Column]:
    return [
        *_student_row_columns(),
        col("gender", "string", "Gender", "M", "F"),
        DEPT_CODE,
        col("admission_year", "int", "Year of admission"),
        col("current_semester", "int", "Current semester"),
        SECTION,
        col("advisor_name", "string", "Faculty advisor name"),
    ]


def _faculty_template() -> str:
    return """
    SELECT f.id AS faculty_id, f.name AS faculty_name, d.code AS dept_code, f.designation,
           f.is_advisor, f.is_hod
    FROM faculty f JOIN departments d ON d.id = f.dept_id
    """


def _faculty_columns() -> list[Column]:
    return [
        FACULTY_ID,
        FACULTY_NAME,
        DEPT_CODE,
        col(
            "designation",
            "string",
            "Designation",
            "Professor",
            "Associate Professor",
            "Assistant Professor",
        ),
        col("is_advisor", "boolean (0/1)", "1 if a faculty advisor"),
        col("is_hod", "boolean (0/1)", "1 if head of department"),
    ]


def _offering_template() -> str:
    return """
    SELECT co.id AS offering_id, s.code AS subject_code, s.name AS subject_name, d.code AS dept_code,
           co.semester, co.section, co.faculty_id, f.name AS faculty_name, co.planned_classes
    FROM course_offerings co
    JOIN subjects s ON s.id = co.subject_id
    JOIN faculty f ON f.id = co.faculty_id
    JOIN departments d ON d.id = co.dept_id
    WHERE co.academic_year = {year}
    """


def _offering_columns() -> list[Column]:
    return [
        OFFERING_ID,
        SUBJECT_CODE,
        SUBJECT_NAME,
        DEPT_CODE,
        SEMESTER,
        SECTION,
        FACULTY_ID,
        FACULTY_NAME,
        col("planned_classes", "int", "Classes planned for the semester"),
    ]


def _college_views() -> list[LogicalView]:
    with_student_dept = (
        "SELECT x.*, st.roll_no, st.name AS student_name, d.code AS dept_code FROM ({base}) x "
        "JOIN students st ON st.id = x.student_id JOIN departments d ON d.id = x.dept_id"
    )
    return [
        view(
            "students",
            "All students of the college.",
            [ACADEMICS_COLLEGE],
            STUDENT_BASE,
            _student_columns(),
            [
                (
                    "Students per department",
                    "SELECT dept_code, COUNT(*) AS students FROM students GROUP BY dept_code",
                )
            ],
        ),
        view(
            "faculty",
            "All faculty of the college.",
            [ACADEMICS_COLLEGE],
            _faculty_template(),
            _faculty_columns(),
            [
                (
                    "Faculty count per department",
                    "SELECT dept_code, COUNT(*) AS faculty FROM faculty GROUP BY dept_code",
                )
            ],
        ),
        view(
            "departments",
            "Departments of the college.",
            [ACADEMICS_COLLEGE],
            "SELECT d.code AS dept_code, d.name AS dept_name FROM departments d",
            [DEPT_CODE, col("dept_name", "string", "Department name")],
            [("List departments", "SELECT dept_code, dept_name FROM departments")],
        ),
        view(
            "course_offerings",
            "All course offerings this semester.",
            [ACADEMICS_COLLEGE],
            _offering_template(),
            _offering_columns(),
            [
                (
                    "Offerings per department",
                    "SELECT dept_code, COUNT(*) AS offerings FROM course_offerings GROUP BY dept_code",
                )
            ],
        ),
        view(
            "registrations",
            "All current-semester registrations.",
            [ACADEMICS_COLLEGE],
            with_student_dept.replace("{base}", REGISTRATION_BASE),
            [*_student_row_columns(), DEPT_CODE, *REGISTRATION_COLUMNS],
            [
                (
                    "Pending registrations per department",
                    "SELECT dept_code, COUNT(*) AS pending FROM registrations WHERE status = 'pending' "
                    "GROUP BY dept_code",
                )
            ],
        ),
        view(
            "attendance_summary",
            "Per-student per-subject attendance this semester, college-wide.",
            [ACADEMICS_COLLEGE],
            with_student_dept.replace("{base}", ATTENDANCE_BASE),
            [*_student_row_columns(), DEPT_CODE, *ATTENDANCE_COLUMNS],
            [
                (
                    "Average attendance per department",
                    "SELECT dept_code, ROUND(AVG(attendance_percent), 2) AS avg_attendance "
                    "FROM attendance_summary GROUP BY dept_code",
                )
            ],
        ),
        view(
            "attendance_weekly",
            "Week-by-week attendance per class, college-wide.",
            [ACADEMICS_COLLEGE],
            WEEKLY_BASE,
            WEEKLY_COLUMNS,
            [
                (
                    "Weekly attendance of ECE 3rd sem section B",
                    "SELECT week_start, ROUND(AVG(attendance_percent), 2) AS attendance_percent "
                    "FROM attendance_weekly WHERE dept_code = 'ECE' AND semester = 3 AND section = 'B' "
                    "GROUP BY week_start ORDER BY week_start",
                )
            ],
        ),
        view(
            "marks",
            "Internal marks per student per subject this semester, college-wide.",
            [ACADEMICS_COLLEGE],
            with_student_dept.replace("{base}", MARKS_BASE),
            [*_student_row_columns(), DEPT_CODE, *MARKS_COLUMNS],
            [
                (
                    "Compare pass percentage across all departments",
                    "SELECT dept_code, ROUND(AVG(internal_pass) * 100, 2) AS pass_percent FROM marks "
                    "GROUP BY dept_code ORDER BY dept_code",
                )
            ],
        ),
        view(
            "results",
            "Semester results of all students.",
            [ACADEMICS_COLLEGE],
            RESULTS_BASE,
            RESULT_COLUMNS,
            [
                (
                    "Average SGPA per department in the last completed semester",
                    "SELECT dept_code, ROUND(AVG(sgpa), 2) AS avg_sgpa FROM results "
                    "WHERE academic_year = '2025-26' GROUP BY dept_code",
                )
            ],
        ),
        view(
            "feedback",
            "Anonymous teaching feedback, college-wide, with tagged sentiment.",
            [("teaching_feedback", "college")],
            FEEDBACK_BASE,
            FEEDBACK_COLUMNS,
            [
                (
                    "Average rating per department",
                    "SELECT dept_code, ROUND(AVG(rating), 2) AS avg_rating FROM feedback "
                    "GROUP BY dept_code",
                )
            ],
        ),
        view(
            "feedback_themes",
            "Themes tagged on teaching feedback, college-wide.",
            [("teaching_feedback", "college")],
            FEEDBACK_THEMES_BASE,
            FEEDBACK_THEME_COLUMNS,
            [
                (
                    "Top feedback themes per department",
                    "SELECT dept_code, theme, COUNT(*) AS mentions FROM feedback_themes "
                    "GROUP BY dept_code, theme ORDER BY mentions DESC",
                )
            ],
        ),
        view(
            "fee_dues",
            "All fee dues raised to students.",
            [("fees", "college")],
            """
             SELECT fd.id AS fee_due_id, fd.student_id, d.code AS dept_code, fd.academic_year,
                    fd.semester, fd.fee_type, fd.amount_due, fd.due_date
             FROM fee_dues fd JOIN students st ON st.id = fd.student_id
             JOIN departments d ON d.id = st.dept_id
             """,
            [
                col("fee_due_id", "int", "Fee due id"),
                STUDENT_ID,
                DEPT_CODE,
                col("academic_year", "string", "Academic year"),
                SEMESTER,
                col("fee_type", "string", "Fee type", "tuition", "hostel", "mess", "exam"),
                col("amount_due", "decimal", "Amount due in INR"),
                col("due_date", "date", "Due date"),
            ],
            [
                (
                    "Total fees raised per type",
                    "SELECT fee_type, SUM(amount_due) AS total FROM fee_dues GROUP BY fee_type",
                )
            ],
        ),
        view(
            "fee_payments",
            "All fee payments.",
            [("fees", "college")],
            """
             SELECT p.id AS payment_id, p.fee_due_id, fd.student_id, fd.fee_type, p.amount_paid,
                    p.paid_on, p.mode
             FROM fee_payments p JOIN fee_dues fd ON fd.id = p.fee_due_id
             """,
            [
                col("payment_id", "int", "Payment id"),
                col("fee_due_id", "int", "Fee due id"),
                STUDENT_ID,
                col("fee_type", "string", "Fee type", "tuition", "hostel", "mess", "exam"),
                col("amount_paid", "decimal", "Amount paid in INR"),
                col("paid_on", "date", "Paid on"),
                col("mode", "string", "Payment mode", "upi", "netbanking", "card", "cash"),
            ],
            [
                (
                    "Monthly fee collection",
                    "SELECT DATE_FORMAT(paid_on, '%Y-%m') AS month, SUM(amount_paid) AS collected "
                    "FROM fee_payments GROUP BY month ORDER BY month",
                )
            ],
        ),
        view(
            "fee_status",
            "Per student per fee due: paid, pending amount and overdue flag.",
            [("fees", "college")],
            FEE_STATUS_BASE,
            _fee_status_columns(),
            [
                (
                    "Department-wise pending fees",
                    "SELECT dept_code, SUM(pending) AS total_pending FROM fee_status "
                    "GROUP BY dept_code ORDER BY total_pending DESC",
                )
            ],
        ),
    ]


def _admin_views() -> list[LogicalView]:
    return [
        view(
            "hostels",
            "Hostels with gender and capacity.",
            [("hostel", "college")],
            "SELECT h.id AS hostel_id, h.name AS hostel_name, h.gender, h.capacity FROM hostels h",
            [
                col("hostel_id", "int", "Hostel id"),
                col("hostel_name", "string", "Hostel name"),
                col("gender", "string", "Residents' gender", "M", "F"),
                col("capacity", "int", "Number of beds"),
            ],
            [("List hostels", "SELECT hostel_name, capacity FROM hostels")],
        ),
        view(
            "rooms",
            "Hostel rooms.",
            [("hostel", "college")],
            """
             SELECT rm.id AS room_id, rm.hostel_id, h.name AS hostel_name, rm.room_no, rm.capacity
             FROM rooms rm JOIN hostels h ON h.id = rm.hostel_id
             """,
            [
                col("room_id", "int", "Room id"),
                col("hostel_id", "int", "Hostel id"),
                col("hostel_name", "string", "Hostel name"),
                col("room_no", "string", "Room number"),
                col("capacity", "int", "Beds in the room"),
            ],
            [
                (
                    "Rooms per hostel",
                    "SELECT hostel_name, COUNT(*) AS rooms FROM rooms GROUP BY hostel_name",
                )
            ],
        ),
        view(
            "hostel_allocations",
            "Which student lives in which hostel room.",
            [("hostel", "college")],
            """
             SELECT ha.student_id, st.roll_no, st.name AS student_name, d.code AS dept_code,
                    rm.hostel_id, h.name AS hostel_name, rm.room_no, ha.from_date, ha.to_date,
                    (ha.to_date IS NULL) AS is_current
             FROM hostel_allocations ha
             JOIN students st ON st.id = ha.student_id
             JOIN departments d ON d.id = st.dept_id
             JOIN rooms rm ON rm.id = ha.room_id
             JOIN hostels h ON h.id = rm.hostel_id
             """,
            [
                STUDENT_ID,
                ROLL_NO,
                STUDENT_NAME,
                DEPT_CODE,
                col("hostel_id", "int", "Hostel id"),
                col("hostel_name", "string", "Hostel name"),
                col("room_no", "string", "Room number"),
                col("from_date", "date", "Allocation start"),
                col("to_date", "date", "Allocation end; NULL if current"),
                col("is_current", "boolean (0/1)", "1 for the current allocation"),
            ],
            [
                (
                    "Hostel-wise fee defaulters",
                    "SELECT h.hostel_name, COUNT(DISTINCT f.student_id) AS defaulters "
                    "FROM fee_status f JOIN hostel_allocations h ON h.student_id = f.student_id "
                    "WHERE h.is_current = 1 AND f.is_overdue = 1 GROUP BY h.hostel_name "
                    "ORDER BY defaulters DESC",
                )
            ],
        ),
        view(
            "student_residence",
            "Every student with hosteller/day-scholar status and current hostel.",
            [("hostel", "college")],
            """
             SELECT st.id AS student_id, st.roll_no, d.code AS dept_code, st.is_hosteller,
                    h.name AS hostel_name
             FROM students st
             JOIN departments d ON d.id = st.dept_id
             LEFT JOIN hostel_allocations ha ON ha.student_id = st.id AND ha.to_date IS NULL
             LEFT JOIN rooms rm ON rm.id = ha.room_id
             LEFT JOIN hostels h ON h.id = rm.hostel_id
             """,
            [
                STUDENT_ID,
                ROLL_NO,
                DEPT_CODE,
                col("is_hosteller", "boolean (0/1)", "1 = hosteller, 0 = day scholar"),
                col("hostel_name", "string", "Current hostel; NULL for day scholars"),
            ],
            [
                (
                    "Compare average SGPA of hostellers vs day scholars by department",
                    "SELECT r.dept_code, ROUND(AVG(CASE WHEN s.is_hosteller = 1 THEN r.sgpa END), 2) "
                    "AS hosteller_avg_sgpa, ROUND(AVG(CASE WHEN s.is_hosteller = 0 THEN r.sgpa END), 2) "
                    "AS day_scholar_avg_sgpa FROM results r JOIN student_residence s "
                    "ON s.student_id = r.student_id GROUP BY r.dept_code",
                )
            ],
        ),
        view(
            "messes",
            "Messes and their type.",
            [("mess", "college")],
            "SELECT m.id AS mess_id, m.name AS mess_name, m.type AS mess_type FROM messes m",
            [
                col("mess_id", "int", "Mess id"),
                col("mess_name", "string", "Mess name"),
                col("mess_type", "string", "Mess type", "veg", "nonveg"),
            ],
            [("List messes", "SELECT mess_name, mess_type FROM messes")],
        ),
        view(
            "mess_allocations",
            "Monthly mess allocation per student.",
            [("mess", "college")],
            """
             SELECT ma.student_id, ma.mess_id, m.name AS mess_name, ma.month
             FROM mess_allocations ma JOIN messes m ON m.id = ma.mess_id
             """,
            [
                STUDENT_ID,
                col("mess_id", "int", "Mess id"),
                col("mess_name", "string", "Mess name"),
                col("month", "string", "Month, YYYY-MM"),
            ],
            [
                (
                    "Students per mess this month",
                    "SELECT mess_name, COUNT(*) AS students FROM mess_allocations WHERE month = '2026-11' "
                    "GROUP BY mess_name",
                )
            ],
        ),
        view(
            "mess_change_requests",
            "Requests to change mess.",
            [("mess", "college")],
            """
             SELECT r.id AS request_id, r.student_id, fm.name AS from_mess, tm.name AS to_mess,
                    r.status, DATE(r.requested_at) AS requested_on
             FROM mess_change_requests r
             JOIN messes fm ON fm.id = r.from_mess_id JOIN messes tm ON tm.id = r.to_mess_id
             """,
            [
                col("request_id", "int", "Request id"),
                STUDENT_ID,
                col("from_mess", "string", "Current mess"),
                col("to_mess", "string", "Requested mess"),
                col("status", "string", "Status", "pending", "approved", "rejected"),
                col("requested_on", "date", "Date requested"),
            ],
            [
                (
                    "Most requested mess",
                    "SELECT to_mess, COUNT(*) AS requests FROM mess_change_requests GROUP BY to_mess",
                )
            ],
        ),
        view(
            "complaints",
            "All complaints with student details, status and tagged summary.",
            [("complaints", "college")],
            COMPLAINTS_BASE,
            _complaint_columns(with_student=True),
            [
                (
                    "Open complaints per category",
                    "SELECT category, COUNT(*) AS open_complaints FROM complaints "
                    "WHERE status <> 'resolved' GROUP BY category",
                )
            ],
        ),
        view(
            "complaint_themes",
            "Themes tagged on complaints (one row per theme).",
            [("complaints", "college")],
            """
             SELECT th.complaint_id, th.theme, c.category, m.name AS mess_name, h.name AS hostel_name,
                    DATE(c.created_at) AS created_on
             FROM complaint_themes th
             JOIN complaints c ON c.id = th.complaint_id
             LEFT JOIN messes m ON m.id = c.mess_id
             LEFT JOIN hostels h ON h.id = c.hostel_id
             """,
            [
                col("complaint_id", "int", "Complaint id (join to complaints)"),
                col("theme", "string", "One theme of the complaint", *COMPLAINT_THEMES),
                col("category", "string", "Category", "mess", "hostel", "infrastructure", "other"),
                col("mess_name", "string", "Mess name or NULL"),
                col("hostel_name", "string", "Hostel name or NULL"),
                col("created_on", "date", "Date filed, YYYY-MM-DD"),
            ],
            [
                (
                    "Which mess got the most hygiene complaints this month?",
                    "SELECT mess_name, COUNT(*) AS hygiene_complaints FROM complaint_themes "
                    "WHERE theme = 'hygiene' AND mess_name IS NOT NULL "
                    "AND created_on >= '2026-11-01' AND created_on < '2026-12-01' "
                    "GROUP BY mess_name ORDER BY hygiene_complaints DESC",
                )
            ],
        ),
    ]


RECURRING_FEEDBACK = """
SELECT x.offering_id, x.subject_code, x.faculty_name, x.dept_code, x.theme,
       COUNT(DISTINCT YEARWEEK(x.submitted_on, 1)) AS weeks, COUNT(*) AS mentions,
       MIN(x.submitted_on) AS first_seen, MAX(x.submitted_on) AS last_seen
FROM ({base}) x
WHERE x.theme <> 'other'
GROUP BY x.offering_id, x.subject_code, x.faculty_name, x.dept_code, x.theme
HAVING COUNT(DISTINCT YEARWEEK(x.submitted_on, 1)) >= 3
"""

RECURRING_COLUMNS = [
    OFFERING_ID,
    SUBJECT_CODE,
    FACULTY_NAME,
    DEPT_CODE,
    col("theme", "string", "Recurring feedback theme", *TEACHING_THEMES),
    col("weeks", "int", "Number of different weeks the theme appeared (>= 3)"),
    col("mentions", "int", "Total comments with this theme"),
    col("first_seen", "date", "First comment date"),
    col("last_seen", "date", "Latest comment date"),
]


def _recurring_views() -> list[LogicalView]:
    own = FEEDBACK_THEMES_BASE + (" WHERE fb.faculty_id = {faculty_id} AND fb.dept_id = {dept_id}")
    dept = FEEDBACK_THEMES_BASE + " WHERE fb.dept_id = {dept_id}"
    example = "SELECT subject_code, theme, weeks, mentions FROM {name} ORDER BY weeks DESC"
    specs = [
        ("my_class_recurring_issues", "your classes", ("teaching_feedback", "own_classes"), own),
        ("dept_recurring_issues", "your department", ("teaching_feedback", "department"), dept),
        (
            "recurring_feedback_issues",
            "the college",
            ("teaching_feedback", "college"),
            FEEDBACK_THEMES_BASE,
        ),
    ]
    views = [
        view(
            name,
            f"Feedback themes that recur in at least 3 different weeks for the same class in {label}.",
            [grant],
            RECURRING_FEEDBACK.replace("{base}", base),
            RECURRING_COLUMNS,
            [("Recurring issues in feedback", example.format(name=name))],
        )
        for name, label, grant, base in specs
    ]
    views.append(
        view(
            "recurring_complaint_issues",
            "Complaint themes that recur in at least 3 different weeks for the same mess or hostel.",
            [("complaints", "college")],
            """
            SELECT COALESCE(m.name, h.name) AS target, c.category, th.theme,
                   COUNT(DISTINCT YEARWEEK(c.created_at, 1)) AS weeks, COUNT(*) AS complaints,
                   DATE(MIN(c.created_at)) AS first_seen, DATE(MAX(c.created_at)) AS last_seen
            FROM complaint_themes th
            JOIN complaints c ON c.id = th.complaint_id
            LEFT JOIN messes m ON m.id = c.mess_id
            LEFT JOIN hostels h ON h.id = c.hostel_id
            WHERE COALESCE(m.name, h.name) IS NOT NULL AND th.theme <> 'other'
            GROUP BY COALESCE(m.name, h.name), c.category, th.theme
            HAVING COUNT(DISTINCT YEARWEEK(c.created_at, 1)) >= 3
            """,
            [
                col("target", "string", "Mess or hostel name"),
                col("category", "string", "Category", "mess", "hostel"),
                col("theme", "string", "Recurring complaint theme", *COMPLAINT_THEMES),
                col("weeks", "int", "Number of different weeks the theme appeared (>= 3)"),
                col("complaints", "int", "Total complaints with this theme"),
                col("first_seen", "date", "First complaint date"),
                col("last_seen", "date", "Latest complaint date"),
            ],
            [
                (
                    "Recurring mess problems",
                    "SELECT target, theme, weeks, complaints FROM recurring_complaint_issues "
                    "WHERE category = 'mess' ORDER BY weeks DESC",
                )
            ],
        )
    )
    return views


@cache
def all_views() -> dict[str, LogicalView]:
    views = (
        _student_views()
        + _faculty_views()
        + _advisor_views()
        + _department_views()
        + _college_views()
        + _admin_views()
        + _recurring_views()
    )
    registry = {item.name: item for item in views}
    assert len(registry) == len(views), "duplicate view name"
    return registry
