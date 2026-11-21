import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { errorResponse, jsonResponse, mockFetch } from "../../test/fetchMock";
import { Composer } from "../Composer";

function setup(isAnswering = false) {
  const onSend = vi.fn().mockResolvedValue(true);
  render(<Composer isAnswering={isAnswering} onSend={onSend} />);
  return {
    onSend,
    input: screen.getByLabelText("Message"),
    send: screen.getByRole("button", { name: "Send" }),
  };
}

describe("Composer", () => {
  it("disables Send for empty or whitespace input", async () => {
    const { input, send } = setup();
    expect(send).toBeDisabled();
    await userEvent.type(input, "   ");
    expect(send).toBeDisabled();
  });

  it("sends on Enter, clears and keeps focus", async () => {
    const { input, onSend } = setup();
    await userEvent.type(input, "What is my CGPA?{Enter}");
    expect(onSend).toHaveBeenCalledWith("What is my CGPA?", null);
    expect(input).toHaveValue("");
    await waitFor(() => expect(input).toHaveFocus());
  });

  it("adds a new line on Shift+Enter", async () => {
    const { input, onSend } = setup();
    await userEvent.type(input, "line one{Shift>}{Enter}{/Shift}line two");
    expect(input).toHaveValue("line one\nline two");
    expect(onSend).not.toHaveBeenCalled();
  });

  it("handles Hindi, emoji and mixed scripts", async () => {
    const { input, onSend } = setup();
    await userEvent.type(input, "मेरी attendance कितनी है? 🙂{Enter}");
    expect(onSend).toHaveBeenCalledWith("मेरी attendance कितनी है? 🙂", null);
  });

  it("blocks messages over 2,000 characters with a clear message", async () => {
    const { input, send } = setup();
    await userEvent.click(input);
    await userEvent.paste("a".repeat(2001));
    expect(send).toBeDisabled();
    expect(screen.getByText(/Too long: 2,001 \/ 2,000 characters/)).toBeInTheDocument();
    expect(input).toHaveAttribute("aria-invalid", "true");
  });

  it("does not send while an answer is streaming", async () => {
    const { input, send, onSend } = setup(true);
    await userEvent.type(input, "hello{Enter}");
    expect(send).toBeDisabled();
    expect(onSend).not.toHaveBeenCalled();
  });

  it("uploads a PDF, shows a chip and sends it with the next message", async () => {
    mockFetch({
      "POST /api/files/pdf": () =>
        jsonResponse({ file_id: "f1", filename: "notes.pdf", pages: 3, characters: 900 }),
    });
    const { input, onSend } = setup();
    const file = new File(["%PDF"], "notes.pdf", { type: "application/pdf" });
    await userEvent.upload(screen.getByLabelText("PDF file"), file);
    expect(await screen.findByText("PDF: notes.pdf")).toBeInTheDocument();
    await userEvent.type(input, "Quiz me{Enter}");
    expect(onSend).toHaveBeenCalledWith("Quiz me", { fileId: "f1", filename: "notes.pdf" });
    expect(screen.queryByText("PDF: notes.pdf")).not.toBeInTheDocument();
  });

  it("shows the server's upload error", async () => {
    mockFetch({
      "POST /api/files/pdf": () =>
        errorResponse(400, "pdf_encrypted", "This PDF is password protected."),
    });
    setup();
    await userEvent.upload(
      screen.getByLabelText("PDF file"),
      new File(["x"], "locked.pdf", { type: "application/pdf" }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent("This PDF is password protected.");
  });

  it("rejects non-PDF files before uploading", async () => {
    const fetchMock = mockFetch({});
    setup();
    await userEvent.upload(
      screen.getByLabelText("PDF file"),
      new File(["x"], "photo.png", { type: "image/png" }),
      {
        applyAccept: false,
      },
    );
    expect(screen.getByRole("alert")).toHaveTextContent("That file is not a PDF.");
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("uploads a CSV, shows its table and sends it with the next message", async () => {
    mockFetch({
      "POST /api/files/csv": () =>
        jsonResponse({
          dataset_id: "d1",
          table_name: "upload_marks",
          columns: ["roll_no", "marks"],
          rows: 1250,
        }),
    });
    const { input, onSend } = setup();
    const file = new File(["roll_no,marks\n1,40"], "marks.csv", { type: "text/csv" });
    await userEvent.upload(screen.getByLabelText("CSV file"), file);
    expect(await screen.findByText("upload_marks · 1,250 rows")).toBeInTheDocument();
    await userEvent.type(input, "Average marks?{Enter}");
    expect(onSend).toHaveBeenCalledWith("Average marks?", {
      tableName: "upload_marks",
      columns: ["roll_no", "marks"],
      rows: 1250,
      filename: "marks.csv",
    });
    expect(screen.queryByText("upload_marks · 1,250 rows")).not.toBeInTheDocument();
  });

  it("shows the server's CSV error", async () => {
    mockFetch({
      "POST /api/files/csv": () =>
        errorResponse(400, "csv_encoding", "Save the CSV as UTF-8 and try again."),
    });
    setup();
    await userEvent.upload(
      screen.getByLabelText("CSV file"),
      new File(["\xff"], "data.csv", { type: "text/csv" }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Save the CSV as UTF-8 and try again.",
    );
  });

  it("rejects non-CSV and oversized files before uploading", async () => {
    const fetchMock = mockFetch({});
    setup();
    await userEvent.upload(
      screen.getByLabelText("CSV file"),
      new File(["x"], "data.xlsx", { type: "application/vnd.ms-excel" }),
      { applyAccept: false },
    );
    expect(screen.getByRole("alert")).toHaveTextContent("That file is not a CSV.");
    const big = new File(["x"], "big.csv", { type: "text/csv" });
    Object.defineProperty(big, "size", { value: 6 * 1024 * 1024 });
    await userEvent.upload(screen.getByLabelText("CSV file"), big);
    expect(screen.getByRole("alert")).toHaveTextContent("CSV is over 5 MB.");
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
