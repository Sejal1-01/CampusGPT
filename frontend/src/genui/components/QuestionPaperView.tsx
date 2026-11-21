import { useRef } from "react";
import { api } from "../../api/client";
import type { PaperSection, QuestionPaper } from "../../api/types";
import { Button, Card } from "../../components/ui";
import { INSTITUTE_NAME } from "../../config";
import { downloadTextFile } from "../../lib/download";
import { printElement } from "../../lib/print";
import { questionPaperMarkdown } from "../markdownExport";
import { useAnswerData } from "../useAnswerData";
import { ContentStatus } from "./ContentStatus";

function PaperSectionView({ section }: { section: PaperSection }) {
  return (
    <section className="paper-section">
      <h5 className="paper-section-title">{section.title}</h5>
      {section.instructions && <p className="paper-instructions">{section.instructions}</p>}
      <ol className="paper-questions">
        {section.questions.map((question, index) => (
          <li key={`${index}-${question.number}`} className="paper-question">
            <span className="paper-question-number">{question.number}.</span>
            <span className="paper-question-text">{question.text}</span>
            <span className="paper-question-meta">
              [{question.marks}] {question.course_outcome} · {question.difficulty}
            </span>
          </li>
        ))}
      </ol>
    </section>
  );
}

function QuestionPaperBody({ paper }: { paper: QuestionPaper }) {
  const paperRef = useRef<HTMLElement>(null);
  const print = () => {
    if (paperRef.current) printElement(paperRef.current);
  };
  const download = () =>
    downloadTextFile(`question-paper-${paper.paper_id}.md`, questionPaperMarkdown(paper));

  return (
    <Card
      title="Question paper"
      actions={
        <>
          <Button variant="secondary" size="small" onClick={print}>
            Print / PDF
          </Button>
          <Button variant="secondary" size="small" onClick={download}>
            Download
          </Button>
        </>
      }
    >
      <article ref={paperRef} className="question-paper" aria-label={`${paper.subject} paper`}>
        <header className="paper-header">
          <img src="/iiitbh-logo.png" alt="IIIT Bhagalpur logo" className="paper-logo" />
          <div className="paper-heading">
            <p className="paper-institute">{INSTITUTE_NAME}</p>
            <h4 className="paper-subject">{paper.subject}</h4>
          </div>
        </header>
        <div className="paper-meta">
          <span>Max marks: {paper.total_marks}</span>
          <span>Time: {paper.duration_minutes} minutes</span>
        </div>
        {paper.sections.map((section, index) => (
          <PaperSectionView key={`${index}-${section.title}`} section={section} />
        ))}
      </article>
    </Card>
  );
}

export function QuestionPaperView({ paperId }: { paperId: string }) {
  const paper = useAnswerData(`question-paper:${paperId}`, () => api.questionPaper(paperId));
  if (paper.data) return <QuestionPaperBody paper={paper.data} />;
  return (
    <Card title="Question paper">
      <ContentStatus
        error={paper.error}
        loadingLabel="Loading question paper"
        notFoundTitle="Question paper not found"
        onRetry={paper.reload}
      />
    </Card>
  );
}
