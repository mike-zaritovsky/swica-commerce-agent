// Copyright 2026 Anthropic PBC
// SPDX-License-Identifier: Apache-2.0

"use client";

import { useEffect, useState } from "react";
import type { AgentApi } from "./api";

export interface Session {
  /** Null while login is in flight or after it failed. */
  sessionId: string | null;
  /** The signed-in operator's name, on merchant sessions. */
  operator?: string;
  /** The signed-in shopper, on storefront sessions. */
  shopper?: { name: string; tier?: string };
}

const generations = new WeakMap<AgentApi, number>();

// The anonymous id the API issued this browser; sent back so memory follows the visitor
// across visits and is never shared with other visitors.
const VISITOR_KEY = "agent-visitor-id";

function storedVisitor(): string | null {
  try {
    return window.localStorage.getItem(VISITOR_KEY);
  } catch {
    return null;
  }
}

function rememberVisitor(userId: string | undefined): void {
  if (!userId) return;
  try {
    window.localStorage.setItem(VISITOR_KEY, userId);
  } catch {}
}

/**
 * Only the newest start installs its token. Key the caller on the profile so per-session
 * state resets with it.
 */
export function useSession(
  api: AgentApi,
  options: { profile?: string } = {},
): Session {
  const { profile } = options;
  const [session, setSession] = useState<Session>({ sessionId: null });

  useEffect(() => {
    const generation = (generations.get(api) ?? 0) + 1;
    generations.set(api, generation);
    const current = () => generations.get(api) === generation;
    void (async () => {
      const claimed = profile ?? storedVisitor();
      const started = await api.startSession(claimed ? { user_id: claimed } : undefined);
      if (!current()) return;
      if (!profile) rememberVisitor(started?.userId);
      api.session = started?.sessionId ?? null;
      setSession({ sessionId: started?.sessionId ?? null, operator: started?.operator, shopper: started?.shopper });
    })();
    return () => {
      generations.set(api, (generations.get(api) ?? 0) + 1);
    };
  }, [api, profile]);

  return session;
}
