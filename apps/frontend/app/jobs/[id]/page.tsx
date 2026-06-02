"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { formatSalary, getJob, type JobDetail } from "@/lib/api";

export default function JobDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const [job, setJob] = useState<JobDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getJob(params.id)
      .then(setJob)
      .catch(() => setError("Job not found."));
  }, [params.id]);

  if (error) {
    return (
      <div>
        <p className="text-accent">{error}</p>
        <Link href="/" className="mt-4 inline-block text-sm underline">
          ← Back to search
        </Link>
      </div>
    );
  }

  if (!job) return <p className="text-ink/50">Loading…</p>;

  return (
    <article>
      <Link href="/" className="text-sm text-ink/50 hover:text-accent">
        ← Back to search
      </Link>
      <h1 className="mt-4 font-display text-3xl font-semibold leading-tight sm:text-4xl">
        {job.title}
      </h1>
      <p className="mt-2 text-lg text-ink/70">
        {job.company ?? "—"}
        {job.city ? ` · ${job.city}` : ""}
        {job.state ? `, ${job.state}` : ""}
      </p>

      <div className="mt-5 flex flex-wrap items-center gap-3 text-sm">
        <span className="rounded-lg bg-accent/10 px-3 py-1 font-medium text-accent">
          {formatSalary(job.salary_min, job.salary_max)}
        </span>
        <span className="rounded-lg bg-ink/5 px-3 py-1 uppercase tracking-wide text-ink/60">
          {job.source}
        </span>
        {job.posted_date && (
          <span className="text-ink/50">Posted {job.posted_date}</span>
        )}
      </div>

      {job.skills && job.skills.length > 0 && (
        <div className="mt-5 flex flex-wrap gap-2">
          {job.skills.map((s) => (
            <span
              key={s}
              className="rounded-full border border-ink/15 px-3 py-1 text-xs text-ink/70"
            >
              {s}
            </span>
          ))}
        </div>
      )}

      {job.description && (
        <div className="mt-6 max-w-2xl whitespace-pre-line leading-relaxed text-ink/80">
          {job.description}
        </div>
      )}

      <a
        href={job.source_url}
        target="_blank"
        rel="noopener noreferrer"
        className="mt-8 inline-block rounded-lg bg-ink px-6 py-3 font-medium text-paper transition hover:bg-accent"
      >
        Apply on {job.source} →
      </a>
    </article>
  );
}
