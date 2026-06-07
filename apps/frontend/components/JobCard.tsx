"use client";

import Link from "next/link";
import { motion } from "framer-motion";

import { formatSalary, type SearchHit } from "@/lib/api";
import { track, EVENTS } from "@/lib/analytics";
import { gridItem } from "@/lib/motion";

export function JobCard({
  job,
  position,
}: {
  job: SearchHit;
  position?: number;
}) {
  return (
    <motion.article
      variants={gridItem}
      whileHover={{ y: -3 }}
      transition={{ type: "spring", stiffness: 300, damping: 26 }}
      className="group rounded-xl border border-line bg-paper-raised p-5 shadow-card transition-[box-shadow,border-color,background-color] duration-300 hover:border-accent/40 hover:bg-paper-overlay hover:shadow-lift"
    >
      <div className="flex items-start justify-between gap-3">
        <Link
          href={`/jobs/${job.id}`}
          onClick={() =>
            track(EVENTS.JOB_VIEWED, {
              job_id: job.id,
              source: job.source,
              position_in_list: position,
              score: job.score ?? null,
            })
          }
          className="font-display text-lg font-medium leading-snug transition-colors group-hover:text-accent"
        >
          {job.title}
        </Link>
        {job.score != null && (
          <span className="shrink-0 rounded-full bg-accent-soft px-2 py-0.5 font-mono text-xs font-medium text-accent">
            {(job.score * 100).toFixed(0)}%
          </span>
        )}
      </div>

      <p className="mt-1 text-sm text-ink/55">
        {job.company ?? "—"}
        {job.city ? ` · ${job.city}` : ""}
      </p>

      <div className="mt-4 flex items-center justify-between border-t border-line pt-3 font-mono text-xs">
        <span className="text-ink/70">
          {formatSalary(job.salary_min, job.salary_max)}
        </span>
        <span className="rounded bg-ink/5 px-2 py-0.5 uppercase tracking-wide text-ink/45">
          {job.source}
        </span>
      </div>
    </motion.article>
  );
}
