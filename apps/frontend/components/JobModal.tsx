"use client";

import DOMPurify from "dompurify";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { EVENTS, track } from "@/lib/analytics";
import { formatSalary, getJob, type JobDetail } from "@/lib/api";

export function JobModal({ id }: { id: string }) {
  const router = useRouter();
  const [job, setJob] = useState<JobDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getJob(id)
      .then((j) => {
        if (cancelled) return;
        setJob(j);
        track(EVENTS.JOB_DETAIL_OPENED, { job_id: j.id, source: j.source });
      })
      .catch(() => {
        if (!cancelled) setError("Job not found.");
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  // Close on Escape.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") router.back();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [router]);

  // Lock the page behind the modal from scrolling.
  useEffect(() => {
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, []);

  function close() {
    router.back();
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-ink/40 px-4 py-10 backdrop-blur-sm"
      onClick={close}
    >
      <div
        className="relative w-full max-w-2xl rounded-2xl border border-ink/10 bg-paper p-7 shadow-xl sm:p-9"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={close}
          aria-label="Close"
          className="absolute right-4 top-4 rounded-full p-1.5 text-ink/40 transition hover:bg-ink/5 hover:text-accent"
        >
          ✕
        </button>

        {error ? (
          <p className="text-accent">{error}</p>
        ) : !job ? (
          <p className="text-ink/50">Loading…</p>
        ) : (
          <article>
            <h1 className="pr-8 font-display text-3xl font-semibold leading-tight sm:text-4xl">
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
            {job.description &&
              (job.description.includes("</") ? (
                <div
                  className="mt-6 space-y-3 leading-relaxed text-ink/80"
                  dangerouslySetInnerHTML={{
                    __html: DOMPurify.sanitize(job.description),
                  }}
                />
              ) : (
                <div className="mt-6 whitespace-pre-line leading-relaxed text-ink/80">
                  {job.description}
                </div>
              ))}
            <a
              href={job.source_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={() =>
                track(EVENTS.APPLY_CLICKED, {
                  job_id: job.id,
                  source: job.source,
                })
              }
              className="mt-8 inline-block rounded-lg bg-ink px-6 py-3 font-medium text-paper transition hover:bg-accent"
            >
              Apply on {job.source} →
            </a>
          </article>
        )}
      </div>
    </div>
  );
}
