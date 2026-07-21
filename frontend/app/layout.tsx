import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = { title: "AI Algebra Coach", description: "Socratic feedback for algebra homework." };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
