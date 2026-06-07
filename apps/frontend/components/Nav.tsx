"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, useReducedMotion } from "framer-motion";

import { track, EVENTS } from "@/lib/analytics";
import { ThemeToggle } from "@/components/ThemeToggle";

const NAV_LINKS = [
  { href: "/", label: "Search" },
  { href: "/match", label: "Match" },
  { href: "/salary", label: "Salaries" },
  { href: "/about", label: "About" },
];

export function Nav() {
  const pathname = usePathname();
  const reduce = useReducedMotion();

  return (
    <header className="sticky top-0 z-30 border-b border-line bg-[var(--nav-bg)] backdrop-blur-md">
      <nav className="mx-auto flex max-w-5xl items-center justify-between px-5 py-4">
        <Link
          href="/"
          onClick={() =>
            track(EVENTS.NAV_LINK_CLICKED, { destination: "/", label: "home" })
          }
          className="text-lg font-semibold tracking-tight"
        >
          Job<span className="text-accent">Atlas</span>
        </Link>

        <div className="flex items-center gap-1 text-sm font-medium">
          <ThemeToggle />
          <span className="mx-2 h-4 w-px bg-line" />
          {NAV_LINKS.map((l) => {
            const active =
              l.href === "/" ? pathname === "/" : pathname.startsWith(l.href);
            return (
              <Link
                key={l.href}
                href={l.href}
                onClick={() =>
                  track(EVENTS.NAV_LINK_CLICKED, {
                    destination: l.href,
                    label: l.label,
                  })
                }
                className={`relative rounded-full px-3 py-1.5 transition-colors ${
                  active ? "text-ink" : "text-ink/55 hover:text-ink"
                }`}
              >
                {l.label}
                {active && (
                  <motion.span
                    layoutId="navUnderline"
                    className="absolute inset-x-3 -bottom-px h-0.5 rounded-full bg-accent"
                    transition={
                      reduce
                        ? { duration: 0 }
                        : { type: "spring", stiffness: 380, damping: 32 }
                    }
                  />
                )}
              </Link>
            );
          })}
        </div>
      </nav>
    </header>
  );
}
