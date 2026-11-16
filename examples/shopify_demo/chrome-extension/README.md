# SWICA AI Assistant: Chrome extension (demo)

This extension adds our AI insurance assistant to the live SWICA website for demos. On
www.swica.ch, the site's own help button ("How can we help you?") gets a new first entry,
**AI Assistant / KI-Assistent ✦**, which opens the assistant in a side panel in the page's
language (German or English).

It works only on www.swica.ch and changes nothing on SWICA's side: the site normally blocks
embedded content from other domains, and the extension lifts that restriction in your browser
only, for swica.ch only. Every other site is untouched.

## Install (once, about a minute)

Works in Google Chrome and Microsoft Edge on Mac and Windows.

1. Unzip `swica-assistant-extension-<version>.zip` into a folder you keep, for example
   `Documents/swica-assistant-extension`. Chrome loads the extension from this folder, so
   don't delete or move it afterwards.
2. Open `chrome://extensions` (in Edge: `edge://extensions`).
3. Turn on **Developer mode** (top right in Chrome, left sidebar in Edge).
4. Click **Load unpacked** and select the unzipped folder (the one that contains
   `manifest.json`).
5. "SWICA AI Assistant (demo)" appears in the list with a mint icon. Optionally pin it via
   the puzzle-piece icon in the toolbar.

## Use

1. Open https://www.swica.ch/de (or `/en` for English). If the page was already open, reload it.
2. Click SWICA's round help button in the bottom right corner.
3. Choose **KI-Assistent ✦** (or **AI Assistant ✦**). The assistant opens on the right.
4. Close it with the ✕ next to the panel, the Esc key, or a click outside it.

The assistant answers in the language you write in; the EN | DE switch in its header changes
the interface. Prices are "from" premiums; the personal premium always comes from SWICA's
calculator or application.

## Turn off, update, remove

- **Turn off** between demos: switch the extension off on `chrome://extensions`. While it is
  on, swica.ch runs without its usual content-security restriction in your browser.
- **Update**: replace the folder's contents with the new version, then click the reload icon on
  the extension's card in `chrome://extensions`.
- **Remove**: click **Remove** on the extension's card.

## Troubleshooting

- **No "KI-Assistent" entry in the menu**: reload swica.ch; check that the extension is
  switched on; open the menu once more.
- **"Developer mode" or "Load unpacked" is greyed out**: your browser is managed by company IT
  policy, which blocks unpacked extensions. Ask IT, or use another browser profile or Edge.
- **The panel opens but stays blank, or the assistant opens in a separate window**: the
  extension is off or outdated; switch it on or update it and reload the page.
- **Chrome warns about developer-mode extensions** at start-up: expected for extensions
  loaded this way; choose to keep it.
