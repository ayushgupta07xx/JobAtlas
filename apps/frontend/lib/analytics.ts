import posthog from "posthog-js";

// JobAtlas event taxonomy — 24 events.
// JobAtlas.md §14 defined 9; expanded here to the §16 contract (24 events).
export const EVENTS = {
  // Search & discovery
  SEARCH_EXECUTED: "search_executed",
  SEARCH_RETURNED_EMPTY: "search_returned_empty",
  FILTER_APPLIED: "filter_applied",
  FILTER_CLEARED: "filter_cleared",
  RESULTS_PAGINATED: "results_paginated",
  // Job interactions
  JOB_VIEWED: "job_viewed",
  JOB_DETAIL_OPENED: "job_detail_opened",
  JOB_SAVED: "job_saved",
  JOB_UNSAVED: "job_unsaved",
  JOB_SHARE_CLICKED: "job_share_clicked",
  // Match flow
  RESUME_UPLOADED: "resume_uploaded",
  RESUME_PARSE_FAILED: "resume_parse_failed",
  MATCH_REQUESTED: "match_requested",
  MATCH_SCORE_REVEALED: "match_score_revealed",
  MATCH_RESULTS_FILTERED: "match_results_filtered",
  MATCH_FEEDBACK_SUBMITTED: "match_feedback_submitted",
  // Apply
  APPLY_CLICKED: "apply_clicked",
  EXTERNAL_APPLY_REDIRECTED: "external_apply_redirected",
  // Salary explorer
  SALARY_EXPLORER_VIEWED: "salary_explorer_viewed",
  SALARY_FILTER_CHANGED: "salary_filter_changed",
  // Lifecycle & nav
  NAV_LINK_CLICKED: "nav_link_clicked",
  SIGNUP_MODAL_OPENED: "signup_modal_opened",
  USER_SIGNED_UP: "user_signed_up",
  USER_RETURNED: "user_returned",
} as const;

export type EventName = (typeof EVENTS)[keyof typeof EVENTS];

export function track(event: EventName, props?: Record<string, unknown>) {
  if (typeof window === "undefined") return;
  posthog.capture(event, props);
}

export function identifyUser(id: string, props?: Record<string, unknown>) {
  if (typeof window === "undefined") return;
  posthog.identify(id, props);
}

export function resetUser() {
  if (typeof window === "undefined") return;
  posthog.reset();
}
