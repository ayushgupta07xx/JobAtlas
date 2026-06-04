"use client";

import { JobModal } from "@/components/JobModal";

export default function InterceptedJobPage({
  params,
}: {
  params: { id: string };
}) {
  return <JobModal id={params.id} />;
}
