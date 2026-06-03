"use client";

import Link from "next/link";
import { track, EVENTS } from "@/lib/analytics";

const NAV_LINKS = [
  { href: "/", label: "Search" },
  { href: "/match", label: "Match" },
  { href: "/salary", label: "Salaries" },
];

export function Nav() {
  return (
    <header className="border-b border-ink/10">
      <nav className="mx-auto flex max-w-5xl items-center justify-between px-5 py-4">
        <Link
          href="/"
          onClick={() =>
            track(EVENTS.NAV_LINK_CLICKED, { destination: "/", label: "home" })
          }
          className="font-display text-xl font-semibold tracking-tight"
        >
          Job<span className="text-accent">Atlas</span>
        </Link>
        <div className="flex items-center gap-5 text-sm font-medium">
          {NAV_LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              onClick={() =>
                track(EVENTS.NAV_LINK_CLICKED, {
                  destination: l.href,
                  label: l.label,
                })
              }
              className="hover:text-accent"
            >
              {l.label}
            </Link>
          ))}
        </div>
      </nav>
    </header>
  );
}
