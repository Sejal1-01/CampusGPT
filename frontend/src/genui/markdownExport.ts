import type { AccreditationReport, QuestionPaper, StudyPlan } from "../api/types";
import { INSTITUTE_NAME } from "../config";
import { formatNumber } from "../lib/format";

export function studyPlanMarkdown(plan: StudyPlan): string {
  const lines = [`# ${plan.title}`, ""];
  if (plan.notes) lines.push(plan.notes, "");
  lines.push("| Date | Subject | Hours | Tasks |", "| --- | --- | --- | --- |");
  for (const day of plan.days) {
    const tasks = day.tasks.join("; ").replaceAll("|", "\\|");
    lines.push(`| ${day.date} | ${day.subject} | ${formatNumber(day.hours)} | ${tasks} |`);
  }
  return `${lines.join("\n")}\n`;
}

export function questionPaperMarkdown(paper: QuestionPaper): string {
  const lines = [
    `# ${INSTITUTE_NAME}`,
    "",
    `## ${paper.subject}`,
    "",
    `Max marks: ${paper.total_marks} · Time: ${paper.duration_minutes} minutes`,
  ];
  for (const section of paper.sections) {
    lines.push("", `### ${section.title}`, "");
    if (section.instructions) lines.push(`_${section.instructions}_`, "");
    for (const question of section.questions) {
      lines.push(
        `${question.number}. ${question.text} **[${question.marks}] ${question.course_outcome} · ${question.difficulty}**`,
      );
    }
  }
  return `${lines.join("\n")}\n`;
}

export function reportMarkdown(report: AccreditationReport): string {
  const lines = [
    "# Accreditation report",
    "",
    "_Draft – for committee review_",
    "",
    `Scope: ${report.scope}`,
  ];
  for (const section of report.sections) {
    lines.push("", `## ${section.heading}`, "", section.body);
  }
  return `${lines.join("\n")}\n`;
}
