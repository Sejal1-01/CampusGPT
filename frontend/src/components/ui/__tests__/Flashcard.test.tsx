import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { Flashcard } from "..";

describe("Flashcard", () => {
  it("shows the front until flipped", async () => {
    const onFlip = vi.fn();
    const { rerender } = render(
      <Flashcard front="What is 2NF?" back="No partial deps" isFlipped={false} onFlip={onFlip} />,
    );
    expect(screen.getByText("What is 2NF?")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Show answer" }));
    expect(onFlip).toHaveBeenCalledOnce();
    rerender(<Flashcard front="What is 2NF?" back="No partial deps" isFlipped onFlip={onFlip} />);
    expect(screen.getByText("No partial deps")).toBeInTheDocument();
  });
});
