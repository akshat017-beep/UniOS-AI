import Link from "next/link";
import { SiteHeader } from "@/components/site-header";
import { branding } from "@/lib/branding";

const capabilities = [
  {
    title: "AI Assistant",
    body: "One conversation that routes your request to the right specialist agent automatically.",
  },
  {
    title: "Study Intelligence",
    body: "Explanations, notes, MCQs, viva questions, flashcards and study plans from your material.",
  },
  {
    title: "Research Intelligence",
    body: "Find, summarise and compare papers; extract methodology, datasets and research gaps.",
  },
  {
    title: "Coding Assistant",
    body: "Explain, debug, review and test C, C++, Python, Java, JavaScript and TypeScript.",
  },
  {
    title: "Career Intelligence",
    body: "Skill-gap analysis, roadmaps, project ideas, resume building and interview practice.",
  },
  {
    title: "Campus Intelligence",
    body: "Departments, faculty, calendar, events, clubs, facilities, rules and notices in one place.",
  },
  {
    title: "Multimodal input",
    body: "Ask with text, PDFs, handwritten notes, screenshots, diagrams or your voice.",
  },
  {
    title: "Secure university knowledge",
    body: "Answers grounded in your university's documents, with the source and page shown.",
  },
];

const steps = [
  { step: "01", title: "Ask", body: "Type, speak, or upload a document, image or question paper." },
  { step: "02", title: "Route", body: "The orchestrator picks the agents your request actually needs." },
  { step: "03", title: "Ground", body: "Retrieval pulls the relevant passages from approved sources." },
  { step: "04", title: "Answer", body: "You get a verified response with citations you can open." },
];

const faqs = [
  {
    q: "Is this just a chatbot with a university theme?",
    a: "No. Requests are routed across nine specialised agents that use retrieval, university data and tools, and every document-based answer carries its source.",
  },
  {
    q: "Where do the answers come from?",
    a: "University PDFs, notices, regulations, course material and documents you upload. When no reliable source exists, the system says so instead of guessing.",
  },
  {
    q: "Can my university host it privately?",
    a: "Yes. The whole stack runs from a single Docker Compose file, and the AI provider is configurable through environment variables.",
  },
  {
    q: "Which parts are built today?",
    a: "The foundation: accounts, roles, dashboard, database and deployment. AI agents, retrieval and multimodal input arrive in the phases documented in the repository.",
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      <SiteHeader />

      <main>
        <section className="mx-auto max-w-6xl px-5 pb-20 pt-20 text-center sm:pt-28">
          <p className="inline-flex rounded-full border px-3 py-1 text-xs font-medium uppercase tracking-widest text-muted-foreground">
            AI University Operating System
          </p>
          <h1 className="mx-auto mt-6 max-w-3xl text-4xl font-semibold leading-tight tracking-tight sm:text-6xl">
            {branding.name}
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-muted-foreground sm:text-xl">
            {branding.heroLine}
          </p>
          <p className="mx-auto mt-3 max-w-xl text-sm text-muted-foreground">{branding.tagline}</p>

          <div className="mt-9 flex flex-wrap items-center justify-center gap-3">
            <Link href="/register" className="btn-primary">
              Start using {branding.shortName}
            </Link>
            <Link href="/login" className="btn-ghost">
              I already have an account
            </Link>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-5 pb-20">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {capabilities.map((item) => (
              <article key={item.title} className="card p-5">
                <h2 className="text-base font-semibold">{item.title}</h2>
                <p className="mt-2 text-sm text-muted-foreground">{item.body}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="border-y bg-surface-muted">
          <div className="mx-auto max-w-6xl px-5 py-16">
            <h2 className="text-2xl font-semibold tracking-tight">How it works</h2>
            <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {steps.map((item) => (
                <div key={item.step}>
                  <span className="text-sm font-semibold text-accent">{item.step}</span>
                  <h3 className="mt-1 font-semibold">{item.title}</h3>
                  <p className="mt-1 text-sm text-muted-foreground">{item.body}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-5 py-16">
          <h2 className="text-2xl font-semibold tracking-tight">Technology</h2>
          <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
            Next.js and TypeScript on the front end, FastAPI and PostgreSQL on the back end, a
            provider-agnostic AI layer, and pgvector for retrieval. Everything runs locally with
            Docker Compose.
          </p>
        </section>

        <section className="mx-auto max-w-3xl px-5 pb-20">
          <h2 className="text-2xl font-semibold tracking-tight">Frequently asked questions</h2>
          <dl className="mt-6 space-y-5">
            {faqs.map((faq) => (
              <div key={faq.q} className="card p-5">
                <dt className="font-semibold">{faq.q}</dt>
                <dd className="mt-2 text-sm text-muted-foreground">{faq.a}</dd>
              </div>
            ))}
          </dl>
        </section>
      </main>

      <footer className="border-t">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 px-5 py-8 text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
          <span>
            {branding.name} — {branding.tagline}
          </span>
          <span>Open source, MIT licensed.</span>
        </div>
      </footer>
    </div>
  );
}
