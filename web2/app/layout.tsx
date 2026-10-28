import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RollWatch: every voter-roll change, explained",
  description: "RollWatch compares two versions of a voter roll, tells you which story each removal fits, checks viral claims part by part, and helps any voter find out why their name changed. Synthetic data.",
};

export const viewport: Viewport = { themeColor: "#050608" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preload" href="/fonts/Geist-Variable.woff2" as="font" type="font/woff2" crossOrigin="" />
        <link rel="preload" href="/fonts/GeistMono-Variable.woff2" as="font" type="font/woff2" crossOrigin="" />
      </head>
      <body>{children}</body>
    </html>
  );
}
