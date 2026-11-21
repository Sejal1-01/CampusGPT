import { createLibrary, defineComponent, type PromptOptions } from "@openuidev/react-lang";
import { z } from "zod/v4";
import { Markdown } from "../components/Markdown";
import { StatCard as StatCardView } from "../components/ui/StatCard";
import { DataChartView } from "./components/DataChartView";
import { DataTableView } from "./components/DataTableView";
import { FlashcardDeckView } from "./components/FlashcardDeckView";
import { MessageDraftView } from "./components/MessageDraftView";
import { QuestionPaperView } from "./components/QuestionPaperView";
import { QuizBlock } from "./components/QuizBlock";
import { ReportDraftView } from "./components/ReportDraftView";
import { SourceLinkView, SourcesView } from "./components/SourcesView";
import { StudyPlanView } from "./components/StudyPlanView";

const TextBlock = defineComponent({
  name: "TextBlock",
  description:
    "Short prose in Markdown (paragraphs, bold, bullet lists). Use for the direct answer.",
  props: z.object({ markdown: z.string() }),
  component: ({ props }) => <Markdown text={props.markdown} />,
});

const Insight = defineComponent({
  name: "Insight",
  description: "One or two sentences stating the key finding of the chart just above it.",
  props: z.object({ text: z.string() }),
  component: ({ props }) => <p className="insight">{props.text}</p>,
});

const StatCard = defineComponent({
  name: "StatCard",
  description:
    "One headline number with a label and an optional short hint, e.g. the comparison or unit.",
  props: z.object({ label: z.string(), value: z.string(), hint: z.string().optional() }),
  component: ({ props }) => (
    <StatCardView label={props.label} value={props.value} hint={props.hint} />
  ),
});

const StatCards = defineComponent({
  name: "StatCards",
  description:
    "A row of StatCard items for single values such as a count, a percentage or a total.",
  props: z.object({ cards: z.array(StatCard.ref) }),
  component: ({ props, renderNode }) => <div className="stat-cards">{renderNode(props.cards)}</div>,
});

const DataChart = defineComponent({
  name: "DataChart",
  description:
    "Chart of a stored query result: column x on the axis against numeric columns y. resultId must come from query_portal_data.",
  props: z.object({
    resultId: z.string(),
    kind: z.enum(["bar", "grouped_bar", "line", "pie"]),
    x: z.string(),
    y: z.array(z.string()),
    title: z.string().optional(),
  }),
  component: ({ props }) => (
    <DataChartView
      resultId={props.resultId}
      kind={props.kind}
      x={props.x}
      y={props.y}
      title={props.title}
    />
  ),
});

const DataTable = defineComponent({
  name: "DataTable",
  description:
    "Table of every column of a stored query result. resultId must come from query_portal_data.",
  props: z.object({ resultId: z.string(), title: z.string().optional() }),
  component: ({ props }) => <DataTableView resultId={props.resultId} title={props.title} />,
});

const QuizCard = defineComponent({
  name: "QuizCard",
  description:
    "Interactive multiple-choice quiz. quizId must come from generate_quiz or quiz_from_pdf.",
  props: z.object({ quizId: z.string() }),
  component: ({ props }) => <QuizBlock quizId={props.quizId} />,
});

const FlashcardDeck = defineComponent({
  name: "FlashcardDeck",
  description: "Flip-card deck for revision. setId must come from generate_flashcards.",
  props: z.object({ setId: z.string() }),
  component: ({ props }) => <FlashcardDeckView setId={props.setId} />,
});

const StudyPlanCard = defineComponent({
  name: "StudyPlanCard",
  description:
    "Day-by-day exam study plan with subjects, hours and tasks. planId must come from make_study_plan.",
  props: z.object({ planId: z.string() }),
  component: ({ props }) => <StudyPlanView planId={props.planId} />,
});

const QuestionPaperCard = defineComponent({
  name: "QuestionPaperCard",
  description:
    "Printable exam paper with sections, marks and CO mapping per question. paperId must come from generate_question_paper.",
  props: z.object({ paperId: z.string() }),
  component: ({ props }) => <QuestionPaperView paperId={props.paperId} />,
});

const ReportDraftCard = defineComponent({
  name: "ReportDraftCard",
  description:
    "Accreditation (NAAC/NBA) report draft: narrative sections plus its metric tables. reportId must come from draft_accreditation_report.",
  props: z.object({ reportId: z.string() }),
  component: ({ props }) => <ReportDraftView reportId={props.reportId} />,
});

const SourceLink = defineComponent({
  name: "SourceLink",
  description: "One web source: page title and its full URL.",
  props: z.object({ title: z.string(), url: z.string() }),
  component: ({ props }) => <SourceLinkView title={props.title} url={props.url} />,
});

const Sources = defineComponent({
  name: "Sources",
  description: "List of web sources used in the answer. Only URLs returned by web_search.",
  props: z.object({ links: z.array(SourceLink.ref) }),
  component: ({ props, renderNode }) => <SourcesView>{renderNode(props.links)}</SourcesView>,
});

const MessageDraft = defineComponent({
  name: "MessageDraft",
  description: "A drafted message for the user to copy and send themselves. It is never sent.",
  props: z.object({ to: z.string(), subject: z.string(), body: z.string() }),
  component: ({ props }) => (
    <MessageDraftView to={props.to} subject={props.subject} body={props.body} />
  ),
});

const answerChild = z.union([
  TextBlock.ref,
  Insight.ref,
  StatCards.ref,
  DataChart.ref,
  DataTable.ref,
  QuizCard.ref,
  FlashcardDeck.ref,
  StudyPlanCard.ref,
  QuestionPaperCard.ref,
  ReportDraftCard.ref,
  Sources.ref,
  MessageDraft.ref,
]);

const Answer = defineComponent({
  name: "Answer",
  description:
    "The whole reply: its parts stacked top to bottom. Every reply is exactly one Answer.",
  props: z.object({ children: z.array(answerChild) }),
  component: ({ props, renderNode }) => <div className="answer">{renderNode(props.children)}</div>,
});

export const library = createLibrary({
  root: "Answer",
  components: [
    Answer,
    TextBlock,
    Insight,
    StatCards,
    StatCard,
    DataChart,
    DataTable,
    QuizCard,
    FlashcardDeck,
    StudyPlanCard,
    QuestionPaperCard,
    ReportDraftCard,
    Sources,
    SourceLink,
    MessageDraft,
  ],
  componentGroups: [
    { name: "Layout", components: ["Answer"] },
    {
      name: "Text",
      components: ["TextBlock", "Insight"],
      notes: [
        "- Lead with the answer in one TextBlock. Keep it short: no filler, no restating the question.",
        "- Insight goes directly after the DataChart it describes.",
      ],
    },
    {
      name: "Data",
      components: ["StatCards", "StatCard", "DataChart", "DataTable"],
      notes: [
        '- DataChart kind: "bar" to compare categories, "grouped_bar" for several measures per category, "line" for trends over time, "pie" only for parts of a whole with 6 or fewer slices.',
        "- x and every y must be exact column names from the query result. y columns must be numeric.",
        "- Use DataTable for lists of records or when no chart fits.",
      ],
    },
    {
      name: "Learning",
      components: ["QuizCard", "FlashcardDeck", "StudyPlanCard"],
      notes: [
        "- The quiz, flashcard and study plan content is loaded by id; do not repeat it in text.",
      ],
    },
    {
      name: "Academic documents",
      components: ["QuestionPaperCard", "ReportDraftCard"],
      notes: [
        "- The paper and report are loaded by id; give a one-line TextBlock above, not their content.",
        "- ReportDraftCard already shows its metric tables; do not add DataTable for them.",
      ],
    },
    {
      name: "Sources and drafts",
      components: ["Sources", "SourceLink", "MessageDraft"],
      notes: ["- Never claim a MessageDraft was sent."],
    },
  ],
});

export const promptOptions: PromptOptions = {
  preamble:
    "Write every reply as one OpenUI Lang program built only from the components below. The app renders it as the answer.",
  additionalRules: [
    "Write exactly one Answer per reply, starting with root = Answer([...]).",
    "DataChart and DataTable must reference a resultId returned by the query_portal_data tool in this conversation. Never invent a resultId and never write numbers inline as chart data.",
    "Put an Insight right after every DataChart.",
    "Use StatCards for single values (one count, percentage or total) instead of a chart or table.",
    "For a refusal or a short plain reply, use a single TextBlock.",
    'Inside strings, write line breaks as \\n and escape double quotes as \\".',
    "Only use ids (resultId, quizId, setId, planId, paperId, reportId) and URLs that a tool returned.",
  ],
  examples: [
    [
      "root = Answer([t, c, i])",
      't = TextBlock("Pass percentage by subject")',
      'c = DataChart("r_ab12cd34", "bar", "subject_name", ["pass_percent"], "Pass % by subject")',
      'i = Insight("DBMS has the lowest pass rate at 41.3%.")',
    ].join("\n"),
    [
      "root = Answer([t, s])",
      't = TextBlock("Your attendance in DBMS is **68%**, below the 75% requirement.")',
      "s = StatCards([a, b])",
      'a = StatCard("Attended", "34 / 50", "classes")',
      'b = StatCard("Needed for 75%", "4", "more classes in a row")',
    ].join("\n"),
    [
      "root = Answer([t, q])",
      't = TextBlock("Here is a 5-question quiz on normalisation.")',
      'q = QuizCard("qz_7f3a91")',
    ].join("\n"),
  ],
};
