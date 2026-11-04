// Prices in this storefront are insurance premiums: each listed price is an indicative
// starting premium, and the actual premium is calculated from the customer's details
// (age, package, deductible, residence). So every price reads as a "from" price.

import { formatMoney } from "web-shared";

export const FROM_PREFIX = "from";

export function fromPrice(value: number, currency?: string): string {
  return `${FROM_PREFIX} ${formatMoney(value, currency)}`;
}

export function fromPriceLabel(product: { price: number; currency?: string | null }): string {
  return fromPrice(product.price, product.currency ?? undefined);
}
