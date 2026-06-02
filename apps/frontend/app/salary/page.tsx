"use client";

import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { salaryTrend, type SalaryRow } from "@/lib/api";

export default function SalaryPage() {
  const [rows, setRows] = useState<SalaryRow[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    salaryTrend(12)
      .then((res) => setRows(res.rows))
      .catch(() => setError("Could not load salary data."));
  }, []);

  const data = rows.map((r) => ({
    city: r.city,
    "Avg min": r.avg_salary_min ? Math.round(r.avg_salary_min / 100000) : 0,
    "Avg max": r.avg_salary_max ? Math.round(r.avg_salary_max / 100000) : 0,
  }));

  return (
    <div>
      <section className="mb-8">
        <h1 className="font-display text-4xl font-semibold tracking-tight">
          Salary <span className="text-accent">explorer</span>
        </h1>
        <p className="mt-3 max-w-xl text-ink/60">
          Average disclosed salary range by city (₹ lakhs per annum) across
          indexed roles.
        </p>
      </section>

      {error && <p className="text-sm text-accent">{error}</p>}

      <div className="rounded-lg border border-ink/10 bg-white/40 p-4">
        <ResponsiveContainer width="100%" height={420}>
          <BarChart
            data={data}
            margin={{ top: 8, right: 8, bottom: 70, left: 8 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(22,19,15,0.08)" />
            <XAxis
              dataKey="city"
              angle={-40}
              textAnchor="end"
              interval={0}
              height={70}
              tick={{ fontSize: 12, fill: "#16130f" }}
            />
            <YAxis unit="L" tick={{ fontSize: 12, fill: "#16130f" }} />
            <Tooltip formatter={(value) => `₹${value}L`} />
            <Bar dataKey="Avg min" fill="#16130f" radius={[3, 3, 0, 0]} />
            <Bar dataKey="Avg max" fill="#e8492b" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
