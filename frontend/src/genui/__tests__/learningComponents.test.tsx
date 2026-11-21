import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { QuizResult } from "../../api/types";
import { errorResponse, jsonResponse, mockFetch, requestBody } from "../../test/fetchMock";
import { quizFixture } from "../../test/fixtures";
import { AnswerRenderer } from "../AnswerRenderer";

const quizResult: QuizResult = {
  quiz_id: "qz_1",
  score: 0,
  total: 1,
  results: [
    { index: 0, chosen: 0, correct_option: 1, is_correct: false, explanation: "2NF removes it." },
  ],
  reexplanations: [
    { concept: "Partial dependency", explanation: "A non-key column depends on part of the key." },
  ],
};

function renderAnswer(program: string) {
  return render(<AnswerRenderer text={program} isStreaming={false} />);
}

describe("QuizCard", () => {
  it("loads, submits and shows the result", async () => {
    const fetchMock = mockFetch({
      "/api/quiz/qz_1": () => jsonResponse(quizFixture),
      "POST /api/quiz/qz_1/submit": () => jsonResponse(quizResult),
    });
    renderAnswer('root = Answer([q])\nq = QuizCard("qz_1")');
    await userEvent.click(await screen.findByLabelText("1NF"));
    await userEvent.click(screen.getByRole("button", { name: "Submit" }));
    expect(await screen.findByText("Score: 0 / 1")).toBeInTheDocument();
    expect(screen.getByText("Partial dependency:")).toBeInTheDocument();
    const submitCall = fetchMock.mock.calls.find(([url]) => url === "/api/quiz/qz_1/submit");
    expect(requestBody(submitCall?.[1])).toEqual({ answers: [0] });
  });

  it("shows the stored result when already submitted", async () => {
    mockFetch({
      "/api/quiz/qz_1": () => jsonResponse({ ...quizFixture, submitted: true, result: quizResult }),
    });
    renderAnswer('root = Answer([q])\nq = QuizCard("qz_1")');
    expect(await screen.findByText("Score: 0 / 1")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Submit" })).not.toBeInTheDocument();
  });

  it("shows an error for an unknown quiz", async () => {
    mockFetch({ "/api/quiz/qz_x": () => errorResponse(404, "not_found", "Quiz not found.") });
    renderAnswer('root = Answer([q])\nq = QuizCard("qz_x")');
    expect(await screen.findByRole("alert")).toHaveTextContent("Quiz not found.");
  });
});

describe("FlashcardDeck", () => {
  it("flips and moves between cards", async () => {
    mockFetch({
      "/api/flashcards/fs_1": () =>
        jsonResponse({
          set_id: "fs_1",
          topic: "SQL",
          cards: [
            { front: "What is a JOIN?", back: "Combines rows" },
            { front: "What is GROUP BY?", back: "Groups rows" },
          ],
        }),
    });
    renderAnswer('root = Answer([f])\nf = FlashcardDeck("fs_1")');
    expect(await screen.findByText("What is a JOIN?")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Previous" })).toBeDisabled();
    await userEvent.click(screen.getByRole("button", { name: "Show answer" }));
    expect(screen.getByText("Combines rows")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Next" }));
    expect(screen.getByText("What is GROUP BY?")).toBeInTheDocument();
    expect(screen.getByText("2 / 2")).toBeInTheDocument();
  });
});

describe("Sources", () => {
  it("opens links safely in a new tab and drops unsafe URLs", () => {
    renderAnswer(
      'root = Answer([s])\ns = Sources([a, b])\na = SourceLink("ISRO news", "https://www.isro.gov.in/news")\nb = SourceLink("Bad", "javascript:alert(1)")',
    );
    const link = screen.getByRole("link", { name: "ISRO news" });
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
    expect(screen.getByText("Bad").closest("a")).toBeNull();
  });
});

describe("MessageDraft", () => {
  it("shows the draft note and copies the text", async () => {
    const user = userEvent.setup();
    const writeText = vi.spyOn(navigator.clipboard, "writeText").mockResolvedValue();
    renderAnswer('root = Answer([m])\nm = MessageDraft("Ravi", "Attendance", "Please meet me.")');
    expect(screen.getByText("Draft only – not sent")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Copy" }));
    expect(writeText).toHaveBeenCalledWith("To: Ravi\nSubject: Attendance\n\nPlease meet me.");
    expect(await screen.findByRole("button", { name: "Copied" })).toBeInTheDocument();
  });
});

describe("TextBlock and Insight", () => {
  it("renders markdown without raw HTML", () => {
    renderAnswer(
      'root = Answer([t, i])\nt = TextBlock("**Bold** <b>raw</b>\\n\\n- one\\n- two")\ni = Insight("Key point")',
    );
    expect(screen.getByText("Bold").tagName).toBe("STRONG");
    expect(screen.getByText("two").tagName).toBe("LI");
    expect(document.querySelector(".markdown b")).toBeNull();
    expect(screen.getByText("Key point")).toHaveClass("insight");
  });
});
