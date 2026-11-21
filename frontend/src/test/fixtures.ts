import type {
  AccreditationReport,
  Me,
  QuestionPaper,
  QuizPublic,
  StoredResult,
  StudyPlan,
} from "../api/types";
import type { PinnedTile } from "../lib/pinnedTiles";

export const testUser: Me = {
  username: "student1",
  display_name: "Aarav Kumar",
  roles: ["student"],
  department: "CSE",
  is_platform_admin: false,
  allowed_areas: ["academics"],
  starter_questions: ["What is my attendance?", "Show my marks"],
};

export const adminUser: Me = {
  ...testUser,
  username: "admin",
  display_name: "Platform Admin",
  roles: [],
  department: null,
  is_platform_admin: true,
  starter_questions: [],
};

export function storedResult(overrides: Partial<StoredResult> = {}): StoredResult {
  return {
    result_id: "r_ab12cd34",
    columns: ["subject_name", "pass_percent"],
    rows: [
      ["DBMS", 41.3],
      ["OS", 78.5],
    ],
    total_rows: 2,
    truncated: false,
    sql: "SELECT subject_name, pass_percent FROM subject_results",
    explanation: "Pass percentage per subject this semester.",
    ...overrides,
  };
}

export const quizFixture: QuizPublic = {
  quiz_id: "qz_1",
  topic: "Normalisation",
  difficulty: "medium",
  submitted: false,
  result: null,
  questions: [
    {
      index: 0,
      question: "Which form removes partial dependency?",
      options: ["1NF", "2NF", "3NF", "BCNF"],
    },
  ],
};

export const studyPlanFixture: StudyPlan = {
  plan_id: "sp_1",
  title: "End-sem study plan",
  notes: "Start with DBMS, your weakest subject.",
  days: [
    { date: "2026-11-13", subject: "DBMS", hours: 3, tasks: ["Revise joins", "Solve 2019 paper"] },
    { date: "2026-11-15", subject: "OS", hours: 2.5, tasks: ["Deadlock problems"] },
    { date: "2026-11-16", subject: "CN", hours: 2, tasks: ["Subnetting"] },
  ],
};

export const questionPaperFixture: QuestionPaper = {
  paper_id: "qp_1",
  subject: "Database Management Systems",
  total_marks: 50,
  duration_minutes: 120,
  sections: [
    {
      title: "Section A",
      instructions: "Answer all questions.",
      questions: [
        {
          number: "1",
          text: "Define a candidate key.",
          marks: 2,
          course_outcome: "CO1",
          difficulty: "easy",
        },
      ],
    },
    {
      title: "Section B",
      instructions: "Answer any two.",
      questions: [
        {
          number: "2",
          text: "Normalise the given relation to BCNF.",
          marks: 10,
          course_outcome: "CO3",
          difficulty: "hard",
        },
      ],
    },
  ],
};

export const reportFixture: AccreditationReport = {
  report_id: "rp_1",
  scope: "CSE department",
  result_ids: ["r_ab12cd34"],
  sections: [
    { heading: "Results", body: "Pass percentage rose to **82%**." },
    { heading: "Student feedback", body: "Clarity is the top theme." },
  ],
};

export function pinnedTile(overrides: Partial<PinnedTile> = {}): PinnedTile {
  return {
    id: "t1",
    title: "Pass % by subject",
    kind: "bar",
    x: "subject_name",
    y: ["pass_percent"],
    sql: "SELECT subject_name, pass_percent FROM subject_results",
    explanation: "Pass percentage per subject this semester.",
    pinnedAt: "2026-11-13T10:00:00.000Z",
    ...overrides,
  };
}
