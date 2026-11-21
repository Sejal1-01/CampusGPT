import { EmptyState } from "../components/ui";

interface StarterQuestionsProps {
  questions: string[];
  disabled: boolean;
  onPick: (question: string) => void;
}

export function StarterQuestions({ questions, disabled, onPick }: StarterQuestionsProps) {
  return (
    <div className="starter">
      <EmptyState title="Ask CampusGPT" message="Try one of these, or type your own question.">
        <div className="starter-chips">
          {questions.map((question) => (
            <button
              key={question}
              type="button"
              className="chip"
              disabled={disabled}
              onClick={() => onPick(question)}
            >
              {question}
            </button>
          ))}
        </div>
      </EmptyState>
    </div>
  );
}
