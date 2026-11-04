// Copyright 2026 Anthropic PBC
// SPDX-License-Identifier: Apache-2.0

/**
 * Interface language for the shared components. Text is keyed by its English wording:
 * `tr("Cart")` returns the active locale's entry, or the English text when the locale has
 * none, so an app that registers nothing stays English. An app registers a dictionary with
 * `registerTranslations`, switches with `setLocale`, and subscribes its root with `useLocale`
 * so the tree re-renders on a switch.
 */

import { useSyncExternalStore } from "react";

export type Locale = "en" | "de";

let locale: Locale = "en";
const listeners = new Set<() => void>();
const dictionaries: Partial<Record<Locale, Record<string, string>>> = {};

export function registerTranslations(target: Locale, entries: Record<string, string>): void {
  dictionaries[target] = { ...dictionaries[target], ...entries };
}

export function getLocale(): Locale {
  return locale;
}

export function setLocale(next: Locale): void {
  if (next === locale) return;
  locale = next;
  listeners.forEach((listener) => listener());
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

/** The active locale; the server render and first client render are always "en". */
export function useLocale(): Locale {
  return useSyncExternalStore(subscribe, getLocale, () => "en");
}

/** `text` in the active locale; `{name}` placeholders take `vars`. */
export function tr(text: string, vars?: Record<string, string | number>): string {
  let out = dictionaries[locale]?.[text] ?? text;
  if (vars) for (const [name, value] of Object.entries(vars)) out = out.replaceAll(`{${name}}`, String(value));
  return out;
}

/** BCP 47 tag for dates and numbers in the active locale (Swiss conventions for German). */
export function localeTag(): string {
  return locale === "de" ? "de-CH" : "en-US";
}

const GERMAN = new Set(
  "ich du sie wir und oder der die das den dem ein eine einen ist sind bin bist nicht kein keine mit für fuer von zu zum zur auf bei wie was wo wann warum welche welcher welches gibt es mein meine meinen mir mich ihr ihre kann können koennen möchte moechte will brauche bitte danke hallo grüezi gruezi versicherung versicherungen prämie praemie franchise kinder kind familie spital zusatz grundversicherung kostet kosten habe hat haben auch noch nur schon sehr".split(" "),
);
const ENGLISH = new Set(
  "i you we they and or the a an is are am not no with for of to at on how what where when why which there my me your can could would like want need please thanks hello hi insurance premium premiums children child family hospital cost costs do does have has also only just very".split(" "),
);

/** "de" or "en" when a message is clearly in one of them, else null (a product name, a number). */
export function detectLanguage(text: string): Locale | null {
  const words = text.toLowerCase().match(/[a-zäöüß]+/g) ?? [];
  let de = /[äöüß]/i.test(text) ? 2 : 0;
  let en = 0;
  for (const word of words) {
    if (GERMAN.has(word)) de += 1;
    if (ENGLISH.has(word)) en += 1;
  }
  if (de >= 2 && de > en) return "de";
  if (en >= 2 && en > de) return "en";
  return null;
}
