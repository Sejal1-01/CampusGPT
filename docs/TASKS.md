# Tasks

Status: `done`, `in_progress`, `todo`, `blocked` (with reason). Streams follow PRD §13.2.

| ID | Title | Stream | Depends on | Files | Done when | Status |
|---|---|---|---|---|---|---|
| T-M0-contracts | Shared contracts: DDL, view registry interface, Pydantic schemas + OpenAPI, tool signatures, get_model + FakeModel, config | — | — | docker/, backend/app/{config,schemas}.py, app/sql/registry.py, app/agent/{models,fake_model}.py | imports clean, OpenAPI exported | done |
| T-M0-1 | Spike: Strands agent → SSE → OpenUI renderer | C | contracts | app/services/chat.py, frontend/src/genui | streamed OpenUI Lang renders a chart from a tool result | done |
| T-M1-1 | docker compose MySQL 8.4 + init users/grants | A | contracts | docker-compose.yml, docker/mysql/01-*.sh | campus_ro can't read campus_auth or write (test_access_resolver) | done |
| T-M1-2 | Schemas campus + campus_auth | A | T-M1-1 | docker/mysql/02-*,03-* | tables created on first start | done |
| T-M1-3 | Access domain: policy.yaml, loader, resolver, department wall | A | T-M1-2 | app/access/* | test_access_resolver passes | done |
| T-M1-4 | Deterministic mock data + planted patterns + seeded accounts | A | T-M1-3 | scripts/generate_mock_data.py | test_mock_data passes; identical reruns | done |
| T-M1-5 | Access CLI | A | T-M1-3 | scripts/access.py | wall violations rejected via role, group, user | done |
| T-M2-1 | Logical views tagged (domain, scope) | B | contracts | app/sql/views.py | 62 views load; join keys derived | done |
| T-M2-2 | SQL guard | B | T-M2-1 | app/sql/guard.py | test_sql_guard (every rule accepted + rejected) | done |
| T-M2-3 | Scope rewrite | B | T-M2-1 | app/sql/rewrite.py | test_scope_rewrite per role | done |
| T-M2-4 | Executor with 5 s timeout, 500-row cap, describe-before-SQL | B | T-M2-2,3 | app/db.py, app/services/portal_data.py | timeout + undescribed tests pass | done |
| T-M3-1 | Login, sessions, cookie | C | T-M1-3 | app/auth.py, app/sessions.py, routes/auth_routes.py | test_routes login/401/logout | done |
| T-M3-2 | Agent + tools + system prompt | C | T-M2-4 | app/agent/* | test_chat_service with FakeModel | done |
| T-M3-3 | Chat SSE route, results API, CSV | C | T-M3-2 | routes/chat_routes.py, routes/content_routes.py | test_routes chat stream + CSV | done |
| T-M3-4 | Frontend: login, chat, OpenUI components, How I got this | C | T-M3-3 | frontend/ | lint, typecheck, test, build pass | done |
| T-M4-1 | Guardrails: word list + classifier | E | get_model | app/guardrails/* | test_guardrails | done |
| T-M4-2 | Web search (Tavily / ddgs) | E | tools | app/services/search.py | web row of §6 works with links | done |
| T-M5-1 | Quiz generate/grade/re-explain | D | get_model | app/learning/quiz.py | test_quiz | done |
| T-M6-1 | Tagger + tag_text.py | F | DDL, get_model | app/services/tagging.py, scripts/tag_text.py | test_tagging; tag tables filled | done |
| T-M7-1 | Eval datasets | G | planted patterns | evals/datasets/* | test_eval_datasets (gold SQL runs) | done |
| T-M7-2 | run_all.py + report builder | G | T-M7-1 | evals/*.py, scripts/build_eval_report.py | run completes; report has real numbers | in_progress (report has real numbers; quiz, latency and cost need a re-run after the free quota resets) |
| T-M7-3 | Postman collection + coverage test | — | routes | scripts/build_postman.py, docs/api/* | test_postman_coverage | done |
| T-M8-1 | CSV download | C | T-M3-3 | content_routes.py, DataTable | CSV link works | done |
| T-M8-2 | Flashcards | D | T-M5-1 | app/learning/flashcards.py | FlashcardDeck renders | done |
| T-M8-3 | Quiz from PDF | D | T-M5-1 | app/learning/pdf.py | test_pdf edge cases | done |
| T-M8-4 | Recurring issues | F | T-M6-1 | views `*_recurring_issues` | Mess 2 hygiene surfaced | done |
| T-M8-5 | At-risk list + draft message | B | T-M2-4 | app/services/at_risk.py, drafting.py | test_at_risk | done |
| T-M8-6 | Access page + audit log | C | T-M1-3 | routes/access_routes.py, frontend Access page | 403 for non-platform-admin; audit rows written | done |
| T-M9-1 | Exam study plan from exam dates + weakest subjects | D | T-M5-1 | app/learning/study_plan.py, StudyPlanCard | test_stretch study plan tests | done (unit/UI tests pass; not yet tried with the live model) |
| T-M9-2 | Spaced revision: wrong answers return 2 turns later | D | T-M5-1 | app/learning/quiz.py, app/services/chat.py | test_wrong_answers_come_back_after_two_turns | done |
| T-M9-3 | Question paper generator with CO mapping | D | get_model | app/services/question_paper.py, QuestionPaperCard | marks add up; students refused | done (unit/UI tests pass; not yet tried with the live model) |
| T-M9-4 | Accreditation report draft | F | T-M2-4 | app/services/accreditation.py, ReportDraftCard | scoped metrics; students refused | done (unit/UI tests pass; not yet tried with the live model) |
| T-M9-5 | Saved dashboards (localStorage, re-run SQL) | C | T-M3-3 | POST /api/results/rerun, Dashboard page | rerun uses current user's scope | done (unit/UI tests pass; not yet tried with the live model) |
| T-M9-6 | CSV upload as private session table | B | T-M2-2 | app/services/uploads.py, POST /api/files/csv | guard limits queries to uploaded tables | done (unit/UI tests pass; not yet tried with the live model) |
