const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface Job {
  id: number;
  title: string;
  company: string | null;
  city: string | null;
  state: string | null;
  country: string | null;
  source: string;
  source_url: string;
  salary_min: number | null;
  salary_max: number | null;
  currency: string | null;
  posted_date: string | null;
  skills: string[] | null;
  scraped_at: string | null;
}

export interface JobDetail extends Job {
  description: string | null;
}

export interface SearchHit extends Job {
  score: number | null;
}

export interface SearchResponse {
  count: number;
  query: string | null;
  results: SearchHit[];
}

export interface SalaryRow {
  city: string;
  job_count: number;
  avg_salary_min: number | null;
  avg_salary_max: number | null;
}

export interface SalaryResponse {
  count: number;
  rows: SalaryRow[];
}

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json() as Promise<T>;
}

export function searchJobs(params: {
  q?: string;
  city?: string;
  source?: string;
  salary_min?: number;
  limit?: number;
}): Promise<SearchResponse> {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== "") qs.set(k, String(v));
  });
  return getJSON<SearchResponse>(`/search?${qs.toString()}`);
}

export function getJob(id: number | string): Promise<JobDetail> {
  return getJSON<JobDetail>(`/jobs/${id}`);
}

export function salaryTrend(limit = 12): Promise<SalaryResponse> {
  return getJSON<SalaryResponse>(`/analytics/salary-trend?limit=${limit}`);
}

export async function matchResume(
  file: File,
  limit = 10,
): Promise<SearchResponse> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/match?limit=${limit}`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json() as Promise<SearchResponse>;
}

export function formatSalary(
  min: number | null,
  max: number | null,
): string {
  const lakh = (n: number) => `₹${(n / 100000).toFixed(1)}L`;
  if (min && max) return `${lakh(min)}–${lakh(max)}`;
  if (max) return `up to ${lakh(max)}`;
  if (min) return `from ${lakh(min)}`;
  return "Not disclosed";
}
