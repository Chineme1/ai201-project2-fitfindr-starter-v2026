# Acceptance Criteria — FitFindr

1. Given a query that matches at least one listing, the agent completes all
   three tool calls and returns a fit card — in at least 4 of 5 tries.

   **Why this target:** Two of the three tools call the model over the network,
   so a run can fail for reasons outside my code (a timeout or a rate-limit
   error). Allowing one miss in five accounts for that. Two or more misses would
   mean something in my own code is failing, not the network.

2. Given a query that matches no listings, the agent stops before calling
   suggest_outfit and returns a message naming what to change — 5 of 5 tries.

   **Why this target:** Everything before the branch (parsing and
   search_listings) is plain Python with no model call, so the same input
   always takes the same path. Nothing random can cause a miss, so any failure
   here is a bug, and 5 of 5 is the only honest target.

3. Given a query that matches at least one listing, the `id` of
   `session["selected_item"]` equals the `id` of `session["search_results"][0]`
   and equals the `id` of the item passed into `suggest_outfit` (checked by
   printing the session and the tool's input), and the user never re-enters
   the item — 5 of 5 tries.

   **Why this target:** Passing the item from search to suggest_outfit is done
   entirely by my code through the session dictionary; the model is not
   involved. Comparing `id` fields is an exact check with no judgment call, so
   anything below 5 of 5 means the state handling is broken.

4. Given the same matching query run 5 times with `CACHE_ENABLED = False`, each
   fit card is 2–4 sentences (counted by `.`, `!`, or `?`), contains the
   selected item's price (as `$24` or `$24.00`) and its platform name, and no
   two of the five captions are word-for-word identical — format holds in at
   least 4 of 5 tries, and 0 of 5 are exact duplicates.

   **Why this target:** The caption comes from the model, so the wording should
   change between runs. That variation is acceptable, and identical captions
   would mean caching or temperature is masking it. The model can occasionally
   ignore an instruction (dropping the platform or running to five sentences),
   so I allow one formatting miss. Duplicates get zero tolerance because they
   point to a configuration problem, not model randomness.

5. Given each of these three queries — `'graphic tee size L under $30'`,
   `'jeans size W30'`, and `'top size S'` — every listing that search_listings
   returns has a price at or below the stated maximum (when one is given) and a
   size containing the requested size as a whole token (so no `XL` or `L30` for
   `L`, and no `US 9` for `S`) — 5 of 5 tries for each query.

   **Why this target:** Filtering is deterministic code, so results never change
   between runs, and a single wrong listing is a real bug. A shopper who asked
   for a small top and got shoes would stop trusting every other result. The
   three queries were chosen to hit the traps in this data: letter sizes inside
   longer sizes (`L` vs `XL`), waist sizes (`W30 L30`), and shoe sizes that
   contain the letter `s`.