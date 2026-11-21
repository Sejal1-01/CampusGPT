import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AnswerRenderer } from "../AnswerRenderer";

describe("malformed OpenUI output", () => {
  it("shows plain text when nothing parses", () => {
    render(<AnswerRenderer text="Your CGPA is 8.4." isStreaming={false} />);
    expect(screen.getByText("Your CGPA is 8.4.")).toBeInTheDocument();
  });

  it("keeps the parsed parts when one component is invalid", () => {
    render(
      <AnswerRenderer
        text={
          'root = Answer([t, x, s])\nt = TextBlock("Here is your summary")\nx = Unknown("oops")\ns = StatCards([a])\na = StatCard("CGPA", "8.4")'
        }
        isStreaming={false}
      />,
    );
    expect(screen.getByText("Here is your summary")).toBeInTheDocument();
    expect(screen.getByText("8.4")).toBeInTheDocument();
  });

  it("renders a truncated program without crashing", () => {
    render(
      <AnswerRenderer
        text={'root = Answer([t, c])\nt = TextBlock("Partial answer")\nc = DataChart("r_1", "ba'}
        isStreaming={false}
      />,
    );
    expect(screen.getByText("Partial answer")).toBeInTheDocument();
  });

  it("does not show raw text while still streaming", () => {
    const { container } = render(<AnswerRenderer text="root = Ans" isStreaming />);
    expect(container).not.toHaveTextContent("root = Ans");
  });
});
