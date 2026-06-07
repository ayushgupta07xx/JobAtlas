import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "About — JobAtlas",
  description: "What JobAtlas is, and who built it.",
};

export default function AboutPage() {
  return (
    <section className="mx-auto max-w-2xl py-6">
      <p className="mb-6 text-xs font-medium uppercase tracking-[0.2em] text-accent">
        About
      </p>

      <h1 className="text-4xl font-semibold leading-[1.08] tracking-tight sm:text-5xl">
        One place for India&apos;s tech jobs.
      </h1>

      <div className="mt-8 space-y-5 text-lg leading-relaxed text-ink/70">
        <p>
          India&apos;s tech roles are scattered across a dozen job boards — the
          same listing reposted under three different titles, half of them
          stale. JobAtlas pulls them into a single index, removes the repeats,
          and lets you search all of it at once.
        </p>
        <p>
          Beyond keyword search, it reads your résumé and ranks roles by
          semantic similarity — matching on what the work actually involves, not
          just the words in the title.
        </p>
        <p>
          Everything is aggregated from official job-board APIs and public
          company listings, then deduplicated and ranked. A cleaner way to look,
          not another wall of noise.
        </p>
      </div>

      <div className="mt-12 rounded-xl border border-line bg-paper-raised p-6 shadow-card">
        <p className="text-sm font-medium text-ink">Built by Ayush Gupta</p>
        <p className="mt-2 text-sm leading-relaxed text-ink/60">
          JobAtlas is designed, built, and maintained by Ayush Gupta — one
          developer, after one too many evenings tab-hopping between job boards.
          {/* ↑ refine this line to taste */}
        </p>
        <div className="mt-4 flex gap-4 text-sm">
          <a
            href="https://github.com/ayushgupta07xx"
            target="_blank"
            rel="noreferrer"
            className="text-accent transition-colors hover:opacity-80"
          >
            GitHub
          </a>
          <a
            href="https://www.linkedin.com/in/ayush-gupta-544a803a2"
            target="_blank"
            rel="noreferrer"
            className="text-accent transition-colors hover:opacity-80"
          >
            LinkedIn
          </a>
        </div>
      </div>
    </section>
  );
}
