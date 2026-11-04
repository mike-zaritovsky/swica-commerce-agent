// Copyright 2026 Anthropic PBC
// SPDX-License-Identifier: Apache-2.0

/** Image-less products get a tile color and glyph from id and category. */

// SWICA tile grounds: gruen-200/-300, neutrals-200, blau-200 (from swica.ch's palette).
const TILE_CLASSES = [
  "bg-[#e5fff7] text-[#042d2e]",
  "bg-[#d1fcf0] text-[#042d2e]",
  "bg-[#f5f7f7] text-[#042d2e]",
  "bg-[#e5f2fa] text-[#042d2e]",
];

function hash(text: string): number {
  let value = 0;
  for (let i = 0; i < text.length; i++) {
    value = (value * 31 + text.charCodeAt(i)) >>> 0;
  }
  return value;
}

/** First match wins; order runs specific to general. */
const KEYWORD_GLYPHS: [string, string][] = [
  ["salmon", "🐟"], ["stir-fry", "🍜"], ["pasta", "🍝"], ["rigatoni", "🍝"],
  ["sauce", "🍅"], ["beef", "🥩"], ["salad", "🥗"], ["brioche", "🥖"],
  ["roll", "🥖"], ["veggie", "🥦"], ["brownie", "🍫"], ["marinade", "🍋"],
  ["coffee", "☕"], ["skillet", "🍳"], ["knife", "🔪"], ["blender", "🥤"],
  ["bed frame", "🛏️"], ["mattress", "🛏️"], ["duvet", "🛌"], ["pillow", "🛌"],
  ["cosmic", "🚀"], ["rocket", "🚀"], ["starlit", "✨"], ["solar system", "🪐"], ["space", "🚀"],
  ["decal", "🖼️"], ["poster", "🖼️"], ["rug", "🟫"], ["curtain", "🪟"],
  ["night light", "💡"], ["projector", "✨"], ["lamp", "💡"], ["plush", "🧸"],
  ["bedding", "🐋"], ["storage bin", "🧺"], ["ocean", "🐋"], ["tide", "🌊"],
  ["palette", "💄"], ["mascara", "💄"], ["moisturizer", "🧴"], ["serum", "🧴"],
  ["tent", "⛺"], ["sleeping bag", "🛌"], ["stove", "🔥"], ["lantern", "🏮"],
  ["headphone", "🎧"], ["monitor", "🖥️"], ["keyboard", "⌨️"], ["mouse", "🖱️"],
  ["chair", "🪑"], ["desk", "🖥️"], ["stand", "💻"], ["webcam", "📷"],
  ["dumbbell", "🏋️"], ["yoga", "🧘"], ["kettlebell", "🏋️"], ["resistance", "💪"],
  ["spinner", "🧳"], ["carry-on", "🧳"], ["packing", "🎒"], ["adapter", "🔌"],
  ["tracker", "📍"], ["toiletry", "🧴"],
  ["dog", "🐕"], ["cat", "🐈"], ["leash", "🦮"], ["pet", "🐾"],
  ["brick", "🧱"], ["building", "🧱"], ["art studio", "🎨"], ["figure", "🦖"],
  ["book", "📚"], ["game", "🎲"], ["puzzle", "🧩"],
];

/** Rotated by product id so a same-category row varies. */
const CATEGORY_GLYPHS: Record<string, string[]> = {
  KVG: ["🩺"], // SWICA basic health insurance
  VVG: ["🛡️"], // SWICA supplementary insurance
  "home-kitchen": ["🍳", "🫖", "🥘", "🔪"],
  "office-electronics": ["🖥️", "⌨️", "🎧", "🖱️"],
  "outdoor-camping": ["⛺", "🔦", "🥾", "🏕️"],
  fitness: ["🏋️", "🧘", "💪", "🤸"],
  "toys-games": ["🦖", "🧩", "🎲", "🧸"],
  "pet-supplies": ["🐾", "🐕", "🐈", "🦴"],
  "beauty-personal-care": ["🌿", "🧴", "💄", "🪞"],
  travel: ["🧳", "🎒", "🌍", "✈️"],
  "kids-room": ["🦕", "🦖", "🌋", "🧸"],
  "furniture-bedroom": ["🛏️", "🛌", "🪑", "🕯️"],
  grocery: ["🥕", "🍎", "🧀", "🥫"],
};

export function productGlyph(product: { title?: string; category?: string | null; product_id?: string }): string {
  // Insurance categories take their own glyph before any keyword in the title can match.
  if (product.category === "KVG" || product.category === "VVG") return CATEGORY_GLYPHS[product.category][0];
  const title = (product.title ?? "").toLowerCase();
  for (const [keyword, glyph] of KEYWORD_GLYPHS) {
    if (title.includes(keyword)) return glyph;
  }
  const pool = CATEGORY_GLYPHS[product.category ?? ""] ?? ["🛍️"];
  return pool[hash(product.product_id ?? title) % pool.length];
}

export function productTileClass(productId: string): string {
  return TILE_CLASSES[hash(productId) % TILE_CLASSES.length];
}

/** These have their own renderers. */
const STAMPED_ATTRIBUTES = new Set(["delivery", "low_stock"]);

export function attributeChips(product: { attributes?: Record<string, string> }): string[] {
  return Object.entries(product.attributes ?? {})
    .filter(([key]) => !STAMPED_ATTRIBUTES.has(key))
    .map(([key, value]) => {
      if (/^(yes|true)$/i.test(value)) return key.replaceAll("_", " ");
      if (/^(no|false)$/i.test(value)) return null;
      return value;
    })
    .filter((chip): chip is string => Boolean(chip))
    // A value can arrive twice (a Shopify product type repeated as a tag); show it once.
    .filter((chip, index, chips) => chips.findIndex((other) => other.toLowerCase() === chip.toLowerCase()) === index)
    .slice(0, 3);
}
