import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { QuizCard } from "..";
import type { QuizPublic, QuizResult } from "../../../api/types";

const quiz: QuizPublic = {
  quiz_id: "qz_1",
  topic: "Normalisation",
  difficulty: "easy",
  submitted: false,
  result: null,
  questions: [
    {
      index: 0,
      question: "What removes partial dependency?",
      options: ["1NF", "2NF", "3NF", "BCNF"],
    },
    {
      index: 1,
      question: "What removes transitive dependency?",
      options: ["1NF", "2NF", "3NF", "4NF"],
    },
  ],
};

const result: QuizResult = {
  quiz_id: "qz_1",
  score: 1,
  total: 2,
  results: [
    { index: 0, chosen: 1, correct_option: 1, is_correct: true, explanation: "2NF." },
    {
      index: 1,
      chosen: null,
      correct_option: 2,
      is_correct: false,
      explanation: "3NF removes it.",
    },
  ],
  reexplanations: [
    { concept: "Transitive dependency", explanation: "A depends on B depends on C." },
  ],
};

describe("QuizCard", () => {
  it("submits chosen options with null for unanswered", async () => {
    const onSubmit = vi.fn();
    render(<QuizCard quiz={quiz} result={null} isSubmitting={false} onSubmit={onSubmit} />);
    expect(screen.getByText("2 unanswered (counted as wrong)")).toBeInTheDocument();
    const [firstQuestionOption] = screen.getAllByLabelText("2NF");
    if (!firstQuestionOption) throw new Error("Option not found");
    await userEvent.click(firstQuestionOption);
    await userEvent.click(screen.getByRole("button", { name: "Submit" }));
    expect(onSubmit).toHaveBeenCalledWith([1, null]);
  });

  it("shows score, marks and re-explanations after grading", () => {
    render(<QuizCard quiz={quiz} result={result} isSubmitting={false} onSubmit={vi.fn()} />);
    expect(screen.getByText("Score: 1 / 2")).toBeInTheDocument();
    expect(screen.getByText("Correct")).toBeInTheDocument();
    expect(screen.getByText("Wrong")).toBeInTheDocument();
    expect(screen.getByText(/Correct answer: 3NF\. 3NF removes it\./)).toBeInTheDocument();
    expect(screen.getByText("Transitive dependency:")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Submit" })).not.toBeInTheDocument();
    for (const radio of screen.getAllByRole("radio")) expect(radio).toBeDisabled();
  });
});
