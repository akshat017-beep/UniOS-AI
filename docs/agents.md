# Agent architecture

> Status: the router and all nine agent roles are implemented (Phase 2). Each
> agent is a system-prompt specialisation in `app/agents/registry.py`; Phase 4
> adds their tools (retrieval, code execution, resume parsing). Tool-backed
> behaviour is never faked — an agent says when it lacks the data.

## Routing

`app/agents/router.py` scores the message against each agent's keyword set plus
structural signals (for example code in the message) and returns the agent, a
confidence value and the matched signals, so the interface can show *why* a given
agent answered. An attached document always routes to the Document Agent. Below
a confidence of 0.4 the Study Agent answers as the generalist. The decision is
deterministic and unit-tested, and a model-based re-ranker can be layered on top
without changing any caller.

## Orchestration

```text
User → AI Gateway → Intent detection → Agent router → Agent(s)
     → Tools / RAG / Database / APIs → Verification → Response → Memory
```

The router may select several agents. "Analyse this PDF and make viva questions"
resolves to the Document Agent followed by the Study Agent, with the retrieved
passages passed forward as untrusted context.

## Agents

| Agent | Responsibilities |
| --- | --- |
| Study | Explain concepts, notes, MCQs, viva questions, study plans, summaries, flashcards, practice problems |
| Research | Search and summarise papers, compare them, extract methodology, identify gaps, cited reports |
| Coding | Explain, debug, review, improve, generate tests, explain compiler errors and complexity (C, C++, Python, Java, JS, TS) |
| Career | Resume analysis and generation, skill gaps, job and internship matching, interview prep, roadmaps |
| Document | PDF question answering, summarisation, OCR, tables, diagrams, cross-document comparison |
| Campus | Departments, faculty, calendar, events, clubs, facilities, rules, notices |
| Academic performance | GPA/CGPA analysis, grades, attendance, trends, weak subjects, recommendations |
| Communication | Emails, applications, formal letters, messages, professional rewrites |
| University admin | Announcements, student support, document management, FAQs, analytics, workflows |

## Activity transparency

The UI may show high-level progress — "Reading uploaded PDF", "Retrieving
relevant sections", "Generating questions". It never exposes model reasoning or
private chain-of-thought, and AI-generated content is always labelled.

## Safety rules

1. Retrieved and uploaded content is untrusted data. Instructions inside a
   document are never followed.
2. University-specific claims require a retrieved source; below the retrieval
   confidence threshold the agent says it does not know.
3. Answers derived from documents carry citations with document and page.
4. Agents only see data the requesting user's role permits.
