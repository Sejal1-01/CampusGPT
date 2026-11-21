import { describe, expect, it } from "vitest";
import { formatCell, formatDay, formatRole, toIsoDate } from "../format";
import { isSafeUrl } from "../url";

describe("formatCell", () => {
  it("shows NULL and empty values as a dash", () => {
    expect(formatCell(null)).toBe("—");
    expect(formatCell(undefined)).toBe("—");
    expect(formatCell("")).toBe("—");
  });

  it("formats numbers, booleans and text", () => {
    expect(formatCell(2024)).toBe("2024");
    expect(formatCell(41.333)).toBe("41.33");
    expect(formatCell(true)).toBe("Yes");
    expect(formatCell("DBMS")).toBe("DBMS");
  });
});

describe("formatRole", () => {
  it("title-cases role names", () => {
    expect(formatRole("course_faculty")).toBe("Course Faculty");
  });
});

describe("isSafeUrl", () => {
  it("allows only http and https", () => {
    expect(isSafeUrl("https://iiitbh.ac.in")).toBe(true);
    expect(isSafeUrl("javascript:alert(1)")).toBe(false);
    expect(isSafeUrl("not a url")).toBe(false);
  });
});

describe("dates", () => {
  it("formats a local date as ISO", () => {
    expect(toIsoDate(new Date(2026, 0, 5, 23, 30))).toBe("2026-01-05");
  });

  it("shows an ISO date as a short day and keeps bad input as is", () => {
    expect(formatDay("2026-11-13")).toBe("Fri, 13 Nov");
    expect(formatDay("soon")).toBe("soon");
  });
});
