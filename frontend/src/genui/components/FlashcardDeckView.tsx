import { useIsStreaming } from "@openuidev/react-lang";
import { useState } from "react";
import { api, errorMessage } from "../../api/client";
import { Button, Card, EmptyState, ErrorBanner, Flashcard, Spinner } from "../../components/ui";
import { useApi } from "../../hooks/useApi";

export function FlashcardDeckView({ setId }: { setId: string }) {
  const isStreaming = useIsStreaming();
  const deck = useApi(isStreaming ? null : `flashcards:${setId}`, () => api.flashcards(setId), {
    cache: true,
  });
  const [position, setPosition] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);

  if (deck.error) return <ErrorBanner message={errorMessage(deck.error)} onRetry={deck.reload} />;
  if (!deck.data) return <Spinner label="Loading flashcards" />;

  const { cards, topic } = deck.data;
  const card = cards[position];
  if (!card) return <EmptyState title="No flashcards" />;

  const move = (step: number) => {
    setPosition((current) => Math.min(Math.max(current + step, 0), cards.length - 1));
    setIsFlipped(false);
  };

  return (
    <Card title={`Flashcards: ${topic}`}>
      <Flashcard
        front={card.front}
        back={card.back}
        isFlipped={isFlipped}
        onFlip={() => setIsFlipped((current) => !current)}
      />
      <div className="flashcard-nav">
        <Button variant="secondary" size="small" onClick={() => move(-1)} disabled={position === 0}>
          Previous
        </Button>
        <span className="muted">
          {position + 1} / {cards.length}
        </span>
        <Button
          variant="secondary"
          size="small"
          onClick={() => move(1)}
          disabled={position === cards.length - 1}
        >
          Next
        </Button>
      </div>
    </Card>
  );
}
