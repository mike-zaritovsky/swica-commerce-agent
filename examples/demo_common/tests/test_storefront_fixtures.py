# Copyright 2026 Anthropic PBC
# SPDX-License-Identifier: Apache-2.0

"""The help-content search the backend's search_policies uses."""

from demo_common.storefront_fixtures import search_help
from shopping_agent import Policy


def test_help_search_ignores_function_words_and_weights_headings():
    returns = Policy(policy_id="h-1", title="Returns", category="orders", content="Thirty days.")
    guide = Policy(
        policy_id="h-2",
        title="Buying guide",
        category="guides",
        content="How do I choose a tent? What is the return on a good tent? Returns matter.",
    )
    assert search_help([guide, returns], "how do returns work") == [returns, guide]
    assert search_help([guide, returns], "the a of") == []


def test_german_words_keep_their_umlauts():
    excess = Policy(
        policy_id="e", title="Franchise", category="excess", content="Ändern bis Dezember."
    )
    other = Policy(policy_id="o", title="Kontakt", category="contact", content="Telefon.")
    assert search_help([other, excess], "Franchise ändern") == [excess]
    assert search_help([other, excess], "ändern") == [excess]
