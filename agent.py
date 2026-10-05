"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re

import config
import trace
from tools import search_listings, suggest_outfit, create_fit_card
from generate import ModelUnavailable


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    TODO — build this, following the branch rule you wrote in Milestone 2.

      1. Start a session with new_session().

      2. Count the times round the loop, and call trace.check_iterations(count)
         on each one before you go again. It raises when the count passes
         MAX_ITERATIONS in config.py — see trace.py.

      3. Parse the query into a description, a size, and a max_price. Regex,
         string splitting, or asking the model are all fine — say which you
         chose in your README. Put the result in session["parsed"].

      4. Call search_listings() with what you parsed.
         Put the results in session["search_results"].

         ⚠️ THIS IS THE BRANCH. If nothing came back:
              - put a message in session["error"] saying what the user could
                change — "No results" is not that message
              - return the session
              - do NOT call suggest_outfit with nothing

      5. Choose an item — the first result is fine. Put it in
         session["selected_item"].

      6. Call suggest_outfit() with the selected item and the wardrobe.
         Put the result in session["outfit_suggestion"].

      7. Call create_fit_card() with the outfit and the item.
         Put the result in session["fit_card"].

      8. Return the session.

    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """
    session = new_session(query, wardrobe)
    session["parsed"] = parse_query(query)

    # Each pass runs one step, then picks the next step from what that step
    # left in the session. "done" ends the loop.
    next_step = "search"
    count = 0
    while next_step != "done":
        count += 1
        trace.check_iterations(count)

        if next_step == "search":
            parsed = session["parsed"]
            session["search_results"] = search_listings(
                parsed["description"], parsed["size"], parsed["max_price"]
            )
            # THE BRANCH: nothing found → explain what to change, and stop.
            if not session["search_results"]:
                session["error"] = no_results_message(parsed)
                next_step = "done"
            else:
                session["selected_item"] = session["search_results"][0]
                next_step = "suggest"

        elif next_step == "suggest":
            session["outfit_suggestion"] = suggest_outfit(
                session["selected_item"], session["wardrobe"]
            )
            next_step = "fit_card"

        elif next_step == "fit_card":
            session["fit_card"] = create_fit_card(
                session["outfit_suggestion"], session["selected_item"]
            )
            next_step = "done"

    return session


# ── query parsing ─────────────────────────────────────────────────────────────

_PRICE = re.compile(
    r"\b(?:under|below|less than|max|up to|<)\s*\$?\s*(\d+(?:\.\d+)?)|\$(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
_SIZE = re.compile(r"\b(?:in\s+)?(?:a\s+)?size\s+([a-z0-9./]+)", re.IGNORECASE)


def parse_query(query: str) -> dict:
    """
    Pull a max_price and a size out of the query with regex; whatever is left
    is the description.

        "90s track jacket in size M"     → size "M"
        "vintage graphic tee under $30"  → max_price 30.0
    """
    rest = query

    max_price = None
    price = _PRICE.search(rest)
    if price:
        max_price = float(price.group(1) or price.group(2))
        rest = rest[: price.start()] + " " + rest[price.end():]

    size = None
    size_match = _SIZE.search(rest)
    if size_match:
        size = size_match.group(1).upper()
        rest = rest[: size_match.start()] + " " + rest[size_match.end():]

    description = " ".join(rest.replace(",", " ").split())
    return {"description": description, "size": size, "max_price": max_price}


def no_results_message(parsed: dict) -> str:
    """
    Say which part of the query to change. Re-runs the search with one filter
    taken off at a time to find out which one emptied the results.
    """
    desc, size, max_price = parsed["description"], parsed["size"], parsed["max_price"]
    asked = f'"{desc}"' + (f" in size {size}" if size else "") + (
        f" under ${max_price:.0f}" if max_price is not None else ""
    )

    by_words = search_listings(desc)
    if not by_words:
        return (
            f"Nothing matched {asked}. None of the listings mention those words — "
            "try a more general item word like 'tee', 'jeans', 'jacket' or "
            "'sneakers', or a style like 'vintage' or '90s'."
        )

    if size and not search_listings(desc, size=size):
        sizes = sorted({item["size"] for item in by_words})
        return (
            f"Nothing matched {asked}. There are listings for \"{desc}\", but "
            f"none in size {size} — they come in {', '.join(sizes[:6])}. "
            "Try one of those sizes, or leave the size out."
        )

    cheapest = min(search_listings(desc, size=size), key=lambda item: item["price"])
    return (
        f"Nothing matched {asked}. The cheapest match is "
        f"\"{cheapest['title']}\" at ${cheapest['price']:.0f} — try raising "
        f"your budget to ${cheapest['price']:.0f} or more."
    )


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
