# Handover

For the teammate who will test and push this project.

## First run
1. Install Docker Desktop, uv (`brew install uv`) and Node 20+.
2. `cp .env.example .env`, put your own free Gemini key in `GEMINI_API_KEY` (https://aistudio.google.com/apikey), and replace every `change-me` value with any random strings.
3. Follow the Setup section of README.md (docker compose → generate_mock_data → tag_text → backend → frontend).
4. Open http://localhost:5173 and log in as `student1` / `demo123`.

## Status
- All Must, Should and Stretch features are built. 304 backend tests and 149 frontend tests pass; lint, type-check, build and the gitleaks scan are clean.
- Every row of the PRD §6 demo script was run live with the real model and worked (2–11 s each). Screenshots are in docs/screenshots and the README.
- Evaluation (docs/evaluation-report.md): SQL accuracy 82.5%, SQL validity 100%, data isolation 100%, explicit refusals 95%, guardrail refusals 100%, false refusals 0%, tool routing 96%, chart type 93.3%, sentiment 93.3%, theme F1 0.97. Insight faithfulness 88.2% (target 90%) was measured before the insight prompt fix.

## Still to do (for the tester)
1. Re-run the evals not finished on the free tier: `uv run python evals/run_all.py --suite charts --suite quiz --suite routing --suite tagging`, then `uv run python scripts/build_eval_report.py`.
2. Live-test the stretch features: "Make me a study plan for my end-sem exams" (student1), "Draft the NAAC report sections" (dean), Attach CSV + a question (any user), and get a quiz answer wrong then send two more messages (revision quiz).
3. Record a short demo video or GIF following docs/DEMO.md and link it in the README.
4. Keep the GitHub repo private (it uses the official IIIT Bhagalpur logo).

## Free tier tips
About 100–150 chat questions per day. Don't run evals on demo day. If answers are slow, Google's free servers are busy: wait and retry. `MODEL_FALLBACK_IDS` switches models automatically.
