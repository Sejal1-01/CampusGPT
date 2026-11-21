import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { createAssistantMessage } from "../messages";
import { MessageItem } from "../MessageItem";

describe("MessageItem", () => {
  it("shows the tool progress while streaming", () => {
    render(
      <MessageItem message={{ ...createAssistantMessage("a"), activeTool: "query_portal_data" }} />,
    );
    expect(screen.getByRole("status")).toHaveTextContent("Querying portal data…");
  });

  it("shows the status text before any answer text", () => {
    render(
      <MessageItem
        message={{ ...createAssistantMessage("a"), status: "Checking your question" }}
      />,
    );
    expect(screen.getByRole("status")).toHaveTextContent("Checking your question");
  });

  it("shows refusals and errors", () => {
    render(
      <MessageItem
        message={{
          ...createAssistantMessage("a"),
          isStreaming: false,
          refusal: "I can only help with campus questions.",
          error: { code: "x", message: "Something failed." },
        }}
      />,
    );
    expect(screen.getByText("I can only help with campus questions.")).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("Something failed.");
  });

  it("shows user text and attachment", () => {
    render(
      <MessageItem
        message={{ id: "u", role: "user", text: "Quiz me", attachmentLabel: "PDF: notes.pdf" }}
      />,
    );
    expect(screen.getByText("Quiz me")).toBeInTheDocument();
    expect(screen.getByText("PDF: notes.pdf")).toBeInTheDocument();
  });
});
