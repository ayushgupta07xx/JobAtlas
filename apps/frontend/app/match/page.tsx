"use client";

import posthog from "posthog-js";
import { useEffect, useRef, useState, type ReactNode } from "react";

import { JobCard } from "@/components/JobCard";
import { EVENTS, track } from "@/lib/analytics";
import {
  getSources,
  matchResume,
  type SearchHit,
  type SourceFacet,
} from "@/lib/api";

const PAGE_SIZE = 24;

const SORTS = [
  { value: "relevance", label: "Best match" },
  { value: "salary", label: "Salary · High to Low" },
  { value: "recency", label: "Recency" },
];

export default function MatchPage() {
  const [file, setFile] = useState<File | null>(null);
  const [variant, setVariant] = useState<string | null>(null);
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [sort, setSort] = useState("relevance");
  const [sourceSet, setSourceSet] = useState<Set<string>>(new Set());
  const [page, setPage] = useState(1);
  const [sourceList, setSourceList] = useState<SourceFacet[]>([]);

  // Set by "Find matches" so the next fetch fires the experiment exposure;
  // pagination / sort / filter fetches do not.
  const fireExposure = useRef(false);

  const sourceCsv = Array.from(sourceSet).join(",");
  const selectedSources = Array.from(sourceSet);
  const matched = variant !== null;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const rangeStart = total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
  const rangeEnd = (page - 1) * PAGE_SIZE + hits.length;

  // Source chips (drop sources the matcher excludes).
  useEffect(() => {
    getSources()
      .then((s) => setSourceList(s.filter((x) => x.source !== "remotive")))
      .catch(() => setSourceList([]));
  }, []);

  // Fetch whenever a match is active and its params change.
  useEffect(() => {
    if (!file || !variant) return;
    let cancelled = false;
    const expose = fireExposure.current;
    fireExposure.current = false;
    setLoading(true);
    setError(null);
    const t0 = performance.now();
    matchResume(file, {
      limit: PAGE_SIZE,
      offset: (page - 1) * PAGE_SIZE,
      sort,
      source: sourceCsv || undefined,
      variant,
    })
      .then((res) => {
        if (cancelled) return;
        setHits(res.results);
        setTotal(res.total);
        if (expose) {
          const latency_ms = Math.round(performance.now() - t0);
          track(EVENTS.MATCH_REQUESTED, {
            num_matches_returned: res.results.length,
            algo_variant: variant,
            latency_ms,
          });
          if (res.results.length > 0) {
            track(EVENTS.MATCH_SCORE_REVEALED, {
              num_results: res.results.length,
              top_score: res.results[0].score ?? null,
              algo_variant: variant,
            });
          }
        }
      })
      .catch(() => {
        if (!cancelled) setError("Match failed. Is the API reachable?");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [file, variant, page, sort, sourceCsv]);

  function onPick(f: File | null) {
    setFile(f);
    setVariant(null); // require an explicit "Find matches" for a new résumé
    setHits([]);
    setTotal(0);
    setPage(1);
    setSort("relevance");
    setSourceSet(new Set());
    if (f) {
      track(EVENTS.RESUME_UPLOADED, {
        file_size_kb: Math.round(f.size / 1024),
        file_type: f.type || f.name.split(".").pop(),
      });
    }
  }

  function run() {
    if (!file) return;
    // Reading the flag fires the PostHog experiment exposure ($feature_flag_called).
    const flag = posthog.getFeatureFlag("match_algo_v2");
    fireExposure.current = true;
    setVariant(flag === "test" ? "test" : "control");
  }

  function changeSort(value: string) {
    setSort(value);
    setPage(1);
  }

  function toggleSource(src: string) {
    const set = new Set(sourceSet);
    if (set.has(src)) {
      set.delete(src);
      track(EVENTS.FILTER_CLEARED, { filter_type: "source", filter_value: src });
    } else {
      set.add(src);
      track(EVENTS.FILTER_APPLIED, { filter_type: "source", filter_value: src });
    }
    setSourceSet(set);
    setPage(1);
  }

  function clearSources() {
    if (sourceSet.size === 0) return;
    track(EVENTS.FILTER_CLEARED, { filter_type: "source" });
    setSourceSet(new Set());
    setPage(1);
  }

  function goPage(p: number) {
    if (p < 1 || p > totalPages || p === page) return;
    setPage(p);
    window.scrollTo({ top: 0, behavior: "smooth" });
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
            onChange={(e) => onPick(e.target.files?.[0] ?? null)}
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

      {loading && hits.length === 0 && (
        <p className="text-sm text-ink/50">
          First match loads the model — this can take ~10s.
        </p>
      )}
      {error && <p className="text-sm text-accent">{error}</p>}

      {matched && (
        <>
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <span className="text-sm text-ink/50">Sort by:</span>
            {SORTS.map((s) => (
              <button
                key={s.value}
                onClick={() => changeSort(s.value)}
                className={pill(sort === s.value)}
              >
                {s.label}
              </button>
            ))}
          </div>

          {sourceList.length > 0 && (
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <span className="text-sm text-ink/50">Filter:</span>
              <button
                onClick={clearSources}
                className={pill(selectedSources.length === 0)}
              >
                All
              </button>
              {sourceList.map((s) => (
                <button
                  key={s.source}
                  onClick={() => toggleSource(s.source)}
                  className={pill(selectedSources.includes(s.source))}
                >
                  {s.source.charAt(0).toUpperCase() + s.source.slice(1)}
                </button>
              ))}
            </div>
          )}

          {!loading && (
            <p className="mb-4 text-sm text-ink/50">
              {total === 0
                ? "No matches with these filters."
                : `Showing ${rangeStart}–${rangeEnd} of ${total} matches`}
            </p>
          )}
        </>
      )}

      <div className="grid gap-3 sm:grid-cols-2">
        {hits.map((job, i) => (
          <JobCard key={job.id} job={job} position={i} />
        ))}
      </div>

      {matched && totalPages > 1 && (
        <div className="mt-10 flex flex-wrap items-center justify-center gap-2">
          <PageBtn onClick={() => goPage(page - 1)} disabled={page <= 1}>
            Prev
          </PageBtn>
          {pageWindow(page, totalPages).map((p, i) =>
            p === "gap" ? (
              <span key={`g${i}`} className="px-2 text-ink/40">
                &hellip;
              </span>
            ) : (
              <PageBtn key={p} onClick={() => goPage(p)} active={p === page}>
                {p}
              </PageBtn>
            ),
          )}
          <PageBtn onClick={() => goPage(page + 1)} disabled={page >= totalPages}>
            Next
          </PageBtn>
        </div>
      )}
    </div>
  );
}

function pill(active: boolean) {
  return [
    "rounded-full border px-4 py-1.5 text-sm transition",
    active
      ? "border-accent bg-accent text-paper"
      : "border-ink/15 bg-paper text-ink/70 hover:border-ink/30",
  ].join(" ");
}

function pageWindow(current: number, totalPages: number): (number | "gap")[] {
  const out: (number | "gap")[] = [];
  const window = 1;
  const first = 1;
  const last = totalPages;
  for (let p = first; p <= last; p++) {
    if (
      p === first ||
      p === last ||
      (p >= current - window && p <= current + window)
    ) {
      out.push(p);
    } else if (out[out.length - 1] !== "gap") {
      out.push("gap");
    }
  }
  return out;
}

function PageBtn({
  children,
  onClick,
  disabled,
  active,
}: {
  children: ReactNode;
  onClick: () => void;
  disabled?: boolean;
  active?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={[
        "min-w-9 rounded-lg border px-3 py-1.5 text-sm transition",
        active
          ? "border-accent bg-accent text-paper"
          : "border-ink/15 bg-paper text-ink/70 hover:border-ink/30",
        disabled ? "cursor-not-allowed opacity-40" : "",
      ].join(" ")}
    >
      {children}
    </button>
  );
}
