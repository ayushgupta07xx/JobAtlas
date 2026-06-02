"use client";

import { useEffect, useState } from "react";

import { JobCard } from "@/components/JobCard";
import { searchJobs, type SearchHit } from "@/lib/api";

const SOURCES = ["adzuna", "jobicy"];

export default function HomePage() {
  const [q, setQ] = useState("");
  const [source, setSource] = useState<string | null>(null);
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setLoading(true);
    setError(null);
    try {
      const res = await searchJobs({
        q: q || undefined,
        source: source || undefined,
        limit: 24,
      });
      setHits(res.results);
    } catch {
      setError("Could not reach the API. Is it running on :8000?");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [source]);

  return (
    <div>
      <section className="mb-8">
        <h1 className="font-display text-4xl font-semibold leading-tight tracking-tight sm:text-5xl">
          India tech jobs,
          <br />
          <span className="text-accent">unified and matched.</span>
        </h1>
        <p className="mt-3 max-w-xl text-ink/60">
          One search across multiple job boards, deduplicated and ranked by
          semantic relevance.
        </p>
      </section>

      <div className="mb-5 flex flex-col gap-3 sm:flex-row">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && run()}
          placeholder="Try: data engineer in Bangalore"
          className="flex-1 rounded-lg border border-ink/15 bg-white/60 px-4 py-3 outline-none focus:border-accent"
        />
        <button
          onClick={run}
          className="rounded-lg bg-ink px-6 py-3 font-medium text-paper transition hover:bg-accent"
        >
          Search
        </button>
      </div>

      <div className="mb-6 flex flex-wrap gap-2">
        <Chip label="All" active={source === null} onClick={() => setSource(null)} />
        {SOURCES.map((s) => (
          <Chip
            key={s}
            label={s}
            active={source === s}
            onClick={() => setSource(s)}
          />
        ))}
      </div>

      {error && <p className="text-sm text-accent">{error}</p>}
      {loading ? (
        <p className="text-ink/50">Searching…</p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {hits.map((job) => (
            <JobCard key={job.id} job={job} />
          ))}
        </div>
      )}
    </div>
  );
}

function Chip({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`rounded-full border px-3 py-1 text-sm capitalize transition ${
        active
          ? "border-accent bg-accent text-paper"
          : "border-ink/15 text-ink/70 hover:border-accent"
      }`}
    >
      {label}
    </button>
  );
}
