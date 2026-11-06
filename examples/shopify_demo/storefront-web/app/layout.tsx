// Copyright 2026 Anthropic PBC
// SPDX-License-Identifier: Apache-2.0

import type { Metadata } from "next";
import { Outfit } from "next/font/google";
import "./globals.css";
import "./brand-theme.css";

const brandFont = Outfit({
  subsets: ["latin"],
  variable: "--font-body",
  display: "swap",
});

export const metadata: Metadata = {
  title: "SWICA Assistant",
  description: "Find the right SWICA insurance cover with the SWICA Assistant.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="de" className={brandFont.variable}>
      <body>{children}</body>
    </html>
  );
}
