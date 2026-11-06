// ==UserScript==
// @name         SWICA AI assistant (demo)
// @match        https://www.swica.ch/*
// @run-at       document-idle
// @grant        none
// ==/UserScript==
/*
 * SWICA AI assistant embed for www.swica.ch (demo).
 *
 * Adds the assistant two ways, each switchable below:
 *  - MENU_ITEM: an "AI Assistant" / "KI-Assistent" entry in the site's own
 *    "How can we help you?" menu, cloned from its "Chat" entry so it keeps the site's styles;
 *  - BUBBLE: a floating button in the site's style (72px, 20px radius, mint) beside the
 *    site's help button.
 * Both open the assistant in a side panel (an iframe of AGENT_URL) in the page's language.
 *
 * swica.ch's Content-Security-Policy (frame-src) allows iframes only from its own list of
 * sites. When it blocks AGENT_URL, the script opens the assistant in a popup window docked
 * to the right instead. The side panel works once AGENT_URL's origin is on that list, or
 * in a browser with an extension that disables the CSP for the demo.
 *
 * Run it in the DevTools console on swica.ch, or let a userscript extension run it on load.
 */
(function () {
  if (document.getElementById('swica-ai-panel')) return;

  var AGENT_URL = 'http://localhost:3000/'; // the storefront; a deployed https URL for a shared demo
  var MENU_ITEM = true;
  var BUBBLE = true;

  // Colours from swica.ch's design tokens.
  var MINT = '#33e6be'; // help button
  var MINT_DARK = '#01bba8'; // help button, open/hover
  var INK = '#042d2e'; // text and icons

  var lang = (document.documentElement.lang || location.pathname.split('/')[1] || 'de').slice(0, 2).toLowerCase();
  var de = lang !== 'en';
  var LABEL = de ? 'KI-Assistent' : 'AI Assistant';
  var OPEN_LABEL = de ? 'SWICA KI-Assistent öffnen' : 'Open the SWICA AI assistant';
  var CLOSE_LABEL = de ? 'Schliessen' : 'Close';

  var SPARK =
    '<svg viewBox="0 0 24 24" width="24" height="24" fill="' + INK + '" aria-hidden="true">' +
    '<path d="M10 2.5l1.9 5.6 5.6 1.9-5.6 1.9L10 17.5l-1.9-5.6L2.5 10l5.6-1.9z"/>' +
    '<path d="M18.5 13.5l.9 2.1 2.1.9-2.1.9-.9 2.1-.9-2.1-2.1-.9 2.1-.9z"/></svg>';

  var css = document.createElement('style');
  css.textContent =
    '#swica-ai-bubble{position:fixed;right:48px;bottom:136px;z-index:2147483001;width:72px;height:72px;border:none;' +
    'border-radius:20px;background:' + MINT + ';color:' + INK + ';cursor:pointer;display:flex;flex-direction:column;' +
    'align-items:center;justify-content:center;gap:2px;box-shadow:0 8px 16px rgba(0,0,0,.1);font-family:inherit;' +
    'transition:background .2s,transform .2s}' +
    '#swica-ai-bubble:hover{background:' + MINT_DARK + ';transform:translateY(-2px)}' +
    '#swica-ai-bubble .swica-ai-tag{font-size:13px;font-weight:700;line-height:1;letter-spacing:.02em}' +
    '#swica-ai-overlay{display:none;position:fixed;inset:0;z-index:2147482999;background:rgba(4,45,46,.25)}' +
    '#swica-ai-panel{display:none;position:fixed;top:16px;right:16px;bottom:16px;width:min(520px,calc(100vw - 32px));' +
    'z-index:2147483000;background:#fff;border-radius:28px;overflow:hidden;box-shadow:0 12px 40px rgba(4,45,46,.25)}' +
    '#swica-ai-panel iframe{width:100%;height:100%;border:none}' +
    // The close button sits outside the panel's left edge, clear of the assistant's own app bar.
    '#swica-ai-close{display:none;position:fixed;top:16px;right:calc(min(520px,100vw - 32px) + 28px);z-index:2147483001;' +
    'width:48px;height:48px;border:none;border-radius:16px;background:' + MINT + ';color:' + INK + ';font-size:20px;' +
    'cursor:pointer;box-shadow:0 8px 16px rgba(0,0,0,.1)}' +
    '#swica-ai-close:hover{background:' + MINT_DARK + '}' +
    '.swica-ai-open #swica-ai-close{display:block}' +
    // While the panel is open, the site's own help button and menu step aside.
    '.swica-ai-open #swica-ai-bubble,.swica-ai-open [class*="floating-buttons_component"]{display:none!important}' +
    '@media (max-width:700px){#swica-ai-bubble{right:24px;bottom:104px;width:56px;height:56px;border-radius:16px}' +
    '#swica-ai-panel{top:64px;right:0;bottom:0;width:100vw;border-radius:28px 28px 0 0}' +
    '#swica-ai-close{top:8px;right:16px}}';
  document.head.appendChild(css);

  var overlay = document.createElement('div');
  overlay.id = 'swica-ai-overlay';
  var panel = document.createElement('div');
  panel.id = 'swica-ai-panel';
  panel.setAttribute('role', 'dialog');
  panel.setAttribute('aria-label', LABEL);
  var close = document.createElement('button');
  close.id = 'swica-ai-close';
  close.type = 'button';
  close.setAttribute('aria-label', CLOSE_LABEL);
  close.textContent = '✕';
  document.body.appendChild(close);

  var src = AGENT_URL + (AGENT_URL.indexOf('?') < 0 ? '?' : '&') + 'lang=' + (de ? 'de' : 'en');
  var agentOrigin = new URL(AGENT_URL).origin;
  var framingBlocked = false;
  var popup = null;

  // A blocked iframe only shows an error page, so the CSP violation event is the signal.
  document.addEventListener('securitypolicyviolation', function (e) {
    if (e.effectiveDirective !== 'frame-src' || (e.blockedURI || '').indexOf(agentOrigin) !== 0) return;
    framingBlocked = true;
    if (panel.style.display === 'block') {
      toggle(false);
      openPopup();
    }
  });

  function openPopup() {
    var width = 480;
    var height = Math.min(screen.availHeight - 40, 900);
    var left = (window.screenX || 0) + window.outerWidth - width - 16;
    var top = (window.screenY || 0) + 80;
    if (popup && !popup.closed) {
      popup.focus();
      return;
    }
    popup = window.open(src, 'swica-ai-assistant', 'popup,width=' + width + ',height=' + height + ',left=' + left + ',top=' + top);
  }

  var frame = null;
  function show() {
    if (framingBlocked) openPopup();
    else toggle(true);
  }
  function toggle(open) {
    if (open && !frame) {
      frame = document.createElement('iframe');
      frame.src = src;
      frame.title = LABEL;
      frame.allow = 'clipboard-write';
      panel.appendChild(frame);
    }
    panel.style.display = open ? 'block' : 'none';
    overlay.style.display = open ? 'block' : 'none';
    document.documentElement.classList.toggle('swica-ai-open', open);
  }
  function closeSiteMenu() {
    var open = document.querySelector('[class*="floating-buttons_triggerButtonOpen"]');
    if (open) open.click();
  }
  close.addEventListener('click', function () { toggle(false); });
  overlay.addEventListener('click', function () { toggle(false); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') toggle(false); });
  document.body.appendChild(overlay);
  document.body.appendChild(panel);

  if (BUBBLE) {
    var bubble = document.createElement('button');
    bubble.id = 'swica-ai-bubble';
    bubble.type = 'button';
    bubble.setAttribute('aria-label', OPEN_LABEL);
    bubble.title = LABEL;
    bubble.innerHTML = SPARK + '<span class="swica-ai-tag">' + (de ? 'KI' : 'AI') + '</span>';
    bubble.addEventListener('click', function () { closeSiteMenu(); show(); });
    document.body.appendChild(bubble);
  }

  if (MENU_ITEM) {
    // The menu is rendered when the site's help button opens it, so watch for its list and
    // add the entry once per render. Class names carry build hashes; match their stable part.
    function addMenuItem() {
      var list = document.querySelector('[class*="info-panel_cards"]');
      if (!list || list.querySelector('[data-swica-ai]')) return;
      var items = list.querySelectorAll('[role="listitem"]');
      var template = items[items.length - 1];
      if (!template) return;
      var item = template.cloneNode(true);
      item.setAttribute('data-swica-ai', '');
      var link = item.querySelector('a,button');
      var label = item.querySelector('[class*="linkLabel"]');
      var icon = item.querySelector('[class*="info-panel_icon"]');
      if (!link || !label) return;
      label.textContent = LABEL + ' ✦';
      if (icon) icon.innerHTML = SPARK;
      // A cloned <a> would navigate; replace it with a button that keeps its classes.
      var trigger = document.createElement('button');
      trigger.type = 'button';
      trigger.className = link.className;
      trigger.innerHTML = link.innerHTML;
      trigger.addEventListener('click', function (e) {
        e.preventDefault();
        closeSiteMenu();
        show();
      });
      link.replaceWith(trigger);
      list.insertBefore(item, list.firstChild);
    }
    new MutationObserver(addMenuItem).observe(document.body, { childList: true, subtree: true });
    addMenuItem();
  }
})();
