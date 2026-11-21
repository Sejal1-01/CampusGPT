import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import {
  Button,
  Card,
  ChartCard,
  EmptyState,
  ErrorBanner,
  Input,
  Select,
  Spinner,
  StatCard,
} from "..";

describe("Button", () => {
  it("calls onClick", async () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Save</Button>);
    await userEvent.click(screen.getByRole("button", { name: "Save" }));
    expect(onClick).toHaveBeenCalledOnce();
  });

  it("is disabled and busy while loading", () => {
    render(<Button isLoading>Save</Button>);
    const button = screen.getByRole("button", { name: /save/i });
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute("aria-busy", "true");
  });

  it("defaults to type button", () => {
    render(<Button>Go</Button>);
    expect(screen.getByRole("button")).toHaveAttribute("type", "button");
  });
});

describe("Input", () => {
  it("links the label and shows an error", () => {
    render(<Input label="Username" error="Required" />);
    const input = screen.getByLabelText("Username");
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(input).toHaveAccessibleDescription("Required");
  });
});

describe("Select", () => {
  it("renders options with a placeholder", async () => {
    const onChange = vi.fn();
    render(
      <Select
        label="Scope"
        options={["own", "department"]}
        placeholder="Pick"
        onChange={onChange}
      />,
    );
    await userEvent.selectOptions(screen.getByLabelText("Scope"), "department");
    expect(onChange).toHaveBeenCalled();
    expect(screen.getAllByRole("option")).toHaveLength(3);
  });
});

describe("Card and ChartCard", () => {
  it("renders title, actions, body and footer", () => {
    render(
      <Card title="Title" actions={<span>Action</span>} footer="Footer">
        Body
      </Card>,
    );
    expect(screen.getByRole("heading", { name: "Title" })).toBeInTheDocument();
    expect(screen.getByText("Action")).toBeInTheDocument();
    expect(screen.getByText("Body")).toBeInTheDocument();
    expect(screen.getByText("Footer")).toBeInTheDocument();
  });

  it("wraps a chart with a title", () => {
    render(<ChartCard title="Pass %">chart</ChartCard>);
    expect(screen.getByRole("heading", { name: "Pass %" })).toBeInTheDocument();
    expect(screen.getByText("chart")).toBeInTheDocument();
  });
});

describe("StatCard", () => {
  it("shows label, value and hint", () => {
    render(<StatCard label="CGPA" value="8.4" hint="out of 10" />);
    expect(screen.getByText("CGPA")).toBeInTheDocument();
    expect(screen.getByText("8.4")).toBeInTheDocument();
    expect(screen.getByText("out of 10")).toBeInTheDocument();
  });
});

describe("EmptyState", () => {
  it("shows title and message", () => {
    render(<EmptyState title="No matching records" message="Try another filter" />);
    expect(screen.getByText("No matching records")).toBeInTheDocument();
    expect(screen.getByText("Try another filter")).toBeInTheDocument();
  });
});

describe("ErrorBanner", () => {
  it("announces the message and supports retry and dismiss", async () => {
    const onRetry = vi.fn();
    const onDismiss = vi.fn();
    render(<ErrorBanner message="Failed" onRetry={onRetry} onDismiss={onDismiss} />);
    expect(screen.getByRole("alert")).toHaveTextContent("Failed");
    await userEvent.click(screen.getByRole("button", { name: "Retry" }));
    await userEvent.click(screen.getByRole("button", { name: "Dismiss" }));
    expect(onRetry).toHaveBeenCalledOnce();
    expect(onDismiss).toHaveBeenCalledOnce();
  });
});

describe("Spinner", () => {
  it("has a status role and label", () => {
    render(<Spinner label="Loading chart" />);
    expect(screen.getByRole("status")).toHaveTextContent("Loading chart");
  });

  it("has a hidden label when none is given", () => {
    render(<Spinner />);
    expect(screen.getByRole("status")).toHaveTextContent("Loading");
  });
});
