# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
<!-- Why 4 of 5 and not 5 of 5? Something about your search, probably —
     "my search is a plain keyword match and some phrasings will miss" is a
     real answer. -->
Not 5 of 5 because two of the three tools call Gemini over the network on
the free tier (15 requests a minute), and one slow or failed call ends the
run without a fit card even when my code is right. The search side is
deterministic for these queries, so I don't expect it to be the miss.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
<!-- Why is 5 of 5 reasonable here when criterion 1 isn't? What's different
     about this path? -->
This path never calls the model: `run_agent` checks whether the search list
is empty and stops, and the message is built by plain Python that re-runs the
search with one filter removed. Nothing random happens on it, so a single
failure would mean the branch itself is broken.

---

## 3. Something about state

<!-- YOU WRITE THIS ONE.

     How would you know that the item your search found is the same item the
     next tool received? Name something countable or observable.

     This is the criterion people find hardest, because state failure doesn't
     look like state failure — it looks like a tool problem. Something that
     compares session["selected_item"] against what actually reached
     suggest_outfit is the shape you're after. -->

Given the query `vintage graphic tee under $30`, the `id` of
`session["selected_item"]` equals `session["search_results"][0]["id"]`, equals
the `id` of the listing `suggest_outfit` actually received, and the fit card
contains that listing's price (`$24`) — in 5 of 5 tries.

**Why this target:**

The item moves from search to the next two tools only through the session, in
plain Python, with no model in between, so it has no reason to change. Checking
the price in the fit card catches the one place the model could swap in a
different item. If this ever misses, the session wiring is wrong, so I won't
accept less than 5 of 5.


---

## 4. Something about the fit card

<!-- YOU WRITE THIS ONE.

     The fit card calls a model, so the same input can produce different words
     each time. That's not a bug — it's the nature of the tool. So what would
     make it acceptable?

     Think about what you'd actually be unhappy to see. A caption that never
     mentions the price? Two different items producing the same opening
     sentence? A card longer than a caption anyone would post? Any of those can
     be turned into a number. -->

Across the five matching example queries in `python app.py examples` (one run
each), at least 4 of the 5 fit cards contain the item's price written as `$N`,
contain the platform name (ignoring capitals), and have 2 to 4 sentences —
counting a sentence as text ending in `.`, `!` or `?`, and ignoring hashtags
and emoji.

**Why this target:**

The prompt asks for all three, but the model writes at `TEMPERATURE = 0.9`, so
the wording changes every run and it sometimes adds an extra sentence or drops
a detail. One card in five drifting is what I'd expect from a free model. Two
would mean my prompt isn't strong enough. In early testing it did break once in
a different way: for the platform sneakers it told the user not to buy them.


---

## 5. Your choice

<!-- YOU WRITE THIS ONE TOO.

     Pick something you actually care about getting right. Speed, the empty
     wardrobe path, what happens when the model can't be reached, whether the
     search respects a price ceiling — anything, as long as it names a number
     or an observable outcome. -->

Given `denim jacket under $50` with the empty wardrobe, the agent completes all
three tools, `session["outfit_suggestion"]` is not empty and does not start
with `No outfit suggestion:`, and it contains none of the ten item names from
the example wardrobe word for word — in at least 4 of 5 tries.

**Why this target:**

`suggest_outfit` switches to a general-advice prompt when `items` is empty, and
that switch is plain code. But the model could still invent "your" pieces that
sound like wardrobe items, and the run depends on two model calls, as in
criterion 1. So 4 of 5, not 5 of 5.


---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
