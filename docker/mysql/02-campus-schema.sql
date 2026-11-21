USE campus;

CREATE TABLE departments (
  id INT PRIMARY KEY,
  code VARCHAR(8) NOT NULL UNIQUE,
  name VARCHAR(100) NOT NULL
);

CREATE TABLE faculty (
  id INT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  dept_id INT NOT NULL,
  designation VARCHAR(50) NOT NULL,
  is_advisor BOOLEAN NOT NULL DEFAULT FALSE,
  is_hod BOOLEAN NOT NULL DEFAULT FALSE,
  INDEX idx_faculty_dept (dept_id),
  FOREIGN KEY (dept_id) REFERENCES departments(id)
);

CREATE TABLE students (
  id INT PRIMARY KEY,
  roll_no VARCHAR(16) NOT NULL UNIQUE,
  name VARCHAR(100) NOT NULL,
  gender CHAR(1) NOT NULL,
  dept_id INT NOT NULL,
  admission_year INT NOT NULL,
  current_semester INT NOT NULL,
  section CHAR(1) NOT NULL,
  advisor_id INT NULL,
  is_hosteller BOOLEAN NOT NULL,
  INDEX idx_students_dept (dept_id),
  INDEX idx_students_advisor (advisor_id),
  INDEX idx_students_sem (dept_id, current_semester, section),
  FOREIGN KEY (dept_id) REFERENCES departments(id),
  FOREIGN KEY (advisor_id) REFERENCES faculty(id)
);

CREATE TABLE subjects (
  id INT PRIMARY KEY,
  code VARCHAR(16) NOT NULL UNIQUE,
  name VARCHAR(120) NOT NULL,
  dept_id INT NOT NULL,
  semester INT NOT NULL,
  credits INT NOT NULL,
  INDEX idx_subjects_dept (dept_id, semester),
  FOREIGN KEY (dept_id) REFERENCES departments(id)
);

CREATE TABLE course_offerings (
  id INT PRIMARY KEY,
  subject_id INT NOT NULL,
  faculty_id INT NOT NULL,
  dept_id INT NOT NULL,
  academic_year VARCHAR(9) NOT NULL,
  semester INT NOT NULL,
  section CHAR(1) NOT NULL,
  planned_classes INT NOT NULL,
  INDEX idx_offerings_subject (subject_id),
  INDEX idx_offerings_faculty (faculty_id),
  INDEX idx_offerings_dept (dept_id, academic_year, semester),
  FOREIGN KEY (subject_id) REFERENCES subjects(id),
  FOREIGN KEY (faculty_id) REFERENCES faculty(id),
  FOREIGN KEY (dept_id) REFERENCES departments(id)
);

CREATE TABLE registrations (
  id INT PRIMARY KEY,
  student_id INT NOT NULL,
  offering_id INT NOT NULL,
  status VARCHAR(10) NOT NULL,
  approved_by INT NULL,
  requested_at DATETIME NOT NULL,
  decided_at DATETIME NULL,
  INDEX idx_reg_student (student_id),
  INDEX idx_reg_offering (offering_id),
  INDEX idx_reg_status (status),
  FOREIGN KEY (student_id) REFERENCES students(id),
  FOREIGN KEY (offering_id) REFERENCES course_offerings(id),
  FOREIGN KEY (approved_by) REFERENCES faculty(id)
);

CREATE TABLE class_sessions (
  id INT PRIMARY KEY,
  offering_id INT NOT NULL,
  held_on DATE NOT NULL,
  INDEX idx_sessions_offering (offering_id, held_on),
  FOREIGN KEY (offering_id) REFERENCES course_offerings(id)
);

CREATE TABLE attendance (
  session_id INT NOT NULL,
  student_id INT NOT NULL,
  present BOOLEAN NOT NULL,
  PRIMARY KEY (session_id, student_id),
  INDEX idx_attendance_student (student_id),
  FOREIGN KEY (session_id) REFERENCES class_sessions(id),
  FOREIGN KEY (student_id) REFERENCES students(id)
);

CREATE TABLE attendance_summary (
  student_id INT NOT NULL,
  offering_id INT NOT NULL,
  held INT NOT NULL,
  attended INT NOT NULL,
  PRIMARY KEY (student_id, offering_id),
  INDEX idx_attsum_offering (offering_id),
  FOREIGN KEY (student_id) REFERENCES students(id),
  FOREIGN KEY (offering_id) REFERENCES course_offerings(id)
);

CREATE TABLE marks (
  student_id INT NOT NULL,
  offering_id INT NOT NULL,
  component VARCHAR(12) NOT NULL,
  max_marks DECIMAL(6,2) NOT NULL,
  marks_obtained DECIMAL(6,2) NULL,
  PRIMARY KEY (student_id, offering_id, component),
  INDEX idx_marks_offering (offering_id),
  FOREIGN KEY (student_id) REFERENCES students(id),
  FOREIGN KEY (offering_id) REFERENCES course_offerings(id)
);

CREATE TABLE results (
  student_id INT NOT NULL,
  academic_year VARCHAR(9) NOT NULL,
  semester INT NOT NULL,
  sgpa DECIMAL(4,2) NOT NULL,
  cgpa DECIMAL(4,2) NOT NULL,
  backlogs INT NOT NULL,
  result_status VARCHAR(10) NOT NULL,
  PRIMARY KEY (student_id, semester),
  INDEX idx_results_year (academic_year, semester),
  FOREIGN KEY (student_id) REFERENCES students(id)
);

CREATE TABLE fee_dues (
  id INT PRIMARY KEY,
  student_id INT NOT NULL,
  academic_year VARCHAR(9) NOT NULL,
  semester INT NOT NULL,
  fee_type VARCHAR(10) NOT NULL,
  amount_due DECIMAL(10,2) NOT NULL,
  due_date DATE NOT NULL,
  INDEX idx_fee_dues_student (student_id),
  INDEX idx_fee_dues_date (due_date),
  FOREIGN KEY (student_id) REFERENCES students(id)
);

CREATE TABLE fee_payments (
  id INT PRIMARY KEY,
  fee_due_id INT NOT NULL,
  amount_paid DECIMAL(10,2) NOT NULL,
  paid_on DATE NOT NULL,
  mode VARCHAR(12) NOT NULL,
  INDEX idx_fee_payments_due (fee_due_id),
  INDEX idx_fee_payments_date (paid_on),
  FOREIGN KEY (fee_due_id) REFERENCES fee_dues(id)
);

CREATE TABLE exams (
  id INT PRIMARY KEY,
  offering_id INT NOT NULL,
  exam_type VARCHAR(12) NOT NULL,
  exam_date DATE NOT NULL,
  INDEX idx_exams_offering (offering_id),
  INDEX idx_exams_date (exam_date),
  FOREIGN KEY (offering_id) REFERENCES course_offerings(id)
);

CREATE TABLE hostels (
  id INT PRIMARY KEY,
  name VARCHAR(50) NOT NULL,
  gender CHAR(1) NOT NULL,
  capacity INT NOT NULL
);

CREATE TABLE rooms (
  id INT PRIMARY KEY,
  hostel_id INT NOT NULL,
  room_no VARCHAR(10) NOT NULL,
  capacity INT NOT NULL,
  INDEX idx_rooms_hostel (hostel_id),
  FOREIGN KEY (hostel_id) REFERENCES hostels(id)
);

CREATE TABLE hostel_allocations (
  student_id INT NOT NULL,
  room_id INT NOT NULL,
  from_date DATE NOT NULL,
  to_date DATE NULL,
  PRIMARY KEY (student_id, from_date),
  INDEX idx_halloc_room (room_id),
  FOREIGN KEY (student_id) REFERENCES students(id),
  FOREIGN KEY (room_id) REFERENCES rooms(id)
);

CREATE TABLE messes (
  id INT PRIMARY KEY,
  name VARCHAR(50) NOT NULL,
  type VARCHAR(10) NOT NULL
);

CREATE TABLE mess_allocations (
  student_id INT NOT NULL,
  mess_id INT NOT NULL,
  month CHAR(7) NOT NULL,
  PRIMARY KEY (student_id, month),
  INDEX idx_malloc_mess (mess_id, month),
  FOREIGN KEY (student_id) REFERENCES students(id),
  FOREIGN KEY (mess_id) REFERENCES messes(id)
);

CREATE TABLE mess_change_requests (
  id INT PRIMARY KEY,
  student_id INT NOT NULL,
  from_mess_id INT NOT NULL,
  to_mess_id INT NOT NULL,
  status VARCHAR(10) NOT NULL,
  requested_at DATETIME NOT NULL,
  INDEX idx_mcr_student (student_id),
  INDEX idx_mcr_status (status),
  FOREIGN KEY (student_id) REFERENCES students(id),
  FOREIGN KEY (from_mess_id) REFERENCES messes(id),
  FOREIGN KEY (to_mess_id) REFERENCES messes(id)
);

CREATE TABLE feedback (
  id INT PRIMARY KEY,
  offering_id INT NOT NULL,
  faculty_id INT NOT NULL,
  dept_id INT NOT NULL,
  semester INT NOT NULL,
  section CHAR(1) NOT NULL,
  rating TINYINT NOT NULL,
  comment TEXT NOT NULL,
  submitted_at DATETIME NOT NULL,
  INDEX idx_feedback_offering (offering_id),
  INDEX idx_feedback_faculty (faculty_id),
  INDEX idx_feedback_dept (dept_id),
  INDEX idx_feedback_date (submitted_at),
  FOREIGN KEY (offering_id) REFERENCES course_offerings(id),
  FOREIGN KEY (faculty_id) REFERENCES faculty(id),
  FOREIGN KEY (dept_id) REFERENCES departments(id)
);

CREATE TABLE feedback_tags (
  feedback_id INT PRIMARY KEY,
  sentiment VARCHAR(10) NOT NULL,
  summary VARCHAR(255) NOT NULL,
  FOREIGN KEY (feedback_id) REFERENCES feedback(id)
);

CREATE TABLE feedback_themes (
  feedback_id INT NOT NULL,
  theme VARCHAR(30) NOT NULL,
  PRIMARY KEY (feedback_id, theme),
  INDEX idx_ftheme_theme (theme),
  FOREIGN KEY (feedback_id) REFERENCES feedback(id)
);

CREATE TABLE complaints (
  id INT PRIMARY KEY,
  student_id INT NOT NULL,
  category VARCHAR(16) NOT NULL,
  mess_id INT NULL,
  hostel_id INT NULL,
  text TEXT NOT NULL,
  status VARCHAR(12) NOT NULL,
  created_at DATETIME NOT NULL,
  resolved_at DATETIME NULL,
  INDEX idx_complaints_student (student_id),
  INDEX idx_complaints_mess (mess_id),
  INDEX idx_complaints_hostel (hostel_id),
  INDEX idx_complaints_date (created_at),
  INDEX idx_complaints_status (status),
  FOREIGN KEY (student_id) REFERENCES students(id),
  FOREIGN KEY (mess_id) REFERENCES messes(id),
  FOREIGN KEY (hostel_id) REFERENCES hostels(id)
);

CREATE TABLE complaint_tags (
  complaint_id INT PRIMARY KEY,
  sentiment VARCHAR(10) NOT NULL,
  summary VARCHAR(255) NOT NULL,
  FOREIGN KEY (complaint_id) REFERENCES complaints(id)
);

CREATE TABLE complaint_themes (
  complaint_id INT NOT NULL,
  theme VARCHAR(30) NOT NULL,
  PRIMARY KEY (complaint_id, theme),
  INDEX idx_ctheme_theme (theme),
  FOREIGN KEY (complaint_id) REFERENCES complaints(id)
);

CREATE TABLE attendance_weekly (
  offering_id INT NOT NULL,
  week_start DATE NOT NULL,
  sessions INT NOT NULL,
  present_count INT NOT NULL,
  possible_count INT NOT NULL,
  PRIMARY KEY (offering_id, week_start),
  FOREIGN KEY (offering_id) REFERENCES course_offerings(id)
);
