# Demo script

About 10 minutes. Log in at http://localhost:5173. Every demo password is `demo123`. Press **New chat** between roles.

| # | Log in as | Ask | What to point out |
|---|---|---|---|
| 1 | student1 | What's my attendance in DBMS and how many more can I skip? | Stat cards; open **How I got this** to show the SQL |
| 2 | student1 | Mera CGPA kitna hai aur kitni fees pending hai? | Hinglish question, Hinglish answer |
| 3 | student1 | Explain deadlock like a 5-mark answer, then give me 5 MCQs | Answer the quiz with some wrong options; wrong answers are re-explained. Two messages later the assistant offers a revision quiz |
| 4 | student1 | Make me a study plan for my end-sem exams | Day-by-day plan built from exam dates and weakest subjects |
| 5 | student1 | Show marks of roll no 21CSE045 | Refused: students see only their own records |
| 6 | faculty1 | Which students in my OS class are below 75% attendance? | Table limited to faculty1's own class |
| 7 | faculty1 | What did students say about my teaching this semester? | Theme chart (pace stands out); feedback is anonymous |
| 8 | faculty1 | Generate a 50 mark DBMS question paper covering ER model, SQL, normalization and transactions | Printable paper with CO mapping; **Print / PDF** |
| 9 | advisor1 | Show fee status of my advisees | Refused: advisors can't see fees |
| 10 | hod_cse | Subject-wise pass percentage in my department this semester | Bar chart; DBMS is the outlier. **Pin** it, then open **Dashboard** |
| 11 | hod_cse | Show attendance of ME 3rd-sem students | Refused: department wall |
| 12 | dean | Department-wise pending fees | Bar chart + insight |
| 13 | dean | Draft the NAAC report sections | Accreditation draft with metric tables |
| 14 | admin | Hostel-wise fee defaulters | Boys Hostel B stands out |
| 15 | admin | Which mess got the most hygiene complaints this month? | Mess 2 (from AI-tagged complaints) |
| 16 | admin | Compare average SGPA of hostellers vs day scholars by department | Grouped bars; gap only in ME |
| 17 | any | Build me a website for my startup | Guardrail refusal |
| 18 | any | What's the latest news about ISRO's next launch? | Web search with source links |
| 19 | admin | Attach a CSV (e.g. a marks sheet), then ask "average marks by city" | Questions over your own uploaded data |
| 20 | platform_admin | (password from `.env`) | Access page: roles, groups, effective access, audit log. Try granting (academics, college) to HOD: rejected by the department wall |

Tips: avoid running evals on demo day (free quota). If an answer is slow, the free Gemini servers are busy; wait and ask again.
