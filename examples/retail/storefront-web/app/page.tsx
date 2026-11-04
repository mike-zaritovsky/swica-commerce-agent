// Copyright 2026 Anthropic PBC
// SPDX-License-Identifier: Apache-2.0

"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { type AgentEvent, detectLanguage, getLocale, type Locale, OrdersView, setLocale, StoreShell, type StoreView, tr, upcoming, useAgentTurn, useLocale, useResource, useSession } from "web-shared";
import CartPanel from "@/components/CartPanel";
import Chat from "@/components/Chat";
import HomeView from "@/components/views/HomeView";
import LanguageSwitch from "@/components/LanguageSwitch";
import "@/lib/i18n-de";
import { api, UNREACHABLE } from "@/lib/api";
import { fromPrice } from "@/lib/price"; // also sets the storefront's default currency
import { NOUNS, OrderThumb } from "@/lib/orders";
import type { CartPayload } from "@/lib/types";

type View = "assistant" | "orders";

const ASSISTANT = "SWICA Assistant";
const LOCALE_KEY = "swica-locale";

function Wordmark() {
  return (
    <span className="flex items-center gap-2.5 pr-1">
      <span className="text-[22px] font-medium tracking-[0.02em] text-(--accent)">SWICA</span>
      <span className="hidden text-[13px] font-medium text-(--ink-soft) sm:inline">{tr("Assistant")}</span>
      <LanguageSwitch />
    </span>
  );
}

export default function StorefrontPage() {
  const session = useSession(api);
  const [view, setView] = useState<View>("assistant");
  const [cart, setCart] = useState<CartPayload | null>(null);
  // A staged checkout owns the panel's primary action until the cart changes again.
  const [checkoutStaged, setCheckoutStaged] = useState(false);
  const [panelOpen, setPanelOpen] = useState(false);

  const handleCartUpdate = useCallback((next: CartPayload) => {
    setCart(next);
    setCheckoutStaged(false);
  }, []);

  const onEvent = useCallback(
    (event: AgentEvent) => {
      if (event.type === "cart_update") handleCartUpdate(event.data.cart as CartPayload);
      else if (event.type === "ui" && event.data.component === "checkout") setCheckoutStaged(true);
    },
    [handleCartUpdate],
  );

  const locale = useLocale();
  // The chosen language is remembered per browser and restored after mount, so the server
  // render (always English) and the first client render agree.
  useEffect(() => {
    try {
      const saved = window.localStorage.getItem(LOCALE_KEY);
      if (saved === "en" || saved === "de") setLocale(saved as Locale);
    } catch {}
  }, []);
  useEffect(() => {
    api.pageExtra = { ui_language: locale };
    try {
      window.localStorage.setItem(LOCALE_KEY, locale);
    } catch {}
  }, [locale]);

  const turn = useAgentTurn(api, { ...session, unreachable: UNREACHABLE, onEvent });
  // A message clearly written in the other language switches the interface (and the
  // assistant's reply language) with it.
  const chat = useMemo(
    () => ({
      ...turn,
      send: (text: string) => {
        const written = detectLanguage(text);
        if (written && written !== getLocale()) setLocale(written);
        api.pageExtra = { ui_language: getLocale() };
        return turn.send(text);
      },
    }),
    [turn],
  );
  // A reply may have started a return, so orders re-read after each one.
  const { data: orders, failed: ordersFailed } = useResource(session.sessionId ? () => api.fetchOrders() : null, [session.sessionId, chat.completed]);

  useEffect(() => {
    if (session.sessionId) void api.fetchCart<CartPayload>().then((next) => next && setCart(next));
  }, [session.sessionId]);

  const late = orders?.filter((order) => order.status === "delayed").length ?? 0;
  const views: StoreView<View>[] = [
    { id: "assistant", label: tr("Assistant"), icon: "spark" },
    { id: "orders", label: tr("Orders"), icon: "box", attention: late ? { count: late, label: tr("{n} delayed", { n: late }) } : null },
  ];
  const shopper = session.shopper ? { ...session.shopper, name: tr(session.shopper.name) } : { name: tr("Guest") };
  const count = cart?.item_count ?? 0;

  return (
    <StoreShell
      brand={<Wordmark />}
      views={views}
      view={view}
      onViewChange={setView}
      chat={chat}
      api={api}
      assistantName={ASSISTANT}
      shopper={shopper}
      bag={{ label: tr("My selection"), count, noun: tr("product"), figure: count ? fromPrice(cart?.subtotal ?? 0, cart?.currency) : null }}
      panel={<CartPanel cart={cart} checkoutStaged={checkoutStaged} />}
      panelOpen={panelOpen}
      onPanelOpenChange={setPanelOpen}
      placeholder={view === "orders" ? tr("Ask about an order…") : tr("Ask about insurance cover, premiums, or your needs…")}
    >
      {/* The conversation stays mounted under the other view so its cards keep their state. */}
      <div className={view === "assistant" ? "h-full" : "hidden"}>
        <Chat chat={chat} onCartUpdate={handleCartUpdate} home={<HomeView shopperName={shopper.name} orders={orders} ordersFailed={ordersFailed} onSeeOrders={() => setView("orders")} />} />
      </div>
      {view === "orders" ? (
        <OrdersView
          orders={orders}
          failed={ordersFailed}
          nouns={NOUNS}
          subtitle={orders ? tr("{n} open. Ask about any of them.", { n: upcoming(orders).length }) : undefined}
          thumb={(order) => <OrderThumb order={order} />}
        />
      ) : null}
    </StoreShell>
  );
}
