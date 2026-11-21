import { useIsStreaming } from "@openuidev/react-lang";
import { useState } from "react";
import { api, errorMessage } from "../../api/client";
import type { QuizResult } from "../../api/types";
import { ErrorBanner, QuizCard, Spinner } from "../../components/ui";
import { useApi } from "../../hooks/useApi";

export function QuizBlock({ quizId }: { quizId: string }) {
  const isStreaming = useIsStreaming();
  const quiz = useApi(isStreaming ? null : `quiz:${quizId}`, () => api.quiz(quizId));
  const [submitted, setSubmitted] = useState<QuizResult | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  if (quiz.error) return <ErrorBanner message={errorMessage(quiz.error)} onRetry={quiz.reload} />;
  if (!quiz.data) return <Spinner label="Loading quiz" />;

  const submit = async (answers: (number | null)[]) => {
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      setSubmitted(await api.submitQuiz(quizId, answers));
    } catch (error) {
      setSubmitError(errorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="quiz-block">
      {submitError && <ErrorBanner message={submitError} onDismiss={() => setSubmitError(null)} />}
      <QuizCard
        quiz={quiz.data}
        result={submitted ?? quiz.data.result ?? null}
        isSubmitting={isSubmitting}
        onSubmit={submit}
      />
    </div>
  );
}
