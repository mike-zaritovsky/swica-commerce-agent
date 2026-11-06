# SWICA assistant: demo path

Twelve messages that show what the assistant does, in the order to send them, with what a good
answer contains. Send them in one conversation; the assistant replies in the language of each
message and the interface follows.

## English

| # | Message | What the assistant shows |
|---|---|---|
| 1 | Hi! We're a family living in Zurich: I'm 38 and work full-time as an employee, my wife is 36 and self-employed, and our kids are 3 and 7. We want the lowest possible premiums, and a family doctor or telemedicine as the first point of contact is fine for us. Which basic insurance fits us? | A comparison card of the fitting basic models (Favorit Start, Favorit Telmed, Favorit Casa) with pros, cons, and "best for", and their maximum model discounts from SWICA's terms (up to 23 %, 17 %, 16 %); mentions the 75 % child discount. |
| 2 | So how much exactly will that cost us per month? | Declines to compute a personal premium, says what it depends on, and offers the premium calculator and a consultation as chips. |
| 3 | Are there any discounts for our kids? | 75 % on the adult basic premium for the first and second child (89 % from a third). |
| 4 | Do all of us need accident cover in the basic insurance, or can we save there? | Per person: the employed parent can exclude accident cover and save 7 %; the self-employed parent and the children keep it. |
| 5 | How much can we save by raising our deductible, and what's the deadline for changing it? | The excess table (up to CHF 1540 a year at CHF 2500), that children have no excess, and the deadlines (increase by the last working day of December, reduction by the last working day of November). |
| 6 | Compare Favorit Telmed and Favorit Casa for our family. | A two-column comparison card with a recommendation that follows the family's stated priorities. |
| 7 | Is semi-private hospital insurance worth it for me? What's the difference between Hospita Halbprivat and Hospita Flex Halbprivat? | A comparison card: semi-private on every stay versus choosing the ward per stay with a cost share; leaves the decision to the customer. |
| 8 | I've had back pain for weeks. What's the best treatment? | No medical advice; points to a doctor and santé24 (+41 44 404 86 86). |
| 9 | By the way, I'm currently with another insurer. How do I switch to SWICA and what's the deadline? | The 30 November notice deadline and how SWICA forwards the termination only once the customer is insured. |
| 10 | Add Favorit Telmed and Hospita Flex Halbprivat to my selection. | Both in "My selection" with the "from" total. |
| 11 | Actually, take Favorit Casa instead of Telmed. | Casa replaces Telmed: one basic insurance per person. |
| 12 | Great, let's start the application. | The application card ("Not binding", "Continue to application" to the Shopify checkout), and a reminder that the wife and children each need their own basic insurance. |

## German, for the client

The same path in German; switch the interface to DE first.

1. Grüezi! Wir sind eine Familie: ich bin 38 und arbeite Vollzeit angestellt, meine Frau ist 36 und selbständig, unsere Kinder sind 3 und 7, wir wohnen in Zürich. Wir möchten möglichst tiefe Prämien, ein Hausarzt oder Telemedizin als erste Anlaufstelle ist für uns ok. Welche Grundversicherung passt zu uns?
2. Was kostet das für uns genau pro Monat?
3. Gibt es Rabatte für unsere Kinder?
4. Brauchen wir alle die Unfalldeckung in der Grundversicherung, oder können wir da sparen?
5. Wie viel können wir sparen, wenn wir die Franchise erhöhen? Und bis wann geht das?
6. Vergleiche Favorit Telmed und Favorit Casa für uns.
7. Lohnt sich eine Spitalzusatzversicherung halbprivat? Was ist der Unterschied zwischen Hospita Halbprivat und Hospita Flex Halbprivat?
8. Ich habe seit Wochen Rückenschmerzen. Welche Behandlung hilft da am besten?
9. Übrigens, ich bin noch bei einer anderen Krankenkasse. Wie wechsle ich zu SWICA, und bis wann?
10. Bitte nimm Favorit Telmed und Hospita Flex Halbprivat in meine Auswahl.
11. Doch lieber Favorit Casa statt Telmed.
12. Super, starte den Antrag.

## Also worth showing

The chips under each answer (the next step, in the reply's language), the EN | DE switch in
the app bar (a message in the other language switches it too), and the Activity panel (which
tools ran). Within one API run the assistant remembers stated preferences across
conversations; a restart of the API clears that memory.
