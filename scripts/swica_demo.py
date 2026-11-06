"""Open www.swica.ch in a browser window with the SWICA assistant embedded, for a live demo.

The window runs examples/shopify_demo/embed/swica-embed.js on every swica.ch page and ignores
the site's Content-Security-Policy, so the assistant opens in the side panel rather than a
popup. Only this window is affected; the site itself is unchanged. The storefront and its API
must be running (see examples/shopify_demo/README.md).

    pip install playwright && playwright install chromium     # once
    python scripts/swica_demo.py                               # German site
    python scripts/swica_demo.py --lang en
    python scripts/swica_demo.py --agent-url https://agent.example.com/

Close the browser window to end.
"""

from __future__ import annotations

import argparse
import contextlib
import re
import sys
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parents[1]
EMBED = REPO_ROOT / "examples" / "shopify_demo" / "embed" / "swica-embed.js"


def embed_script(agent_url: str | None) -> str:
    source = EMBED.read_text(encoding="utf-8")
    if agent_url:
        source = re.sub(
            r"var AGENT_URL = '[^']*';", f"var AGENT_URL = '{agent_url}';", source, count=1
        )
    # Init scripts run before the page has a body; the embed needs one.
    return (
        "(function(){var run=function(){" + source + "};"
        "if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',run);}"
        "else{run();}})();"
    )


def launch(playwright):
    args = ["--start-maximized", "--disable-features=LocalNetworkAccessChecks"]
    # The installed Google Chrome looks like everyday browsing; Playwright's Chromium is the fallback.
    try:
        return playwright.chromium.launch(channel="chrome", headless=False, args=args)
    except PlaywrightError:
        return playwright.chromium.launch(headless=False, args=args)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--lang", choices=("de", "en"), default="de")
    parser.add_argument(
        "--agent-url", help="the storefront URL (default: the embed's, localhost:3000)"
    )
    args = parser.parse_args()

    with sync_playwright() as playwright:
        browser = launch(playwright)
        context = browser.new_context(bypass_csp=True, no_viewport=True)
        context.add_init_script(embed_script(args.agent_url))
        page = context.new_page()
        page.goto(f"https://www.swica.ch/{args.lang}", wait_until="domcontentloaded")
        print("swica.ch is open with the assistant in its help menu. Close the window to end.")
        with contextlib.suppress(PlaywrightError):  # raised when the window is closed
            page.wait_for_event("close", timeout=0)
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
