"""
The three FitFindr tools.

Each one is a standalone function that can be called and tested on its own,
before any of them are wired into the loop.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

The specs for all three are in the Tool Inventory section of README.md.
"""

import re

import config
from generate import generate
from utils.data_loader import load_listings


# ── shared helpers ────────────────────────────────────────────────────────────

# Words that say nothing about the item itself. Dropping them keeps a query like
# "looking for a vintage tee" from matching listings on "for" or "a".
STOPWORDS = {
    "a", "an", "the", "for", "and", "or", "with", "in", "on", "of", "to",
    "is", "it", "that", "this", "some", "something", "any",
    "looking", "want", "need", "find", "get", "me", "my", "please",
    "under", "below", "less", "than", "max", "around", "about",
    "size", "price", "cheap", "dollars",
}

# Word sizes a user might type, mapped to the letter sizes the data uses.
# Longer phrases are replaced first so "extra large" doesn't become "extra l".
SIZE_WORDS = {
    "extra small": "xs",
    "x-small": "xs",
    "extra large": "xl",
    "x-large": "xl",
    "small": "s",
    "medium": "m",
    "large": "l",
}


def _tokens(text: str) -> list[str]:
    """Lowercase and split on anything that isn't a letter or digit."""
    return [t for t in re.split(r"[^a-z0-9]+", str(text).lower()) if t]


def _stem(word: str) -> str:
    """Strip a trailing 's' from longer words so 'tees' matches 'tee'."""
    return word[:-1] if len(word) > 3 and word.endswith("s") else word


def _size_tokens(size: str) -> set[str]:
    """
    Turn a size string into a set of whole tokens.

    "S/M"            → {"s", "m"}
    "XL (oversized)" → {"xl", "oversized"}
    "W30 L30"        → {"w30", "l30"}
    "medium"         → {"m"}
    """
    s = str(size).lower().strip()
    for word in sorted(SIZE_WORDS, key=len, reverse=True):
        s = re.sub(rf"\b{re.escape(word)}\b", SIZE_WORDS[word], s)
    return set(_tokens(s))


def _listing_words(listing: dict) -> set[str]:
    """Every searchable word in a listing, stemmed. Brand is skipped when None."""
    parts = [
        listing.get("title", ""),
        listing.get("description", ""),
        listing.get("category", ""),
    ]
    parts += listing.get("style_tags") or []
    parts += listing.get("colors") or []
    if listing.get("brand"):
        parts.append(listing["brand"])
    return {_stem(t) for t in _tokens(" ".join(str(p) for p in parts))}


def _format_price(price) -> str:
    """24.0 → "$24", 24.5 → "$24.50"."""
    price = float(price)
    return f"${price:.0f}" if price.is_integer() else f"${price:.2f}"


def _describe_item(item: dict) -> str:
    """A one-paragraph description of a listing, for prompts."""
    lines = [
        f"Title: {item.get('title', 'Unknown item')}",
        f"Category: {item.get('category', 'unknown')}",
        f"Description: {item.get('description', '')}",
        f"Style tags: {', '.join(item.get('style_tags') or [])}",
        f"Colors: {', '.join(item.get('colors') or [])}",
        f"Size: {item.get('size', 'unknown')}",
        f"Condition: {item.get('condition', 'unknown')}",
        f"Price: {_format_price(item.get('price', 0))}",
        f"Platform: {item.get('platform', 'unknown')}",
    ]
    if item.get("brand"):
        lines.append(f"Brand: {item['brand']}")
    return "\n".join(lines)


def _describe_wardrobe_item(piece: dict) -> str:
    """
    One line per wardrobe piece. Written to work with whatever fields the
    wardrobe schema uses: every non-empty field except the id is included.
    """
    fields = []
    for key, value in piece.items():
        if key == "id" or value in (None, "", []):
            continue
        if isinstance(value, list):
            value = ", ".join(str(v) for v in value)
        fields.append(f"{key}: {value}")
    return "- " + "; ".join(fields)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings for items matching a description, and optionally a size
    and a price ceiling.

    Returns a list of listing dicts, best match first, at most
    config.SEARCH_RESULT_LIMIT of them. Returns [] when nothing matches.
    """
    keywords = [
        _stem(w)
        for w in _tokens(description or "")
        if w not in STOPWORDS and len(w) > 1
    ]
    if not keywords:
        return []

    wanted_size = _size_tokens(size) if size else None

    scored = []
    for listing in load_listings():
        # Price filter (inclusive).
        if max_price is not None:
            price = listing.get("price")
            if price is None or float(price) > float(max_price):
                continue

        # Size filter: whole-token match only, so "l" never matches "xl".
        if wanted_size is not None:
            listing_size = listing.get("size")
            if not listing_size or not (wanted_size & _size_tokens(listing_size)):
                continue

        # Score by how many keywords appear in the listing.
        words = _listing_words(listing)
        score = sum(1 for k in keywords if k in words)
        if score > 0:
            scored.append((score, listing))

    # Highest score first. sort() is stable, so ties keep file order.
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [listing for _, listing in scored[: config.SEARCH_RESULT_LIMIT]]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    Returns a non-empty string. With an empty wardrobe, returns general styling
    advice for the item instead.
    """
    pieces = (wardrobe or {}).get("items") or []
    item_text = _describe_item(new_item)

    if not pieces:
        prompt = (
            "You are a friendly thrift-store stylist.\n\n"
            "Someone is thinking about buying this secondhand item:\n"
            f"{item_text}\n\n"
            "They haven't told you what's in their wardrobe. Give general styling "
            "advice: describe one or two outfits built around this item, naming the "
            "kinds of pieces it pairs well with (for example 'straight-leg dark "
            "jeans' or 'chunky white sneakers'). Keep it to 3-5 sentences. Plain "
            "text, no headings."
        )
    else:
        wardrobe_text = "\n".join(_describe_wardrobe_item(p) for p in pieces)
        prompt = (
            "You are a friendly thrift-store stylist.\n\n"
            "Someone is thinking about buying this secondhand item:\n"
            f"{item_text}\n\n"
            "Here is what they already own:\n"
            f"{wardrobe_text}\n\n"
            "Suggest one or two complete outfits built around the new item. Use "
            "pieces from their wardrobe and refer to each one by name so they know "
            "exactly what to grab. Keep it to 3-5 sentences. Plain text, no headings."
        )

    response = (generate(prompt) or "").strip()
    if not response:
        return (
            f"Try the {new_item.get('title', 'item')} with simple basics in neutral "
            "colors, like straight-leg jeans and clean sneakers."
        )
    return response


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    Returns a two-to-four sentence caption. If `outfit` is empty or whitespace,
    returns a descriptive message instead of raising.
    """
    if not outfit or not outfit.strip():
        return "Can't write a fit card without an outfit suggestion."

    price = _format_price(new_item.get("price", 0))
    platform = new_item.get("platform", "a thrift app")
    title = new_item.get("title", "this find")

    prompt = (
        "Write a caption for a social media post about a thrifted outfit.\n\n"
        f"The item: {title}\n"
        f"Price: {price}\n"
        f"Found on: {platform}\n"
        f"How it's styled: {outfit}\n\n"
        "Rules:\n"
        "- 2 to 4 sentences, written like a real person posting, not a product "
        "description.\n"
        f"- Mention the item, the price written exactly as {price}, and {platform} "
        "once each.\n"
        "- Be specific about the vibe of the outfit.\n"
        "- No hashtags, no bullet points, no quotation marks around the caption.\n"
        "Reply with only the caption."
    )

    response = (generate(prompt) or "").strip()
    if not response:
        return f"Found this {title} on {platform} for {price} and I'm obsessed."
    return response