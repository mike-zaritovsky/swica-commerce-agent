// Copyright 2026 Anthropic PBC
// SPDX-License-Identifier: Apache-2.0

"use client";

import { useId } from "react";
import { safeHandoffs, tr, useCatalogIndex } from "web-shared";
import { fetchProducts } from "@/lib/api";
import { fromPrice } from "@/lib/price";
import type { CheckoutPayload, Product } from "@/lib/types";
import { ProductImage } from "../ProductTile";

/** The application summary: the selected products at their starting premiums, and the
 * hand-off to the application, where SWICA calculates the personal premium. */
export default function CheckoutSummary({ payload }: { payload: CheckoutPayload }) {
  const cart = payload.cart;
  const handoffs = safeHandoffs(payload.handoffs);
  // Several summaries can coexist across turns, so the describedby id is per card.
  const handoffNoteId = useId();
  const catalog = useCatalogIndex(fetchProducts);
  return (
    <section data-checkout-card className="rounded-2xl border-2 border-(--accent) bg-(--card) p-4 shadow-(--shadow-sm)">
      <div className="flex items-center justify-between gap-2">
        <h3 className="text-[15px] font-semibold text-(--ink)">{tr("Ready to apply")}</h3>
        <span className="whitespace-nowrap rounded-full border border-(--line) bg-(--well)/60 px-2.5 py-0.5 text-[11px] font-semibold text-(--ink-soft)">
          {tr("Not binding")}
        </span>
      </div>
      {payload.note ? <p className="mt-1 text-[13px] text-(--ink-soft)">{payload.note}</p> : null}
      <div className="mt-3 space-y-2 rounded-lg bg-(--well)/60 p-3 text-sm">
        {cart.items.map((item) => {
          // A line holds a variant id; its family listing carries the category and glyph.
          const product: Product = catalog[item.product_id] ?? (item.variant_of ? catalog[item.variant_of] : undefined) ?? { product_id: item.product_id, title: item.title, price: item.price };
          return (
            <div key={item.product_id} className="flex items-center gap-2.5">
              <ProductImage product={product} className="h-10 w-10 shrink-0 rounded-lg !text-xl" />
              <div className="flex min-w-0 flex-1 justify-between gap-2">
                <span className="line-clamp-1 text-(--ink)" title={item.title}>
                  {item.title}
                  {product.category ? <span className="ml-1.5 text-[12px] text-(--ink-soft)">{product.category}</span> : null}
                </span>
                <span className="shrink-0 text-(--ink)">{fromPrice(item.price, cart.currency)}</span>
              </div>
            </div>
          );
        })}
        <div className="flex justify-between border-t border-(--line) pt-1.5 text-base font-bold text-(--ink)">
          <span>{tr("Starting premiums in total")}</span>
          <span>{fromPrice(cart.subtotal, cart.currency)}</span>
        </div>
        <p className="text-[11px] leading-snug text-(--ink-soft)">
          {tr("Your personal premium depends on your age, place of residence, model, excess, and accident cover; SWICA calculates it in the application.")}
        </p>
      </div>
      {handoffs.length ? (
        // The backend named where the application continues (the store's hosted checkout).
        <div className="mt-3 flex flex-col gap-2">
          {handoffs.map((h) => (
            <a
              key={h.url}
              href={h.url}
              target="_blank"
              rel="noopener noreferrer"
              aria-describedby={handoffNoteId}
              className="btn-primary w-full text-center"
            >
              {tr(h.label ?? "Continue to application")}
            </a>
          ))}
        </div>
      ) : (
        // Disabled so assistive tech is not offered a focusable no-op.
        <button disabled aria-disabled aria-describedby={handoffNoteId} className="btn-primary mt-3 w-full cursor-not-allowed opacity-90">
          {tr("Continue to application")}
        </button>
      )}
      <p id={handoffNoteId} className="mt-2 text-center text-[11px] text-(--ink-soft)/80">
        {tr("Nothing is charged here. SWICA confirms your premium before anything becomes binding.")}
      </p>
    </section>
  );
}
