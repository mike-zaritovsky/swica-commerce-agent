// Copyright 2026 Anthropic PBC
// SPDX-License-Identifier: Apache-2.0

/** Card and checkout footnotes. The SWICA storefront shows insurance premiums, so the
 * returns lines carry the premium note instead. */
export const STORE_POLICY = {
  returnsShort: "Premium calculated individually",
  returnsLine: "Prices are starting premiums; SWICA calculates your personal premium from your details.",
  freeShippingThreshold: 49,
  standardShippingEta: "3–5 business days",
} as const;
