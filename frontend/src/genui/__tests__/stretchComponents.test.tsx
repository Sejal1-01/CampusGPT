import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { captureDownloads } from "../../test/download";
import { errorResponse, jsonResponse, mockFetch } from "../../test/fetchMock";
import {
  questionPaperFixture,
  reportFixture,
  storedResult,
  studyPlanFixture,
} from "../../test/fixtures";
import { AnswerRenderer } from "../AnswerRenderer";

function renderAnswer(program: string, isStreaming = false) {
  return render(<AnswerRenderer text={program} isStreaming={isStreaming} />);
}

const PLAN_PROGRAM = 'root = Answer([p])\np = StudyPlanCard("sp_1")';
const PAPER_PROGRAM = 'root = Answer([p])\np = QuestionPaperCard("qp_1")';
const REPORT_PROGRAM = 'root = Answer([r])\nr = ReportDraftCard("rp_1")';

describe("StudyPlanCard", () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date(2026, 10, 14, 9, 0));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("shows the notes and a day table with the next day highlighted", async () => {
    mockFetch({ "/api/study-plans/sp_1": () => jsonResponse(studyPlanFixture) });
    renderAnswer(PLAN_PROGRAM);
    expect(await screen.findByRole("heading", { name: "End-sem study plan" })).toBeInTheDocument();
    expect(screen.getByText("Start with DBMS, your weakest subject.")).toBeInTheDocument();
    const rows = within(screen.getByRole("table")).getAllByRole("row");
    expect(rows).toHaveLength(4);
    expect(within(rows[1] as HTMLElement).getByText("Revise joins")).toBeInTheDocument();
    expect(within(rows[2] as HTMLElement).getByText("2.5")).toBeInTheDocument();
    expect(rows[2]).toHaveClass("table-row--highlight");
    expect(within(rows[2] as HTMLElement).getByText("Next")).toBeInTheDocument();
    expect(rows[1]).not.toHaveClass("table-row--highlight");
  });

  it("marks today's row as Today", async () => {
    vi.setSystemTime(new Date(2026, 10, 13, 9, 0));
    mockFetch({ "/api/study-plans/sp_1": () => jsonResponse(studyPlanFixture) });
    renderAnswer(PLAN_PROGRAM);
    expect(await screen.findByText("Today")).toBeInTheDocument();
  });

  it("downloads the plan as Markdown", async () => {
    const downloads = captureDownloads();
    mockFetch({ "/api/study-plans/sp_1": () => jsonResponse(studyPlanFixture) });
    renderAnswer(PLAN_PROGRAM);
    await userEvent.click(await screen.findByRole("button", { name: "Download" }));
    expect(downloads.lastFileName()).toBe("study-plan-sp_1.md");
    const text = await downloads.lastText();
    expect(text).toContain("# End-sem study plan");
    expect(text).toContain("| 2026-11-13 | DBMS | 3 | Revise joins; Solve 2019 paper |");
  });

  it("does not fetch while the answer is still streaming", () => {
    const fetchMock = mockFetch({});
    renderAnswer(PLAN_PROGRAM, true);
    expect(fetchMock).not.toHaveBeenCalled();
    expect(screen.getByText("Loading study plan")).toBeInTheDocument();
  });

  it("shows a not-found state for an unknown plan", async () => {
    mockFetch({
      "/api/study-plans/sp_1": () => errorResponse(404, "not_found", "Study plan not found."),
    });
    renderAnswer(PLAN_PROGRAM);
    expect(await screen.findByText("Study plan not found")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Retry" })).not.toBeInTheDocument();
  });

  it("shows a retryable error when loading fails", async () => {
    mockFetch({ "/api/study-plans/sp_1": () => errorResponse(503, "busy", "Server is busy.") });
    renderAnswer(PLAN_PROGRAM);
    expect(await screen.findByRole("alert")).toHaveTextContent("Server is busy.");
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });
});

describe("QuestionPaperCard", () => {
  it("renders the exam header, sections and question marks", async () => {
    mockFetch({ "/api/question-papers/qp_1": () => jsonResponse(questionPaperFixture) });
    renderAnswer(PAPER_PROGRAM);
    const paper = await screen.findByRole("article", { name: "Database Management Systems paper" });
    expect(within(paper).getByRole("img", { name: "IIIT Bhagalpur logo" })).toHaveAttribute(
      "src",
      "/iiitbh-logo.png",
    );
    expect(
      within(paper).getByText("Indian Institute of Information Technology Bhagalpur"),
    ).toBeInTheDocument();
    expect(within(paper).getByText("Max marks: 50")).toBeInTheDocument();
    expect(within(paper).getByText("Time: 120 minutes")).toBeInTheDocument();
    expect(within(paper).getByText("Answer any two.")).toBeInTheDocument();
    expect(within(paper).getByText("Normalise the given relation to BCNF.")).toBeInTheDocument();
    expect(within(paper).getByText("[10] CO3 · hard")).toBeInTheDocument();
  });

  it("prints only the paper", async () => {
    const print = vi.fn(() => {
      expect(document.body).toHaveClass("printing-target");
      const printRoot = document.querySelector("body > .print-root");
      expect(printRoot).toHaveTextContent("Define a candidate key.");
      expect(printRoot).not.toHaveTextContent("Print / PDF");
    });
    vi.stubGlobal("print", print);
    mockFetch({ "/api/question-papers/qp_1": () => jsonResponse(questionPaperFixture) });
    renderAnswer(PAPER_PROGRAM);
    await userEvent.click(await screen.findByRole("button", { name: "Print / PDF" }));
    expect(print).toHaveBeenCalledTimes(1);
    window.dispatchEvent(new Event("afterprint"));
    expect(document.body).not.toHaveClass("printing-target");
    expect(document.querySelector(".print-root")).toBeNull();
  });

  it("downloads the paper as Markdown", async () => {
    const downloads = captureDownloads();
    mockFetch({ "/api/question-papers/qp_1": () => jsonResponse(questionPaperFixture) });
    renderAnswer(PAPER_PROGRAM);
    await userEvent.click(await screen.findByRole("button", { name: "Download" }));
    expect(downloads.lastFileName()).toBe("question-paper-qp_1.md");
    const text = await downloads.lastText();
    expect(text).toContain("## Database Management Systems");
    expect(text).toContain("Max marks: 50 · Time: 120 minutes");
    expect(text).toContain("### Section A");
    expect(text).toContain("1. Define a candidate key. **[2] CO1 · easy**");
  });

  it("shows a not-found state for an unknown paper", async () => {
    mockFetch({
      "/api/question-papers/qp_1": () => errorResponse(404, "not_found", "Paper not found."),
    });
    renderAnswer(PAPER_PROGRAM);
    expect(await screen.findByText("Question paper not found")).toBeInTheDocument();
  });
});

describe("ReportDraftCard", () => {
  it("shows the draft badge, sections and each metric table", async () => {
    mockFetch({
      "/api/reports/rp_1": () => jsonResponse(reportFixture),
      "/api/results/r_ab12cd34": () => jsonResponse(storedResult()),
    });
    renderAnswer(REPORT_PROGRAM);
    expect(await screen.findByText("Draft – for committee review")).toBeInTheDocument();
    expect(screen.getByText("CSE department")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Student feedback" })).toBeInTheDocument();
    expect(screen.getByText("82%").tagName).toBe("STRONG");
    const table = await screen.findByRole("table");
    expect(within(table).getByText("41.3")).toBeInTheDocument();
    expect(screen.getByText("How I got this")).toBeInTheDocument();
  });

  it("downloads the report sections as Markdown", async () => {
    const downloads = captureDownloads();
    mockFetch({
      "/api/reports/rp_1": () => jsonResponse(reportFixture),
      "/api/results/r_ab12cd34": () => jsonResponse(storedResult()),
    });
    renderAnswer(REPORT_PROGRAM);
    await userEvent.click(await screen.findByRole("button", { name: "Download" }));
    expect(downloads.lastFileName()).toBe("report-rp_1.md");
    const text = await downloads.lastText();
    expect(text).toContain("_Draft – for committee review_");
    expect(text).toContain("Scope: CSE department");
    expect(text).toContain("## Results\n\nPass percentage rose to **82%**.");
  });

  it("shows a not-found state for an unknown report", async () => {
    mockFetch({ "/api/reports/rp_1": () => errorResponse(404, "not_found", "Report not found.") });
    renderAnswer(REPORT_PROGRAM);
    expect(await screen.findByText("Report not found")).toBeInTheDocument();
  });
});
