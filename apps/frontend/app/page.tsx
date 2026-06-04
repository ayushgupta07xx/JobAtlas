"use client";

import { Suspense, useEffect, useRef, useState, type ReactNode } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { JobCard } from "@/components/JobCard";
import {
  getSources,
  searchJobs,
  type SearchHit,
  type SourceFacet,
} from "@/lib/api";
import { EVENTS, track } from "@/lib/analytics";

const PAGE_SIZE = 24;

const SORTS = [
  { value: "relevance", label: "Relevance" },
  { value: "salary", label: "Salary · High to Low" },
  { value: "recency", label: "Recency" },
];

export default function HomePage() {
  return (
    <Suspense fallback={<p className="text-ink/50">Loading…</p>}>
      <HomeBody />
    </Suspense>
  );
}

function HomeBody() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const qParam = searchParams.get("q") ?? "";
  const sourceParam = searchParams.get("source") ?? "";
  const sortParam = searchParams.get("sort") ?? (qParam ? "relevance" : "salary");
  const pageParam = Math.max(
    1,
    Number.parseInt(searchParams.get("page") ?? "1", 10) || 1,
  );
  const selectedSources = sourceParam
    ? sourceParam.split(",").filter(Boolean)
    : [];

  const [qInput, setQInput] = useState(qParam);
  const [sourceList, setSourceList] = useState<SourceFacet[]>([]);
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const pendingTrigger = useRef<"query" | "filter" | null>(null);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const rangeStart = total === 0 ? 0 : (pageParam - 1) * PAGE_SIZE + 1;
  const rangeEnd = (pageParam - 1) * PAGE_SIZE + hits.length;

  // Keep the input box in sync with the URL (e.g. on back navigation).
  useEffect(() => {
    setQInput(qParam);
  }, [qParam]);

  // Load the source list for the filter (once).
  useEffect(() => {
    getSources()
      .then(setSourceList)
      .catch(() => setSourceList([]));
  }, []);

  // Fetch whenever committed params change (search / filter / sort / page).
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    searchJobs({
      q: qParam || undefined,
      source: sourceParam || undefined,
      sort: sortParam,
      limit: PAGE_SIZE,
      offset: (pageParam - 1) * PAGE_SIZE,
    })
      .then((res) => {
        if (cancelled) return;
        setHits(res.results);
        setTotal(res.total);
        const trigger = pendingTrigger.current;
        if (trigger) {
          track(EVENTS.SEARCH_EXECUTED, {
            query: qParam,
            source: sourceParam || "all",
            num_results: res.results.length,
            trigger,
          });
          if (res.results.length === 0) {
            track(EVENTS.SEARCH_RETURNED_EMPTY, {
              query: qParam,
              source: sourceParam || "all",
              trigger,
            });
          }
        }
        pendingTrigger.current = null;
      })
      .catch(() => {
        if (!cancelled) {
          setError("Could not reach the API. Please try again in a moment.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [qParam, sourceParam, sortParam, pageParam]);

  function setParams(
    updates: Record<string, string | null>,
    scrollTop = false,
  ) {
    const params = new URLSearchParams(searchParams.toString());
    for (const [k, v] of Object.entries(updates)) {
      const isDefault = v === null || v === "" || (k === "page" && v === "1");
      if (isDefault) params.delete(k);
      else params.set(k, v);
    }
    const qs = params.toString();
    router.replace(qs ? `/?${qs}` : "/", { scroll: false });
    if (scrollTop) window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function runSearch() {
    pendingTrigger.current = "query";
    setParams({ q: qInput.trim() || null, page: null });
  }

  function toggleSource(src: string) {
    const set = new Set(selectedSources);
    if (set.has(src)) {
      set.delete(src);
      track(EVENTS.FILTER_CLEARED, { filter_type: "source", filter_value: src });
    } else {
      set.add(src);
      track(EVENTS.FILTER_APPLIED, { filter_type: "source", filter_value: src });
    }
    pendingTrigger.current = "filter";
    setParams({ source: Array.from(set).join(",") || null, page: null });
  }

  function clearSources() {
    if (selectedSources.length === 0) return;
    track(EVENTS.FILTER_CLEARED, { filter_type: "source" });
    pendingTrigger.current = "filter";
    setParams({ source: null, page: null });
  }

  function changeSort(value: string) {
    setParams({ sort: value, page: null });
  }

  function goPage(p: number) {
    if (p < 1 || p > totalPages || p === pageParam) return;
    setParams({ page: String(p) }, true);
  }

  return (
    <>
      <h1 className="font-serif text-5xl font-bold leading-tight tracking-tight">
        India tech jobs,
        <br />
        <span className="text-accent">unified and matched.</span>
      </h1>
      <p className="mt-5 max-w-xl text-lg text-ink/70">
        One search across multiple job boards, deduplicated and ranked by
        semantic relevance.
      </p>

      <div className="mt-8 flex gap-3">
        <input
          value={qInput}
          onChange={(e) => setQInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") runSearch();
          }}
          placeholder="Try: data engineer in Bangalore"
          className="flex-1 rounded-xl border border-ink/15 bg-paper px-5 py-4 text-lg outline-none focus:border-accent"
        />
        <button
          onClick={runSearch}
          className="rounded-xl bg-ink px-8 py-4 text-lg font-medium text-paper hover:opacity-90"
        >
          Search
        </button>
      </div>

      <div className="mt-6 flex flex-wrap items-center gap-2">
        <span className="text-sm text-ink/50">Sort by:</span>
        {SORTS.map((s) => (
          <button
            key={s.value}
            onClick={() => changeSort(s.value)}
            className={pill(sortParam === s.value)}
          >
            {s.label}
          </button>
        ))}
      </div>

      {sourceList.length > 0 && (
        <div className="mt-3 flex flex-wrap items-center gap-2">
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

      <div className="mt-8">
        {error && <p className="text-accent">{error}</p>}

        {!error && (
          <p className="mb-4 text-sm text-ink/50">
            {loading
              ? "Loading…"
              : total === 0
                ? "No jobs match your search."
                : `Showing ${rangeStart}–${rangeEnd} of ${total} jobs`}
          </p>
        )}

        <div className="grid gap-4 sm:grid-cols-2">
          {hits.map((job) => (
            <JobCard key={job.id} job={job} />
          ))}
        </div>

        {totalPages > 1 && (
          <div className="mt-10 flex flex-wrap items-center justify-center gap-2">
            <PageBtn onClick={() => goPage(pageParam - 1)} disabled={pageParam <= 1}>
              Prev
            </PageBtn>
            {pageWindow(pageParam, totalPages).map((p, i) =>
              p === "gap" ? (
                <span key={`g${i}`} className="px-2 text-ink/40">
                  &hellip;
                </span>
              ) : (
                <PageBtn
                  key={p}
                  onClick={() => goPage(p)}
                  active={p === pageParam}
                >
                  {p}
                </PageBtn>
              ),
            )}
            <PageBtn
              onClick={() => goPage(pageParam + 1)}
              disabled={pageParam >= totalPages}
            >
              Next
            </PageBtn>
          </div>
        )}
      </div>
    </>
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
