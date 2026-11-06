// Copyright 2026 Anthropic PBC
// SPDX-License-Identifier: Apache-2.0

"use client";

import { type Locale, setLocale, useLocale } from "web-shared";

const OPTIONS: { id: Locale; label: string; name: string }[] = [
  { id: "en", label: "EN", name: "English" },
  { id: "de", label: "DE", name: "Deutsch" },
];

/** EN | DE in the app bar; the assistant answers in the chosen language from the next message. */
export default function LanguageSwitch() {
  const locale = useLocale();
  return (
    <div role="radiogroup" aria-label="Language / Sprache" className="flex items-center rounded-full bg-(--well) p-0.5 text-[12px] font-bold">
      {OPTIONS.map((option) => (
        <button
          key={option.id}
          type="button"
          role="radio"
          aria-checked={locale === option.id}
          title={option.name}
          onClick={() => setLocale(option.id)}
          className={`rounded-full px-2.5 py-1 transition-colors ${locale === option.id ? "bg-(--accent-strong) text-(--on-accent)" : "text-(--ink-soft) hover:text-(--ink)"}`}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
