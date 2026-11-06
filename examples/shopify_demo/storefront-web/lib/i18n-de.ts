// German interface text for the SWICA storefront, in Swiss Standard German (no sharp s,
// Swiss insurance terms). Keys are the English wording the components pass to `tr`.

import { registerTranslations } from "web-shared";

// English wording that differs from the shared default for an insurance application.
registerTranslations("en", { "Check out": "Start application" });

registerTranslations("de", {
  // App bar and views
  Assistant: "Assistent",
  Activity: "Aktivität",
  Orders: "Bestellungen",
  orders: "Bestellungen",
  Arriving: "Unterwegs",
  "Nothing on the way": "Nichts unterwegs",
  "My selection": "Meine Auswahl",
  Cart: "Auswahl",
  product: "Produkt",
  Guest: "Gast",
  Shopper: "Gast",
  "{n} delayed": "{n} verspätet",
  "{n} open. Ask about any of them.": "{n} offen. Fragen Sie zu jeder.",
  "Ask about an order…": "Fragen Sie zu einer Bestellung…",
  "Ask about insurance cover, premiums, or your needs…": "Fragen Sie zu Versicherungen, Prämien oder Ihrem Bedarf…",
  Working: "Arbeitet",
  "Working…": "Einen Moment…",
  Send: "Senden",
  Latest: "Neueste",
  Close: "Schliessen",

  // Home
  Hello: "Grüezi",
  "Good morning": "Guten Morgen",
  "Good afternoon": "Guten Tag",
  "Good evening": "Guten Abend",
  "Ask about insurance cover, what affects your premium, or which product fits you.":
    "Fragen Sie zu Versicherungsdeckung, zu dem, was Ihre Prämie beeinflusst, oder welches Produkt zu Ihnen passt.",
  "Prices shown are starting premiums; your personal premium depends on your age, model, excess, and other details.":
    "Die angezeigten Preise sind Ab-Prämien; Ihre persönliche Prämie hängt von Alter, Modell, Franchise und weiteren Angaben ab.",
  "Which insurance products do you offer?": "Welche Versicherungen bieten Sie an?",
  "I need cover for my family with two children": "Ich suche eine Versicherung für meine Familie mit zwei Kindern",
  "How is my premium calculated?": "Wie wird meine Prämie berechnet?",
  "Compare supplementary hospital insurance options": "Vergleichen Sie die Spitalzusatzversicherungen",
  "Popular insurance products": "Beliebte Versicherungen",
  "Starting premiums; open one to ask about it": "Ab-Prämien; öffnen Sie eine, um mehr zu erfahren",
  "Tell me about {name}.": "Erzählen Sie mir mehr über {name}.",

  // Products and prices
  from: "ab",
  vs: "vs.",
  "Premium calculated individually": "Prämie wird individuell berechnet",
  "Out of stock": "Nicht verfügbar",
  "Add {name} to my selection": "{name} zur Auswahl hinzufügen",
  "Choose options for {name}": "Optionen für {name} wählen",
  "Collapse details": "Details schliessen",
  "Loading details…": "Details werden geladen…",
  "Scroll to more products": "Weitere Produkte",
  "Scroll to previous products": "Vorherige Produkte",
  Recommended: "Empfohlen",
  "Best for:": "Ideal für:",
  "Compared on:": "Verglichen nach:",
  "Difference in starting premium:": "Unterschied der Ab-Prämie:",

  // Selection (cart) and application
  "{n} product": "{n} Produkt",
  "{n} products": "{n} Produkte",
  "Nothing selected yet.": "Noch nichts ausgewählt.",
  "Ask the SWICA Assistant about any insurance product.": "Fragen Sie den SWICA Assistenten zu jeder Versicherung.",
  "Starting premiums in total": "Total der Ab-Prämien",
  "Your personal premium is calculated in the application.": "Ihre persönliche Prämie wird im Antrag berechnet.",
  "I would like to apply for my selection.": "Ich möchte meine Auswahl beantragen.",
  "Ask about this selection": "Fragen zu dieser Auswahl",
  "Look over my selection: is anything missing for my situation?": "Prüfen Sie meine Auswahl: Fehlt etwas für meine Situation?",
  "Remove {name} from my selection.": "Entfernen Sie {name} aus meiner Auswahl.",
  Remove: "Entfernen",
  "Check out": "Antrag starten",
  "View summary": "Zusammenfassung ansehen",
  "Show me the checkout summary again.": "Zeigen Sie mir die Zusammenfassung des Antrags noch einmal.",
  "Ready to apply": "Bereit für den Antrag",
  "Not binding": "Unverbindlich",
  "Continue to application": "Weiter zum Antrag",
  "Your personal premium depends on your age, place of residence, model, excess, and accident cover; SWICA calculates it in the application.":
    "Ihre persönliche Prämie hängt von Alter, Wohnort, Modell, Franchise und Unfalldeckung ab; SWICA berechnet sie im Antrag.",
  "Nothing is charged here. SWICA confirms your premium before anything becomes binding.":
    "Hier wird nichts belastet. SWICA bestätigt Ihre Prämie, bevor etwas verbindlich wird.",

  // Orders view (shared)
  All: "Alle",
  "All {what}": "Alle {what}",
  Filter: "Filter",
  "On the way": "Unterwegs",
  Delayed: "Verspätet",
  Past: "Vergangen",
  Processing: "In Bearbeitung",
  Shipped: "Versandt",
  "Out for delivery": "In Zustellung",
  Delivered: "Zugestellt",
  Cancelled: "Storniert",
  "Return requested": "Rücksendung beantragt",
  Refunded: "Erstattet",
  "No {what} here.": "Keine {what} vorhanden.",
  "Couldn't load your {what}. The assistant can still look them up.":
    "{what} konnten nicht geladen werden. Der Assistent kann sie trotzdem nachschlagen.",

  // Profile and memory sheet (shared)
  "Signed in as {name}.": "Angemeldet als {name}.",
  "Switch to {name}": "Zu {name} wechseln",
  "What {assistant} knows": "Was {assistant} weiss",
  "{n} saved": "{n} gespeichert",
  "{assistant} uses these when it recommends something. Edit or forget any line; a forgotten line is deleted.":
    "{assistant} nutzt diese Angaben für Empfehlungen. Jede Zeile lässt sich bearbeiten oder vergessen; eine vergessene Zeile wird gelöscht.",
  "Nothing saved yet.": "Noch nichts gespeichert.",
  "Only preferences and standing rules are kept. Card, account, phone, and email details are refused.":
    "Gespeichert werden nur Vorlieben und feste Regeln. Karten-, Konto-, Telefon- und E-Mail-Angaben werden abgelehnt.",
  Preference: "Vorliebe",
  Rule: "Regel",
  "About you": "Über Sie",
  "New this session": "Neu in dieser Sitzung",
  "Correct this": "Korrigieren",
  "That could not be saved. Keep it to a preference or a standing rule.":
    "Das konnte nicht gespeichert werden. Bitte nur Vorlieben oder feste Regeln.",
  Edit: "Bearbeiten",
  Forget: "Vergessen",
  Save: "Speichern",
  Cancel: "Abbrechen",
  "{n} fact saved this session": "{n} Angabe in dieser Sitzung gespeichert",
  "{n} facts saved this session": "{n} Angaben in dieser Sitzung gespeichert",

  // Activity lines while the assistant works
  "Searching the catalog…": "Durchsuche das Angebot…",
  "Reading the details…": "Lese die Details…",
  "Checking the policies…": "Prüfe die Bedingungen…",
  "Looking up your orders…": "Suche Ihre Bestellungen…",
  "Checking the cart…": "Prüfe die Auswahl…",
  "Updating the cart…": "Aktualisiere die Auswahl…",
  "Preparing your order summary…": "Bereite die Zusammenfassung vor…",
  "Reading your profile…": "Lese Ihr Profil…",
  "Recalling what you've told me…": "Erinnere mich an Ihre Angaben…",
  "Saving that for next time…": "Speichere das für das nächste Mal…",
  "Loading…": "Lade…",
  "Searching the web…": "Suche im Web…",
  "Composing the answer…": "Formuliere die Antwort…",
});
