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



---

## Tool Inventory

### `search_listings`

- **What it does:** Searches `data/listings.json` for items matching a keyword description, optionally filtered by size and a maximum price, and returns the best matches first.
- **Inputs:**
  - `description` (str) — keywords describing the item, e.g. `"vintage graphic tee"`. Lowercased and split into words; common filler words ("a", "the", "for", "looking", "under", "size") are ignored.
  - `size` (str or None) — size to filter by, e.g. `"M"`. `None` means no size filtering.
  - `max_price` (float or None) — inclusive price ceiling, e.g. `30.0`. `None` means no price filtering.
- **Returns:** A list of listing dicts, sorted by match score (highest first), at most `config.SEARCH_RESULT_LIMIT` items. Each dict has: `id`, `title`, `description`, `category`, `style_tags` (list), `size`, `condition`, `price` (float), `colors` (list), `brand` (str or None), `platform`.
  - **Size rule:** both the requested size and the listing's size are lowercased and split into tokens on `/`, spaces, and commas. A listing matches if any token is exactly equal. So `M` matches `S/M`, but `S` does not match `US 9` and `L` does not match `XL`. Listings with no size never match a size filter.
  - **Match score:** the number of description keywords that appear in the listing's title, description, category, style_tags, colors, and brand (brand skipped when None). Listings scoring 0 are dropped.
- **When it has nothing:** Returns an empty list `[]` — never `None`, never an exception.

### `suggest_outfit`

- **What it does:** Uses the model to suggest one or two outfits built around the new item, using pieces from the user's wardrobe.
- **Inputs:**
  - `new_item` (dict) — a listing dict, as returned by `search_listings`.
  - `wardrobe` (dict) — a wardrobe dict with an `"items"` key holding a list of wardrobe item dicts. The list may be empty.
- **Returns:** A non-empty string with one or two outfit suggestions that name specific pieces from the wardrobe by name.
- **When it has nothing:** If `wardrobe["items"]` is empty, returns a non-empty string of general styling advice for the item (what it pairs well with) instead of raising or returning `""`.

### `create_fit_card`

- **What it does:** Uses the model to write a short, casual social-media caption about the thrifted find and how it's styled.
- **Inputs:**
  - `outfit` (str) — the outfit suggestion string returned by `suggest_outfit`.
  - `new_item` (dict) — the listing dict for the item.
- **Returns:** A 2–4 sentence caption that reads like a real post (not a product description), mentions the item, its price, and its platform once each, and describes the vibe. Wording varies between runs because the model runs at a non-zero temperature.
- **When it has nothing:** If `outfit` is empty or only whitespace, returns the string `"Can't write a fit card without an outfit suggestion."` instead of raising.

---

## Planning Loop

**Branch rule:** If `search_listings` returns an empty list, the loop puts a message in `session["error"]` that repeats what was searched (description, size, max price) and names what to change (raise the price limit, drop the size, or use broader words), then returns the session without calling `suggest_outfit` or `create_fit_card`. Otherwise, it puts the first (highest-scoring) result in `session["selected_item"]` and continues to `suggest_outfit`, then `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex, no model call. The price is the number after "under", "below", "less than", "max", or "<" (with or without `$`), converted to a float. The size is the token after the word "size". Whatever words remain, minus filler words, become the description. If no price or size is found, that value is `None` and its filter is skipped.

**What moves through the session:** `query` → `parsed` (description, size, max_price) → `search_results` (full list from `search_listings`) → `selected_item` (first result, passed to `suggest_outfit`) → `outfit_suggestion` (passed with `selected_item` to `create_fit_card`) → `fit_card`. Each tool reads its inputs from the session, not from the previous call's return value. If the run stops early, `error` is set and the later fields stay `None`.

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask '...'

```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"

```

```
$ python -c "from tools import suggest_outfit; ..."

```

```
$ python -c "from tools import create_fit_card; ..."

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
