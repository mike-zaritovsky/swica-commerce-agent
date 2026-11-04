// Copyright 2026 Anthropic PBC
// SPDX-License-Identifier: Apache-2.0

"use client";

import { AskLink, BagPanel, CheckoutButton, optionValuesLabel, RemoveLink, TotalRow, tr, useCatalogIndex, useStoreFrame } from "web-shared";
import { fetchProducts } from "@/lib/api";
import { fromPrice } from "@/lib/price";
import type { CartItem, CartPayload, Product } from "@/lib/types";
import { ProductImage, ProductTitle } from "./ProductTile";

/** The listing behind a line; a variant's line borrows its family's brand and image. */
function asProduct(item: CartItem, catalog: Record<string, Product>): Product {
  const family = item.variant_of ? catalog[item.variant_of] : undefined;
  return (
    catalog[item.product_id] ?? {
      ...family,
      product_id: item.product_id,
      title: item.title,
      price: item.price,
      image_url: item.image_url ?? family?.image_url,
      options: undefined,
      option_values: item.option_values,
    }
  );
}

/** "the ACME Sleep Hybrid Mattress (queen)": what a message to the assistant calls a line. */
function lineName(item: CartItem): string {
  const chosen = optionValuesLabel(item);
  return chosen ? `${item.title} (${chosen})` : item.title;
}

/** The docked cart. Quantity and checkout are messages to the assistant, so every write is one it made. */
/** The products the customer wants to apply for. Each is held once (one basic insurance per
 * person), so there is no quantity stepper; removing and the application are messages to
 * the assistant, so every write goes through its gates. */
export default function CartPanel({ cart, checkoutStaged = false }: { cart: CartPayload | null; checkoutStaged?: boolean }) {
  const { ask } = useStoreFrame();
  const items = cart?.items ?? [];
  const count = cart?.item_count ?? 0;
  const catalog = useCatalogIndex(fetchProducts);
  const countLabel = tr(count === 1 ? "{n} product" : "{n} products", { n: count });

  return (
    <BagPanel
      title={tr("My selection")}
      count={countLabel}
      isEmpty={items.length === 0}
      empty={
        <>
          {tr("Nothing selected yet.")}
          <br />
          {tr("Ask the SWICA Assistant about any insurance product.")}
        </>
      }
      footer={
        <>
          <TotalRow
            label={tr("Starting premiums in total")}
            value={fromPrice(cart?.subtotal ?? 0, cart?.currency)}
            note={items.length ? tr("Your personal premium is calculated in the application.") : undefined}
          />
          <CheckoutButton staged={checkoutStaged} disabled={items.length === 0} prompt={tr("I would like to apply for my selection.")} />
          {items.length ? (
            <div className="mt-2.5 flex justify-center">
              <AskLink label={tr("Ask about this selection")} prompt={tr("Look over my selection: is anything missing for my situation?")} />
            </div>
          ) : null}
        </>
      }
    >
      <ul className="divide-y divide-(--line)">
        {items.map((item) => {
          const product = asProduct(item, catalog);
          return (
            <li key={item.product_id} className="ac-reveal flex gap-3 py-3 first:pt-0">
              <ProductImage product={product} className="h-16 w-16 shrink-0 rounded-[10px] !text-3xl" />
              <div className="min-w-0 flex-1">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    {product.brand ? <div className="text-[10.5px] font-semibold uppercase tracking-[0.06em] text-(--ink-soft)">{product.brand}</div> : null}
                    {/* A two-line clamp cuts long names in half. */}
                    <ProductTitle title={item.title} className="line-clamp-3 text-[13.5px] font-semibold leading-snug text-(--ink)" />
                    {product.category ? <div className="text-[11.5px] text-(--ink-soft)">{product.category}</div> : null}
                  </div>
                  <div className="shrink-0 text-right text-[14px] font-bold tabular-nums text-(--ink)">{fromPrice(item.price, cart?.currency)}</div>
                </div>
                <div className="mt-2 flex items-center gap-2.5">
                  <RemoveLink itemTitle={lineName(item)} onClick={() => ask(tr("Remove {name} from my selection.", { name: lineName(item) }))} />
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </BagPanel>
  );
}
