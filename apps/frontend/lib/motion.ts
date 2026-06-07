import type { Variants } from "framer-motion";

// Single shared easing — a smooth editorial ease-out. Reuse everywhere so the
// whole site shares one motion "fingerprint" instead of random per-component timing.
export const EASE = [0.22, 1, 0.36, 1] as const;

// Hero / above-the-fold reveal: gentle rise + fade.
export const fadeUp: Variants = {
  hidden: { opacity: 0, y: 14 },
  show: { opacity: 1, y: 0, transition: { duration: 0.55, ease: EASE } },
};

// Container that reveals its children one after another (hero block).
export const stagger: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.07, delayChildren: 0.05 } },
};

// Lighter/faster orchestration for the results grid (can be 24+ cards).
export const gridContainer: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.035 } },
};

export const gridItem: Variants = {
  hidden: { opacity: 0, y: 8 },
  show: { opacity: 1, y: 0, transition: { duration: 0.3, ease: EASE } },
};
