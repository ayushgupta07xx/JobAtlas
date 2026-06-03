"use client";

import { useEffect, useRef, useState } from "react";

import { JobCard } from "@/components/JobCard";
import {
  searchJobs,
  getSources,
  type SearchHit,
  type SourceFacet,
} from "@/lib/api";
import { track, EVENTS } from "@/lib/analytics";

const PAGE_SIZE = 24;

export default function HomePage() {
  const [q, setQ] = useState("");
  const [committedQ, setCommittedQ] = useState("");
  const [source, setSource] = useState<string | null>(null);
  const [sources, setSources] = useState<SourceFacet[]>([]);
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  async function fetchPage(opts: {
    query: string;
    src: string | null;
    page: number;
    trigger?: "query" | "filter";
  }) {
    setLoading(true);
    setError(null);
    try {
      const res = await searchJobs({
        q: opts.query || undefined,
        source: opts.src || undefined,
        limit: PAGE_SIZE,
        offset: (opts.page - 1) * PAGE_SIZE,
      });
      setHits(res.results);
      setTotal(res.total);
      if (opts.trigger) {
        track(EVENTS.SEARCH_EXECUTED, {
          query: opts.query,
          source: opts.src ?? "all",
          num_results: res.results.length,
          trigger: opts.trigger,
        });
        if (res.results.length === 0) {
          track(EVENTS.SEARCH_RETURNED_EMPTY, {
            query: opts.query,
            source: opts.src ?? "all",
            trigger: opts.trigger,
          });
        }
      }
    } catch {
      setError("Could not reach the API. Please try again in a moment.");
    } finally {
      setLoading(false);
    }
  }

  // Initial load: first page of jobs + the source list for the filter chips.
  const firstLoad = useRef(true);
  useEffect(() => {
    if (!firstLoad.current) return;
    firstLoad.current = false;
    fetchPage({ query: "", src: null, page: 1 });
    getSources()
      .then(setSources)
      .catch(() => setSources([]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function runSearch() {
    setCommittedQ(q);
    setPage(1);
    fetchPage({ query: q, src: source, page: 1, trigger: "query" });
  }

  function applySource(next: string | null) {
    if (next === null) {
      track(EVENTS.FILTER_CLEARED, { filter_type: "source" });
    } else {
      track(EVENTS.FILTER_APPLIED, {
        filter_type: "source",
        filter_value: next,
      });
    }
    setSource(next);
    setPage(1);
    fetchPage({ query: committedQ, src: next, page: 1, trigger: "filter" });
  }

  function goPage(p: number) {
    if (p < 1 || p > totalPages || p === page) return;
    setPage(p);
    if (typeof window !== "undefined") {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
    fetchPage({ query: committedQ, src: source, page: p });
  }

  const rangeStart = total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
  const rangeEnd = (page - 1) * PAGE_SIZE + hits.length;

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
          onKeyDown={(e) => e.key === "Enter" && runSearch()}
          placeholder="Try: data engineer in Bangalore"
          className="flex-1 rounded-lg border border-ink/15 bg-white/60 px-4 py-3 outline-none focus:border-accent"
        />
        <button
          onClick={runSearch}
          className="rounded-lg bg-ink px-6 py-3 font-medium text-paper transition hover:bg-accent"
        >
          Search
        </button>
      </div>

      <div className="mb-6 flex flex-wrap gap-2">
        <Chip
          label="All"
          active={source === null}
          onClick={() => applySource(null)}
        />
        {sources.map((s) => (
          <Chip
            key={s.source}
            label={s.source}
            active={source === s.source}
            onClick={() => applySource(s.source)}
          />
        ))}
      </div>

      {error && <p className="mb-3 text-sm text-accent">{error}</p>}

      {!loading && total > 0 && (
        <p className="mb-3 text-sm text-ink/50">
          Showing {rangeStart.toLocaleString()}&ndash;{rangeEnd.toLocaleString()}{" "}
          of {total.toLocaleString()} jobs
        </p>
      )}

      {loading ? (
        <p className="text-ink/50">Searching&hellip;</p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {hits.map((job, i) => (
            <JobCard key={job.id} job={job} position={i} />
          ))}
        </div>
      )}

      {!loading && totalPages > 1 && (
        <div className="mt-8 flex flex-wrap items-center justify-center gap-1">
          <PageBtn
            label="‹ Prev"
            disabled={page <= 1}
            onClick={() => goPage(page - 1)}
          />
          {pageWindow(page, totalPages).map((p, i) =>
            typeof p === "string" ? (
              <span key={`gap-${i}`} className="px-2 text-ink/40">
                &hellip;
              </span>
            ) : (
              <PageBtn
                key={p}
                label={String(p)}
                active={p === page}
                onClick={() => goPage(p)}
              />
            ),
          )}
          <PageBtn
            label="Next ›"
            disabled={page >= totalPages}
            onClick={() => goPage(page + 1)}
          />
        </div>
      )}
    </div>
  );
}

function pageWindow(current: number, totalPages: number): (number | "gap")[] {
  const out: (number | "gap")[] = [1];
  const lo = Math.max(2, current - 2);
  const hi = Math.min(totalPages - 1, current + 2);
  if (lo > 2) out.push("gap");
  for (let n = lo; n <= hi; n++) out.push(n);
  if (hi < totalPages - 1) out.push("gap");
  if (totalPages > 1) out.push(totalPages);
  return out;
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
      className={`rounded-full border px-3 py-1 text-sm capitalize transition ${active
        ? "border-accent bg-accent text-paper"
        : "border-ink/15 text-ink/70 hover:border-accent"
        }`}
    >
      {label}
    </button>
  );
}

function PageBtn({
  label,
  active,
  disabled,
  onClick,
}: {
  label: string;
  active?: boolean;
  disabled?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`rounded-md border px-3 py-1 text-sm transition disabled:opacity-40 ${active
        ? "border-accent bg-accent text-paper"
        : "border-ink/15 text-ink/70 hover:border-accent"
        }`}
    >
      {label}
    </button>
  );
}
