import type { Metadata } from "next";
import localFont from "next/font/local";
import { Nav } from "@/components/Nav";
import "./globals.css";
import { PostHogProvider } from "./providers";

const sans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-sans",
  weight: "100 900",
});
const mono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "JobAtlas — India tech jobs, unified",
  description:
    "Search and semantically match India tech jobs aggregated across multiple job boards.",
};

// Default is light; apply dark before paint only if the user chose it.
const themeScript = `(function(){try{if(localStorage.getItem('theme')==='dark'){document.documentElement.classList.add('dark');}}catch(e){}})();`;

export default function RootLayout({
  children,
  modal,
}: {
  children: React.ReactNode;
  modal: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${sans.variable} ${mono.variable}`}
    >
      <body className="min-h-screen bg-paper text-ink antialiased">
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
        <PostHogProvider>
          <Nav />
          <main className="relative z-10 mx-auto max-w-5xl px-5 py-8">
            {children}
          </main>
          {modal}
          <footer className="relative z-10 mx-auto max-w-5xl px-5 py-10 text-xs">
            <span className="font-medium text-ink/60">
              Job<span className="text-accent">Atlas</span>
            </span>
          </footer>
        </PostHogProvider>
      </body>
    </html>
  );
}
