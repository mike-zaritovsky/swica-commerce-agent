# SWICA assistant: demo path

Twelve messages that show what the assistant does, in the order to send them, with what a good
answer contains. Start on the German interface (DE); message 9 switches to English.

| # | Message | What the assistant shows |
|---|---|---|
| 1 | Grüezi! Wir sind eine Familie: ich bin 38 und arbeite Vollzeit angestellt, meine Frau ist 36 und selbständig, unsere Kinder sind 3 und 7, wir wohnen in Zürich. Wir möchten möglichst tiefe Prämien, ein Hausarzt oder Telemedizin als erste Anlaufstelle ist für uns ok. Welche Grundversicherung passt zu uns? | A comparison card of the fitting KVG models (Favorit Casa, Favorit Telmed, often Favorit Start) with pros, cons, "best for", and the maximum model discounts from the terms (up to 16 %, 17 %, 23 %). |
| 2 | Was kostet das für uns genau pro Monat? | Declines to compute a personal premium; explains what it depends on; offers the premium calculator and a consultation as chips. |
| 3 | Gibt es Rabatte für unsere Kinder? | 75 % on the adult basic premium for the first and second child (89 % from the third), from the terms. |
| 4 | Brauchen wir alle die Unfalldeckung in der Grundversicherung, oder können wir da sparen? | Per person: the employed parent can exclude accident cover and save 7 %; the self-employed parent and the children keep it. |
| 5 | Wie viel können wir sparen, wenn wir die Franchise erhöhen? Und bis wann geht das? | The excess table (up to CHF 1540 a year at CHF 2500), that children have no excess, and the deadlines (increase by the last working day in December, reduction by November). |
| 6 | Vergleiche Favorit Telmed und Favorit Casa für uns. | A two-column comparison card with a recommendation for the family. |
| 7 | Lohnt sich eine Spitalzusatzversicherung halbprivat? Was ist der Unterschied zwischen Hospita Halbprivat und Hospita Flex Halbprivat? | A comparison card: fixed semi-private cover versus choosing the ward per stay with a co-payment; no "you must buy" answer. |
| 8 | Ich habe seit Wochen Rückenschmerzen. Welche Behandlung hilft da am besten? | No medical advice; points to a doctor and santé24 (+41 44 404 86 86). |
| 9 | By the way, I'm currently with another insurer. How do I switch to SWICA and what's the deadline? | The interface switches to English; the 30 November notice deadline and how SWICA forwards the termination. |
| 10 | Add Favorit Telmed and Hospita Flex Halbprivat to my selection. | Both in "My selection", with the "from" total. |
| 11 | Actually, take Favorit Casa instead of Telmed. | Casa replaces Telmed: one basic insurance per person. |
| 12 | Great, let's start the application. | The application card: products, starting premiums, "Not binding", and "Continue to application" to the Shopify checkout. |

Also worth showing: the EN | DE switch in the app bar, the chips under each answer, and the
Activity panel (which tools ran). Within one API run the assistant remembers stated
preferences across sessions; a restart of the API clears that memory.
