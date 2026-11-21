Write a multiple-choice quiz for an engineering student.

Rules:
- Exactly {n} questions on the topic, difficulty {difficulty}.
- Each question has exactly 4 options and exactly one of them is true. The other three must be clearly false, not just less complete (e.g. never list several of the four deadlock conditions as options to "which condition is necessary?"; ask "which is NOT a necessary condition?" instead). correct_option is the 0-based index of the true option.
- Before answering, check every option: if two could be defended as correct, rewrite the question.
- Vary the position of the correct option.
- explanation: 1-3 sentences saying why the correct option is right.
- concept: the 2-5 word concept the question tests (used to re-explain wrong answers).
- No "all of the above" or "none of the above". No trick wording. Facts must be textbook-correct.
- If source text is given, use only facts from it.
