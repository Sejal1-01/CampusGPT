import { useId, useState } from "react";
import type { QuizPublic, QuizQuestion, QuizResult } from "../../api/types";
import { Button } from "./Button";
import { Card } from "./Card";

type QuestionResult = QuizResult["results"][number];

interface QuizCardProps {
  quiz: QuizPublic;
  result: QuizResult | null;
  isSubmitting: boolean;
  onSubmit: (answers: (number | null)[]) => void;
}

interface QuestionProps {
  question: QuizQuestion;
  groupName: string;
  chosen: number | null;
  outcome: QuestionResult | null;
  onChoose: (option: number) => void;
}

function optionClass(optionIndex: number, outcome: QuestionResult | null): string {
  if (!outcome) return "quiz-option";
  if (optionIndex === outcome.correct_option) return "quiz-option quiz-option--correct";
  if (optionIndex === outcome.chosen) return "quiz-option quiz-option--wrong";
  return "quiz-option";
}

function QuizQuestionView({ question, groupName, chosen, outcome, onChoose }: QuestionProps) {
  return (
    <fieldset className="quiz-question">
      <legend>
        <span className="quiz-question-number">Q{question.index + 1}.</span> {question.question}
        {outcome && (
          <span className={`quiz-mark quiz-mark--${outcome.is_correct ? "right" : "wrong"}`}>
            {outcome.is_correct ? "Correct" : "Wrong"}
          </span>
        )}
      </legend>
      {question.options.map((option, optionIndex) => (
        <label key={optionIndex} className={optionClass(optionIndex, outcome)}>
          <input
            type="radio"
            name={groupName}
            checked={(outcome ? outcome.chosen : chosen) === optionIndex}
            disabled={outcome !== null}
            onChange={() => onChoose(optionIndex)}
          />
          <span>{option}</span>
        </label>
      ))}
      {outcome && !outcome.is_correct && (
        <p className="quiz-explanation">
          Correct answer: {question.options[outcome.correct_option] ?? "—"}. {outcome.explanation}
        </p>
      )}
    </fieldset>
  );
}

function QuizSummary({ result }: { result: QuizResult }) {
  return (
    <div className="quiz-summary">
      <p className="quiz-score">
        Score: {result.score} / {result.total}
      </p>
      {result.reexplanations.length > 0 && (
        <div className="quiz-reexplanations">
          <h4>Review these</h4>
          <ul>
            {result.reexplanations.map((item) => (
              <li key={item.concept}>
                <strong>{item.concept}:</strong> {item.explanation}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export function QuizCard({ quiz, result, isSubmitting, onSubmit }: QuizCardProps) {
  const groupPrefix = useId();
  const [answers, setAnswers] = useState<(number | null)[]>(() => quiz.questions.map(() => null));
  const unanswered = answers.filter((answer) => answer === null).length;

  const choose = (questionPosition: number, option: number) =>
    setAnswers((current) =>
      current.map((answer, index) => (index === questionPosition ? option : answer)),
    );

  return (
    <Card title={`Quiz: ${quiz.topic}`} actions={<span className="badge">{quiz.difficulty}</span>}>
      {result && <QuizSummary result={result} />}
      {quiz.questions.map((question, position) => (
        <QuizQuestionView
          key={question.index}
          question={question}
          groupName={`${groupPrefix}-${question.index}`}
          chosen={answers[position] ?? null}
          outcome={result?.results.find((item) => item.index === question.index) ?? null}
          onChoose={(option) => choose(position, option)}
        />
      ))}
      {!result && (
        <div className="quiz-actions">
          <Button onClick={() => onSubmit(answers)} isLoading={isSubmitting}>
            Submit
          </Button>
          {unanswered > 0 && (
            <span className="muted">{unanswered} unanswered (counted as wrong)</span>
          )}
        </div>
      )}
    </Card>
  );
}
