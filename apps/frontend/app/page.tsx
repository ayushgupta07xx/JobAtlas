"use client";

import { Suspense, useEffect, useRef, useState, type ReactNode } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { animate, motion, useReducedMotion } from "framer-motion";

import { JobCard } from "@/components/JobCard";
import {
  getSources,
  searchJobs,
  type SearchHit,
  type SourceFacet,
} from "@/lib/api";
import { EVENTS, track } from "@/lib/analytics";
import { fadeUp, stagger, gridContainer } from "@/lib/motion";

const PAGE_SIZE = 24;

const SORTS = [
  { value: "relevance", label: "Relevance" },
  { value: "salary", label: "Salary · High to Low" },
  { value: "recency", label: "Recency" },
];

const PLACEHOLDERS = [
  "data engineer in Bangalore",
  "product analyst in Mumbai",
  "machine learning, remote",
  "senior backend engineer, Pune",
  "business analyst in Delhi",
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
  const reduce = useReducedMotion();

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
  const [focused, setFocused] = useState(false);
  const [phIdx, setPhIdx] = useState(0);

  const pendingTrigger = useRef<"query" | "filter" | null>(null);
  const resultsRef = useRef<HTMLDivElement>(null);
  const pendingScroll = useRef(false);

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

  // Cycle the example placeholder while the box is empty and unfocused.
  useEffect(() => {
    if (reduce || focused || qInput) return;
    const t = setInterval(
      () => setPhIdx((i) => (i + 1) % PLACEHOLDERS.length),
      2800,
    );
    return () => clearInterval(t);
  }, [reduce, focused, qInput]);

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

  // After a search from the bar, smooth-scroll down to the results once loaded.
  useEffect(() => {
    if (loading || !pendingScroll.current) return;
    pendingScroll.current = false;
    requestAnimationFrame(() => {
      resultsRef.current?.scrollIntoView({
        behavior: reduce ? "auto" : "smooth",
        block: "start",
      });
    });
  }, [loading, reduce]);

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
    pendingScroll.current = true;
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
    track(EVENTS.RESULTS_PAGINATED, {
      from: pageParam,
      to: p,
      total_pages: totalPages,
    });
    setParams({ page: String(p) }, true);
  }

  return (
    <>
      {/* ---- Hero (centered) ---- */}
      <section className="relative min-h-[calc(100vh-6rem)] pb-10 pt-8 text-center">
        <div
          className="pointer-events-none absolute inset-x-0 -top-24 mx-auto h-[420px] max-w-3xl"
          style={{
            background:
              "radial-gradient(ellipse at top, var(--glow), transparent 70%)",
          }}
        />

        <motion.div
          variants={stagger}
          initial={reduce ? false : "hidden"}
          animate="show"
          className="relative z-10 mx-auto max-w-2xl"
        >
          <motion.p
            variants={fadeUp}
            className="mb-6 text-xs font-medium uppercase tracking-[0.2em] text-accent"
          >
            Unified India tech job search
          </motion.p>

          <h1 className="text-5xl font-semibold leading-[1.05] tracking-tight sm:text-6xl">
            <motion.span variants={fadeUp} className="block">
              India tech jobs,
            </motion.span>
            <motion.span variants={fadeUp} className="block">
              unified and matched.
            </motion.span>
          </h1>

          <motion.p
            variants={fadeUp}
            className="mx-auto mt-6 max-w-lg text-lg leading-relaxed text-ink/55"
          >
            One search across multiple job boards, deduplicated and ranked by
            semantic relevance.
          </motion.p>

          <motion.div variants={fadeUp} className="mt-8 flex gap-3">
            <input
              value={qInput}
              onChange={(e) => setQInput(e.target.value)}
              onFocus={() => setFocused(true)}
              onBlur={() => setFocused(false)}
              onKeyDown={(e) => {
                if (e.key === "Enter") runSearch();
              }}
              placeholder={`Try: ${PLACEHOLDERS[phIdx]}`}
              className="flex-1 rounded-xl border border-line bg-paper-raised px-5 py-4 text-lg text-ink outline-none transition placeholder:text-ink/35 focus:border-accent focus:shadow-[0_0_0_3px_var(--accent-soft)]"
            />
            <button
              onClick={runSearch}
              className="rounded-xl bg-accent px-7 py-4 text-lg font-medium text-on-accent shadow-[0_4px_14px_-6px_var(--glow-accent)] transition-all duration-200 hover:-translate-y-0.5 hover:brightness-105 hover:shadow-[0_12px_32px_-8px_var(--glow-accent)] active:translate-y-0 active:scale-[0.98]"
            >
              Search
            </button>
          </motion.div>
        </motion.div>

        {/* stat row */}
        <motion.div
          variants={fadeUp}
          initial={reduce ? false : "hidden"}
          animate="show"
          className="relative z-10 mt-12 flex flex-wrap items-start justify-center gap-x-14 gap-y-8"
        >
          <Stat value={10000} suffix="+" label="postings processed" />
          <Stat value={8} label="sources unified" />
          <Stat value={380} suffix="+" label="semantic dimensions" />
        </motion.div>
      </section>

      {/* ---- Results label ---- */}
      <div ref={resultsRef} className="mt-12 flex items-center gap-3 scroll-mt-24">
        <span className="text-xs uppercase tracking-[0.18em] text-ink/35">
          Results
        </span>
        <span className="h-px flex-1 bg-line" />
      </div>

      {/* ---- Sort ---- */}
      <div className="mt-5 flex flex-wrap items-center gap-2">
        <span className="text-sm text-ink/45">Sort by:</span>
        {SORTS.map((s) => {
          const active = sortParam === s.value;
          return (
            <button
              key={s.value}
              onClick={() => changeSort(s.value)}
              className={`relative rounded-full border px-4 py-1.5 text-sm transition-colors ${
                active
                  ? "border-accent text-on-accent"
                  : "border-line text-ink/65 hover:border-line-strong hover:text-ink"
              }`}
            >
              {active && (
                <motion.span
                  layoutId="sortPill"
                  className="absolute inset-0 rounded-full bg-accent"
                  transition={
                    reduce
                      ? { duration: 0 }
                      : { type: "spring", stiffness: 380, damping: 32 }
                  }
                />
              )}
              <span className="relative z-10">{s.label}</span>
            </button>
          );
        })}
      </div>

      {/* ---- Filter ---- */}
      {sourceList.length > 0 && (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <span className="text-sm text-ink/45">Filter:</span>
          <motion.button
            whileTap={{ scale: 0.95 }}
            onClick={clearSources}
            className={pill(selectedSources.length === 0)}
          >
            All
          </motion.button>
          {sourceList.map((s) => (
            <motion.button
              key={s.source}
              whileTap={{ scale: 0.95 }}
              onClick={() => toggleSource(s.source)}
              className={pill(selectedSources.includes(s.source))}
            >
              {s.source.charAt(0).toUpperCase() + s.source.slice(1)}
            </motion.button>
          ))}
        </div>
      )}

      {/* ---- Results ---- */}
      <div className="mt-8">
        {error && <p className="text-accent">{error}</p>}

        {!error && (
          <p className="mb-4 text-sm text-ink/45">
            {loading
              ? "Loading…"
              : total === 0
                ? "No jobs match your search."
                : `Showing ${rangeStart}–${rangeEnd} of ${total} jobs`}
          </p>
        )}

        {hits.length > 0 && (
          <motion.div
            key={`${qParam}|${sourceParam}|${sortParam}|${pageParam}`}
            variants={gridContainer}
            initial={reduce ? false : "hidden"}
            animate="show"
            className="grid gap-4 sm:grid-cols-2"
          >
            {hits.map((job, i) => (
              <JobCard
                key={job.id}
                job={job}
                position={(pageParam - 1) * PAGE_SIZE + i + 1}
              />
            ))}
          </motion.div>
        )}

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

function Stat({
  value,
  label,
  suffix = "",
}: {
  value: number;
  label: string;
  suffix?: string;
}) {
  const reduce = useReducedMotion();
  const [n, setN] = useState(reduce ? value : 0);
  useEffect(() => {
    if (reduce) {
      setN(value);
      return;
    }
    const controls = animate(0, value, {
      duration: 1.2,
      ease: [0.22, 1, 0.36, 1],
      onUpdate: (v) => setN(v),
    });
    return () => controls.stop();
  }, [value, reduce]);
  return (
    <div className="text-center">
      <div className="text-2xl font-semibold tabular-nums tracking-tight">
        {Math.round(n).toLocaleString("en-US")}
        {suffix}
      </div>
      <div className="mt-1 text-sm text-ink/45">{label}</div>
    </div>
  );
}

function pill(active: boolean) {
  return [
    "rounded-full border px-4 py-1.5 text-sm transition-colors",
    active
      ? "border-accent bg-accent text-on-accent"
      : "border-line bg-paper-raised text-ink/65 hover:border-line-strong hover:text-ink",
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
        "min-w-9 rounded-lg border px-3 py-1.5 text-sm transition-colors",
        active
          ? "border-accent bg-accent text-on-accent"
          : "border-line bg-paper-raised text-ink/65 hover:border-line-strong hover:text-ink",
        disabled ? "cursor-not-allowed opacity-40" : "active:scale-[0.97]",
      ].join(" ")}
    >
      {children}
    </button>
  );
}
