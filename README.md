# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->

FitFindr takes a plain-language thrift request, such as `vintage graphic tee under $30` or `90s track jacket in size M`, and searches 40 secondhand listings from Depop, Poshmark and thredUp for the best match within that size and budget. It then suggests one or two outfits that pair the find with pieces already in the user's wardrobe, or gives general styling ideas if the wardrobe is empty. Finally it writes a short, post-ready caption (a "fit card") naming the item, its price and the platform. If nothing matches, it stops before styling anything and says whether to change the words, the size or the budget.


---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Finds listings in `data/listings.json` whose words overlap the user's description, after dropping anything over the price ceiling or in the wrong size, and ranks them best match first.
- **Inputs:** `description` (str) — keywords like `"vintage graphic tee"`; `size` (str or None) — e.g. `"M"` or `"8"`, None skips the size filter; `max_price` (float or None) — inclusive ceiling in dollars, None skips the price filter.
- **Returns:** A `list[dict]` of at most `config.SEARCH_RESULT_LIMIT` (10) listing dicts, highest keyword score first. Each dict is the listing exactly as stored: `id`, `title`, `description`, `category`, `style_tags` (list), `size`, `condition`, `price` (float), `colors` (list), `brand` (str or None), `platform`.
  - *Scoring:* each description keyword (lower-cased, stop words like "for"/"under"/"size" removed) scores 2 if it appears in the title or a style tag, 1 if it appears only in the description, category, colors or brand. Listings scoring 0 are dropped. Ties are broken by how many keywords appear in the title, then by file order.
  - *Size match:* the listing's size is split into tokens on spaces, `/` and brackets, and the requested size (upper-cased, with any `US` / `SIZE` prefix removed) must equal one of those tokens. So `M` matches `S/M` and `M/L` but `L` does **not** match `XL`, and `8` matches `US 8` but not `US 8.5`. A listing whose size starts with `One Size` matches any requested size.
- **When it has nothing:** An empty list `[]` — never None, never an exception. That includes an empty or all-stop-word description.

### `suggest_outfit`

- **What it does:** Asks the model for one or two outfits built around the thrifted item, using pieces the user already owns when there are any.
- **Inputs:** `new_item` (dict) — one listing dict, as returned by `search_listings`; `wardrobe` (dict) — `{"items": [ ... ]}` where each item has `id`, `name`, `category`, `colors` (list), `style_tags` (list), `notes`. `items` may be an empty list.
- **Returns:** A non-empty `str` of outfit suggestions. With wardrobe items, each outfit names pieces from the wardrobe by their `name`. With an empty wardrobe, it is general styling advice for the item (what kinds of pieces to pair it with) instead.
- **When it has nothing:** An empty wardrobe is not "nothing" — it returns general advice, as above. If `new_item` is empty/None, or the model returns blank text, it returns a descriptive message string starting `"No outfit suggestion:"` rather than `""` or raising.

### `create_fit_card`

- **What it does:** Asks the model for a short, post-ready caption about the find and how it's styled.
- **Inputs:** `outfit` (str) — the text `suggest_outfit` returned; `new_item` (dict) — the same listing dict that went into `suggest_outfit`.
- **Returns:** A `str` caption of two to four sentences that names the item, its price (e.g. `$24`) and its platform once each, and describes the vibe of the outfit. Brand is mentioned only if the listing has one. Wording varies run to run (`TEMPERATURE = 0.9`).
- **When it has nothing:** If `outfit` is empty or only whitespace (or the model returns blank text), it returns the message string `"No fit card: there was no outfit suggestion to caption."` — never `""`, never an exception.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, put a message in `session["error"]` that says which part of the query to change (the words, the size, or the price — and the cheapest matching price when the price was the problem) and stop, leaving `selected_item`, `outfit_suggestion` and `fit_card` as None. Otherwise take the first result as `session["selected_item"]` and go to `suggest_outfit`, then `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex, in `agent.py::parse_query`. A price comes from `under/below/less than/max/up to $N` or a bare `$N`; a size comes from `size X` or `in size X`. Both phrases are cut out of the query and what's left is the description. No model call. To write the empty-search message, `agent.py::no_results_message` re-runs `search_listings` with one filter removed at a time to find which filter emptied the results.

**What moves through the session:** `query` → `parsed` (`description`, `size`, `max_price`) → `search_results` (the list from `search_listings`) → `selected_item` (`search_results[0]`, read back out of the session for both later tools) → `outfit_suggestion` (from `suggest_outfit(session["selected_item"], session["wardrobe"])`) → `fit_card` (from `create_fit_card(session["outfit_suggestion"], session["selected_item"])`). On the empty path only `parsed`, `search_results` (`[]`) and `error` are set. The loop is a `while` over a `next_step` value (`search` → `suggest` → `fit_card` → `done`, or `search` → `done`), with `trace.check_iterations` on each pass.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'denim jacket under $50'

  Found:    Denim Jacket — Light Wash, Cropped — $42.0 on poshmark

  Outfit:   Outfit 1:
Pair the new light wash Wrangler jacket with the white ribbed tank top tucked into your baggy straight-leg jeans, dark wash. Add the chunky white sneakers and finish with the black crossbody bag for an easy streetwear look.

Outfit 2:
Layer the jacket over the white ribbed tank top paired with your wide-leg khaki trousers. Cinch the look with the brown leather belt and ground the outfit using the black combat boots.

  Fit card: Snagged this cropped light wash Wrangler jacket on Poshmark for just $42, and I am obsessed. It instantly pulls together an easy streetwear vibe with baggy jeans and chunky sneakers, or a cooler, edgier look over khaki trousers and combat boots. 🧥✨ #thrifted #streetwear

2 model calls this session, 616 prompt + 154 output tokens
```

And the empty-search branch:

```
$ python app.py ask 'designer ballgown size XXS under $5'

  Nothing matched "designer ballgown" in size XXS under $5. None of the listings mention those words — try a more general item word like 'tee', 'jeans', 'jacket' or 'sneakers', or a style like 'vintage' or '90s'.

0 model calls this session
```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
[{'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', 'description': 'Vintage-style bootleg tee with faded graphic. Slightly boxy fit. 100% cotton, soft and worn-in.', 'category': 'tops', 'style_tags': ['graphic tee', 'vintage', 'grunge', 'streetwear', 'band tee'], 'size': 'L', 'condition': 'good', 'price': 24.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.', 'category': 'tops', 'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'], 'size': 'S/M', 'condition': 'excellent', 'price': 18.0, 'colors': ['white', 'pink', 'purple'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_033', 'title': 'Vintage Band Tee — Faded Grey', 'description': 'Faded grey band-style tee with distressed graphic. Crew neck. Fits boxy. Well-loved but no holes or major damage.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'band tee', 'graphic tee', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 19.0, 'colors': ['grey', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_015', 'title': 'Vintage Graphic Hoodie — Faded Black', 'description': 'Faded black pullover hoodie with barely-visible vintage graphic on the chest. Cozy interior. Some pilling but adds to the worn-in look.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'graphic', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 26.0, 'colors': ['black', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_017', 'title': 'Mesh Long-Sleeve Top — Black', 'description': 'Sheer black mesh long-sleeve. Great for layering under a graphic tee or over a bralette. Stretchy material, fits true to size.', 'category': 'tops', 'style_tags': ['y2k', 'grunge', 'goth', 'layering'], 'size': 'S/M', 'condition': 'excellent', 'price': 15.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_011', 'title': 'Low-Rise Cargo Pants — Khaki', 'description': 'Y2K era low-rise cargo pants. Lots of pockets. Khaki color, slightly distressed at the hems. Great for layering with a long tee.', 'category': 'bottoms', 'style_tags': ['y2k', 'cargo', '2000s', 'streetwear'], 'size': 'W29', 'condition': 'fair', 'price': 27.0, 'colors': ['khaki', 'tan'], 'brand': None, 'platform': 'poshmark'}]

$ python -c "from tools import search_listings; print(search_listings('designer ballgown', size='XXS', max_price=5))"
[]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
Outfit 1: Casual streetwear
Pair the vintage Levi's 501 jeans with the white ribbed tank top tucked in. Add the brown leather belt, black combat boots, and the slightly cropped vintage black denim jacket on top. Finish with the black crossbody bag.

Outfit 2: Cozy minimal
Wear the Levi's 501 jeans with the oversized grey crewneck sweatshirt pulled loosely over the waistband. Slip on the chunky white sneakers and wear the black crossbody bag for an easy, everyday look.

$ python -c "from tools import suggest_outfit; from utils.data_loader import get_empty_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_empty_wardrobe()))"
Outfit one: casual streetwear. Pair the 501s with an oversized graphic band t-shirt, a distressed black leather jacket, and chunky black loafers or retro white sneakers. Add a silver chain necklace.

Outfit two: smart-casual classic. Tuck a crisp white oversized button-down shirt into the waistband, add a thick brown leather belt, and wear them with suede brown ankle boots or classic canvas slip-ons. Toss on a tortoiseshell pair of sunglasses to finish the look.
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
Scored these vintage Levi's 501 jeans in the absolute best medium wash on Depop for just $38. Threw them on with crisp white sneakers for that effortless, off-duty running errands kind of vibe. Absolute closet staple unlocked. 👖✨ 

#thriftfinds #vintagelevis

$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('', load_listings()[0]))"
No fit card: there was no outfit suggestion to caption.
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:*
- *What came back:*
- *What I changed:*

**Moment 2**

- *What I asked for:*
- *What came back:*
- *What I changed:*

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
