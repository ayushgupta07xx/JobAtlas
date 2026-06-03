"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { JobCard } from "@/components/JobCard";
import {
  searchJobs,
  getSources,
  type SearchHit,
  type SourceFacet,
} from "@/lib/api";
import { track, EVENTS } from "@/lib/analytics";

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
  const sortParam = searchParams.get("sort") ?? "relevance";
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
  const scrollRestored = useRef("");

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

  // Fetch whenever committed params change (search / filter / sort / page / back).
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

  // Save scroll position per result-set, so returning from a job restores it.
  useEffect(() => {
    const key = `home-scroll:${searchParams.toString()}`;
    let ticking = false;
    const save = () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(() => {
        sessionStorage.setItem(key, String(window.scrollY));
        ticking = false;
      });
    };
    window.addEventListener("scroll", save, { passive: true });
    return () => {
      sessionStorage.setItem(key, String(window.scrollY));
      window.removeEventListener("scroll", save);
    };
  }, [searchParams]);

  // Restore scroll once the matching result-set has loaded.
  useEffect(() => {
    const key = searchParams.toString();
    if (loading || hits.length === 0 || scrollRestored.current === key) return;
    scrollRestored.current = key;
    const saved = sessionStorage.getItem(`home-scroll:${key}`);
    if (saved) window.scrollTo(0, Number(saved) || 0);
  }, [loading, hits, searchParams]);

  function setParams(
    updates: Record<string, string | null>,
    scrollTop = false,
  ) {
    const params = new URLSearchParams(searchParams.toString());
    for (const [k, v] of Object.entries(updates)) {
      const isDefault =
        v === null ||
        v === "" ||
        (k === "sort" && v === "relevance") ||
        (k === "page" && v === "1");
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
          value={qInput}
          onChange={(e) => setQInput(e.target.value)}
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

      <div className="mb-3 flex flex-wrap items-center gap-2 text-sm">
        <span className="text-ink/50">Sort by:</span>
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

      <div className="mb-6 flex flex-wrap items-center gap-2 text-sm">
        <span className="text-ink/50">Filter:</span>
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
            className={`${pill(selectedSources.includes(s.source))} capitalize`}
          >
            {s.source}
          </button>
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
            disabled={pageParam <= 1}
            onClick={() => goPage(pageParam - 1)}
          />
          {pageWindow(pageParam, totalPages).map((p, i) =>
            typeof p === "string" ? (
              <span key={`gap-${i}`} className="px-2 text-ink/40">
                &hellip;
              </span>
            ) : (
              <PageBtn
                key={p}
                label={String(p)}
                active={p === pageParam}
                onClick={() => goPage(p)}
              />
            ),
          )}
          <PageBtn
            label="Next ›"
            disabled={pageParam >= totalPages}
            onClick={() => goPage(pageParam + 1)}
          />
        </div>
      )}
    </div>
  );
}

function pill(active: boolean): string {
  return `rounded-full border px-3 py-1 transition ${
    active
      ? "border-accent bg-accent text-paper"
      : "border-ink/15 text-ink/70 hover:border-accent"
  }`;
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
      className={`rounded-md border px-3 py-1 text-sm transition disabled:opacity-40 ${
        active
          ? "border-accent bg-accent text-paper"
          : "border-ink/15 text-ink/70 hover:border-accent"
      }`}
    >
      {label}
    </button>
  );
}
