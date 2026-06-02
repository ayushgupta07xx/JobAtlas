import type { Metadata } from "next";
import { Fraunces, Hanken_Grotesk } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const display = Fraunces({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["400", "500", "600", "700"],
});

const body = Hanken_Grotesk({
  subsets: ["latin"],
  variable: "--font-body",
});

export const metadata: Metadata = {
  title: "JobAtlas — India tech jobs, unified",
  description:
    "Search and semantically match India tech jobs aggregated across multiple job boards.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${display.variable} ${body.variable}`}>
      <body className="min-h-screen bg-paper text-ink antialiased">
        <header className="border-b border-ink/10">
          <nav className="mx-auto flex max-w-5xl items-center justify-between px-5 py-4">
            <Link
              href="/"
              className="font-display text-xl font-semibold tracking-tight"
            >
              Job<span className="text-accent">Atlas</span>
            </Link>
            <div className="flex items-center gap-5 text-sm font-medium">
              <Link href="/" className="hover:text-accent">
                Search
              </Link>
              <Link href="/match" className="hover:text-accent">
                Match
              </Link>
              <Link href="/salary" className="hover:text-accent">
                Salaries
              </Link>
            </div>
          </nav>
        </header>
        <main className="mx-auto max-w-5xl px-5 py-8">{children}</main>
        <footer className="mx-auto max-w-5xl px-5 py-10 text-xs text-ink/40">
          JobAtlas · unified India tech job search
        </footer>
      </body>
    </html>
  );
}
