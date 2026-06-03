import type { Metadata } from "next";
import { Fraunces, Hanken_Grotesk } from "next/font/google";
import { Nav } from "@/components/Nav";
import "./globals.css";
import { PostHogProvider } from "./providers";

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
        <PostHogProvider>
        <Nav />
        <main className="mx-auto max-w-5xl px-5 py-8">{children}</main>
        <footer className="mx-auto max-w-5xl px-5 py-10 text-xs text-ink/40">
          JobAtlas · unified India tech job search
        </footer>
        </PostHogProvider>
      </body>
    </html>
  );
}
