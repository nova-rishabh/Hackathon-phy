import type { Metadata } from "next";
import "./globals.css";
import Shell from "@/components/Shell";

const SITE = process.env.NEXT_PUBLIC_SITE_URL || "https://rollwatch-web.onrender.com";
const TITLE = "RollWatch: every voter-roll change, explained";
const DESC = "Which story fits each removal, how sure we are, and the rumour about it checked part by part. "
  + "Hindi, English and Punjabi, on WhatsApp and the web. Synthetic demo district.";

export const metadata: Metadata = {
  metadataBase: new URL(SITE),
  title: { default: TITLE, template: "%s · RollWatch" },
  description: DESC,
  openGraph: {
    type: "website", url: "/", siteName: "RollWatch", title: TITLE, description: DESC, locale: "en_IN",
    images: [{ url: "/og.png", width: 1200, height: 630, alt: "RollWatch: every change to a voter roll, explained" }],
  },
  twitter: { card: "summary_large_image", title: TITLE, description: DESC, images: ["/og.png"] },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body><Shell>{children}</Shell></body>
    </html>
  );
}
