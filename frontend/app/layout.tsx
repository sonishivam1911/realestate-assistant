import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CMA Assistant",
  description: "Consumer Market Analysis — OpenRouter + LangGraph",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
