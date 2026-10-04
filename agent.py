"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

    python agent.py      runs both example paths below
"""

import re

import config  # noqa: F401
import trace
from tools import search_listings, suggest_outfit, create_fit_card
from generate import ModelUnavailable  # noqa: F401 — handled in unit 4


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.
    """
    return {
        "query": query,               # what the user typed
        "parsed": {},                 # description / size / max_price pulled out of it
        "search_results": [],         # everything search_listings returned
        "selected_item": None,        # the one chosen — goes into suggest_outfit
        "outfit_item_id": None,       # id of the item actually passed to suggest_outfit
        "wardrobe": wardrobe,         # the user's wardrobe
        "outfit_suggestion": None,    # what suggest_outfit returned
        "fit_card": None,             # what create_fit_card returned
        "error": None,                # set when the run ended early
    }


# ── query parsing (regex, no model call) ──────────────────────────────────────

# "under $30", "below 30", "less than $25.50", "max $40", "up to $20", "< 30"
PRICE_RE = re.compile(
    r"(?:under|below|less\s+than|max|up\s+to|<)\s*\$?\s*(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
# A bare "$30" with no keyword in front is also treated as a ceiling.
BARE_PRICE_RE = re.compile(r"\$\s*(\d+(?:\.\d+)?)")
# "size M", "size S/M", "size W30", "size medium", "size extra large"
SIZE_RE = re.compile(
    r"\bsize\s+((?:extra\s+|x-)?(?:small|medium|large)\b|[a-z0-9/]+)",
    re.IGNORECASE,
)


def _cut(text: str, match: re.Match) -> str:
    """Remove a regex match from the text."""
    return text[: match.start()] + " " + text[match.end():]


def parse_query(query: str) -> dict:
    """
    Pull a description, a size, and a max price out of a plain-language query.

    "vintage graphic tee under $30, size M"
        → {"description": "vintage graphic tee", "size": "M", "max_price": 30.0}

    Anything not found is None. The description is whatever words are left;
    search_listings drops filler words like "looking" and "for" itself.
    """
    text = query or ""

    max_price = None
    match = PRICE_RE.search(text) or BARE_PRICE_RE.search(text)
    if match:
        max_price = float(match.group(1))
        text = _cut(text, match)

    size = None
    match = SIZE_RE.search(text)
    if match:
        size = match.group(1).strip()
        text = _cut(text, match)

    description = " ".join(re.sub(r"[,.!?;:]", " ", text).split())
    return {"description": description, "size": size, "max_price": max_price}


# ── the message for an empty search ───────────────────────────────────────────

def _no_results_message(parsed: dict) -> str:
    """
    Say what was searched and what to change.

    Re-runs the search with each filter removed to find out which one is
    blocking results, so the advice is specific rather than generic.
    """
    desc = parsed.get("description") or ""
    size = parsed.get("size")
    price = parsed.get("max_price")

    if not desc:
        return (
            "I couldn't tell what item you're looking for. Describe it in a few "
            "words, for example: 'vintage graphic tee under $30, size M'."
        )

    searched = f'"{desc}"'
    if size:
        searched += f" in size {size}"
    if price is not None:
        searched += f" under ${price:g}"

    hints = []
    if price is not None and search_listings(desc, size, None):
        hints.append(f"raise your price limit above ${price:g}")
    if size and search_listings(desc, None, price):
        hints.append(f"remove the size {size} filter or try a nearby size")
    if not hints and (size or price is not None) and search_listings(desc):
        hints.append("remove both the size and price filters")
    if not hints:
        hints.append(
            "use broader or different words for the item, like 'jacket' instead "
            "of 'designer bomber', or 'tee' instead of 'band shirt'"
        )

    return f"No listings matched {searched}. Try to " + ", or ".join(hints) + "."


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Branch rule: if search_listings returns an empty list, put a message in
    session["error"] naming what to change, and return without calling
    suggest_outfit. Otherwise, take the first result and continue.

    Check session["error"] first — if it isn't None, the run ended early and
    the later fields are still None.
    """
    session = new_session(query, wardrobe)
    tool_calls = 0

    # Parse the query into the session.
    session["parsed"] = parse_query(session["query"])

    # Tool 1: search, reading its inputs from the session.
    tool_calls += 1
    trace.check_iterations(tool_calls)
    parsed = session["parsed"]
    session["search_results"] = search_listings(
        parsed["description"], parsed["size"], parsed["max_price"]
    )

    # ⚠️ THE BRANCH: nothing found → stop here, never call suggest_outfit.
    if not session["search_results"]:
        session["error"] = _no_results_message(session["parsed"])
        return session

    # Choose the best match.
    session["selected_item"] = session["search_results"][0]

    # Tool 2: outfit, reading the item and wardrobe from the session.
    tool_calls += 1
    trace.check_iterations(tool_calls)
    item = session["selected_item"]
    session["outfit_item_id"] = item.get("id")
    session["outfit_suggestion"] = suggest_outfit(item, session["wardrobe"])

    # Tool 3: fit card, reading the outfit and item from the session.
    tool_calls += 1
    trace.check_iterations(tool_calls)
    session["fit_card"] = create_fit_card(
        session["outfit_suggestion"], session["selected_item"]
    )

    return session


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