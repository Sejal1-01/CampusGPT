import { describe, expect, it } from "vitest";
import { library, promptOptions } from "../library";

describe("campus component library", () => {
  const prompt = library.prompt(promptOptions);

  it("uses Answer as the root", () => {
    expect(library.root).toBe("Answer");
    expect(prompt).toContain("root = Answer(");
  });

  it("lists every component with positional signatures", () => {
    expect(prompt).toContain(
      'DataChart(resultId: string, kind: "bar" | "grouped_bar" | "line" | "pie", x: string, y: string[], title?: string)',
    );
    expect(prompt).toContain("DataTable(resultId: string, title?: string)");
    expect(prompt).toContain("StatCard(label: string, value: string, hint?: string)");
    expect(prompt).toContain("MessageDraft(to: string, subject: string, body: string)");
    expect(prompt).toContain("StudyPlanCard(planId: string)");
    expect(prompt).toContain("QuestionPaperCard(paperId: string)");
    expect(prompt).toContain("ReportDraftCard(reportId: string)");
    for (const name of [
      "TextBlock",
      "Insight",
      "StatCards",
      "QuizCard",
      "FlashcardDeck",
      "Sources",
      "SourceLink",
    ]) {
      expect(prompt).toContain(`${name}(`);
    }
  });

  it("tells the model to use tool result ids and insights", () => {
    expect(prompt).toContain("Put an Insight right after every DataChart.");
    expect(prompt).toContain("never write numbers inline as chart data");
  });
});
