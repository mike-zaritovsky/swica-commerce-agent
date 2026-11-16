"""Build the SWICA AI Assistant Chrome extension for distribution.

Copies examples/shopify_demo/chrome-extension, adds the shared embed script
(examples/shopify_demo/embed/swica-embed.js), and writes config.js with the deployed
assistant's URL. The result is a folder to load unpacked and a zip to hand out:

    python scripts/build_extension.py --agent-url https://swica-agent.example.com/
    # -> dist/swica-assistant-extension/  and  dist/swica-assistant-extension-<version>.zip
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE = REPO_ROOT / "examples" / "shopify_demo" / "chrome-extension"
EMBED = REPO_ROOT / "examples" / "shopify_demo" / "embed" / "swica-embed.js"
NAME = "swica-assistant-extension"


def agent_url(value: str) -> str:
    parsed = urlparse(value)
    local = parsed.hostname in {"localhost", "127.0.0.1"}
    if parsed.scheme != "https" and not (parsed.scheme == "http" and local):
        raise argparse.ArgumentTypeError("use the deployed https URL (http only for localhost)")
    return value if value.endswith("/") else value + "/"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--agent-url", type=agent_url, required=True, help="the deployed storefront URL"
    )
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "dist", help="output directory")
    args = parser.parse_args()

    target = args.out / NAME
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(SOURCE, target, ignore=shutil.ignore_patterns(".*"))
    shutil.copy2(EMBED, target / "swica-embed.js")
    (target / "config.js").write_text(
        "// The deployed SWICA assistant this build opens.\n"
        f"var SWICA_AI_CONFIG = {{ agentUrl: {json.dumps(args.agent_url)} }};\n",
        encoding="utf-8",
    )

    version = json.loads((SOURCE / "manifest.json").read_text(encoding="utf-8"))["version"]
    archive = shutil.make_archive(str(args.out / f"{NAME}-{version}"), "zip", target)
    print(f"Folder: {target}")
    print(f"Zip:    {archive}")
    print(f"Opens:  {args.agent_url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
