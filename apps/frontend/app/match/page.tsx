"use client";

import { useState } from "react";

import { JobCard } from "@/components/JobCard";
import { matchResume, type SearchHit } from "@/lib/api";
import { track, EVENTS } from "@/lib/analytics";

export default function MatchPage() {
  const [file, setFile] = useState<File | null>(null);
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const res = await matchResume(file, 12);
      setHits(res.results);
      track(EVENTS.MATCH_REQUESTED, {
        num_matches_returned: res.results.length,
      });
      if (res.results.length > 0) {
        track(EVENTS.MATCH_SCORE_REVEALED, {
          num_results: res.results.length,
          top_score: res.results[0].score ?? null,
        });
      }
    } catch {
      setError("Match failed. Is the API running on :8000?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <section className="mb-8">
        <h1 className="font-display text-4xl font-semibold tracking-tight">
          Match your <span className="text-accent">résumé</span>
        </h1>
        <p className="mt-3 max-w-xl text-ink/60">
          Upload a PDF or text résumé. We embed it with BGE-small and rank the
          closest roles by semantic similarity.
        </p>
      </section>

      <div className="mb-6 flex flex-col items-start gap-3 sm:flex-row sm:items-center">
        <label className="cursor-pointer rounded-lg border border-dashed border-ink/30 bg-white/50 px-4 py-3 text-sm hover:border-accent">
          {file ? file.name : "Choose résumé (.pdf or .txt)"}
          <input
            type="file"
            accept=".pdf,.txt"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0] ?? null;
              setFile(f);
              if (f) {
                track(EVENTS.RESUME_UPLOADED, {
                  file_size_kb: Math.round(f.size / 1024),
                  file_type: f.type || f.name.split(".").pop(),
                });
              }
            }}
          />
        </label>
        <button
          onClick={run}
          disabled={!file || loading}
          className="rounded-lg bg-ink px-6 py-3 font-medium text-paper transition hover:bg-accent disabled:opacity-40"
        >
          {loading ? "Matching…" : "Find matches"}
        </button>
      </div>

      {loading && (
        <p className="text-sm text-ink/50">
          First match loads the model — this can take ~10s.
        </p>
      )}
      {error && <p className="text-sm text-accent">{error}</p>}

      <div className="grid gap-3 sm:grid-cols-2">
        {hits.map((job, i) => (
          <JobCard key={job.id} job={job} position={i} />
        ))}
      </div>
    </div>
  );
}
