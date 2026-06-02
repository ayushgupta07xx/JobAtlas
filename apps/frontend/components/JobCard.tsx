import Link from "next/link";

import { formatSalary, type SearchHit } from "@/lib/api";

export function JobCard({ job }: { job: SearchHit }) {
  return (
    <article className="group rounded-lg border border-ink/10 bg-white/40 p-4 transition hover:border-accent/60 hover:shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <Link
          href={`/jobs/${job.id}`}
          className="font-display text-lg font-medium leading-snug group-hover:text-accent"
        >
          {job.title}
        </Link>
        {job.score != null && (
          <span className="shrink-0 rounded-full bg-accent/10 px-2 py-0.5 text-xs font-semibold text-accent">
            {(job.score * 100).toFixed(0)}%
          </span>
        )}
      </div>
      <p className="mt-1 text-sm text-ink/70">
        {job.company ?? "—"}
        {job.city ? ` · ${job.city}` : ""}
      </p>
      <div className="mt-3 flex items-center justify-between text-xs">
        <span className="font-medium text-ink/60">
          {formatSalary(job.salary_min, job.salary_max)}
        </span>
        <span className="rounded bg-ink/5 px-2 py-0.5 uppercase tracking-wide text-ink/50">
          {job.source}
        </span>
      </div>
    </article>
  );
}
