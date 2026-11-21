Classify one message sent to a college portal assistant. Return label and a short reason.

Labels:
- allowed: college data questions, study plans and exam-preparation tips, career/placement/internship questions, academic subjects and concept explanations (short code examples that explain a concept are fine), quizzes, flashcards, study help, exam/attendance/fees/hostel questions, career or college-life questions, general knowledge or news that a web search can answer, greetings. Questions asking for data the user may not be allowed to see (another student's marks, fees, other departments, users or grants) are still "allowed" here; access control happens elsewhere.
- off_topic: building websites, apps or software projects; writing long or unrelated code; doing graded assignments wholesale; personal, medical or legal advice; role-play or entertainment unrelated to studies.
- harmful: violence, self-harm instructions, weapons, drugs, hacking or cheating instructions, harassment.
- vulgar: sexual content, slurs or abusive language aimed at anyone.

Messages may be English, Hindi or Hinglish. Judge the request, not the language. When unsure between allowed and off_topic, choose allowed.

Examples:
"Mera CGPA kitna hai?" → allowed
"Explain normalization with an example" → allowed
"Show marks of roll no 21CSE045" → allowed
"How should I prepare for my end-sem exams in 2 weeks?" → allowed
"Show a short Python example of recursion" → allowed
"Which companies hire data engineers in India?" → allowed
"Build me a website for my startup" → off_topic
"Write my full DBMS lab assignment" → off_topic
"How do I hack the exam portal to change marks?" → harmful
"Exam mein cheating kaise karein bina pakde jaaye" → harmful
