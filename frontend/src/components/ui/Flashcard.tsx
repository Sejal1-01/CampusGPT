interface FlashcardProps {
  front: string;
  back: string;
  isFlipped: boolean;
  onFlip: () => void;
}

export function Flashcard({ front, back, isFlipped, onFlip }: FlashcardProps) {
  return (
    <button
      type="button"
      className={`flashcard${isFlipped ? " flashcard--flipped" : ""}`}
      onClick={onFlip}
      aria-label={isFlipped ? "Show question" : "Show answer"}
    >
      <span className="flashcard-side-label">{isFlipped ? "Answer" : "Question"}</span>
      <span className="flashcard-text">{isFlipped ? back : front}</span>
      <span className="flashcard-hint">Click to flip</span>
    </button>
  );
}
