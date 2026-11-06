# Copyright 2026 Anthropic PBC
# SPDX-License-Identifier: Apache-2.0

"""Helpers the storefront routes and backends share: the fields a product summary leaves
out, and the help-content search over policy entries."""

from __future__ import annotations

import re
from collections.abc import Iterable

from shopping_agent import Policy

# Letters in any script, so German words with umlauts stay whole.
_WORD = re.compile(r"[^\W_]+")

_HELP_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "any",
        "are",
        "as",
        "at",
        "be",
        "by",
        "can",
        "do",
        "does",
        "for",
        "from",
        "get",
        "how",
        "i",
        "if",
        "in",
        "is",
        "it",
        "its",
        "me",
        "my",
        "of",
        "on",
        "or",
        "so",
        "that",
        "the",
        "there",
        "this",
        "to",
        "up",
        "we",
        "what",
        "when",
        "which",
        "will",
        "with",
        "you",
        "your",
    }
)

SUMMARY_EXCLUDES = frozenset({"long_description", "specs", "review_highlights", "variants"})


def tokens(text: str) -> list[str]:
    return _WORD.findall(text.lower())


def stem(token: str) -> str:
    return token[:-1] if len(token) > 3 and token.endswith("s") else token


def _help_terms(text: str) -> set[str]:
    return {stem(t) for t in tokens(text) if t not in _HELP_STOPWORDS}


def search_help(policies: Iterable[Policy], query: str, limit: int = 3) -> list[Policy]:
    """Help entries ranked by term overlap; a hit in the title or category counts double."""
    query_terms = _help_terms(query)
    if not query_terms:
        return []
    scored = []
    for policy in policies:
        heading_hits = len(query_terms & _help_terms(f"{policy.title} {policy.category}"))
        body_hits = len(query_terms & _help_terms(policy.content))
        if points := 2 * heading_hits + body_hits:
            scored.append((points, policy))
    scored.sort(key=lambda pair: -pair[0])
    return [policy for _, policy in scored[:limit]]
