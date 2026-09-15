# Daily comparison with 15 references

The immutable closed civil day (America/Sao_Paulo) is the input. `data/technology15.json` is the reference registry selected by the owner. No live recollection or rolling window is substituted for the closure. Reference publications are removed from the street corpus before comparison; a URL cannot confirm itself.

`python -m reference_compare.main` processes closed days not yet saved for this version and registry hash. GitHub runs it after the daily workflow, and the dashboard rebuilds after comparison. Reports are persisted and read back from R2, without changing the closure. Changing classification or matching logic requires a new VERSION. Original body object keys are frozen by the closure; if an object is unreadable the article remains in the denominator and cannot create a body-based match.

Sentence Transformers compares title and first 1,200 characters, using the existing versioned embedding cache. Both articles need at least 200 available body characters. Candidates require title and lead similarity >= 0.80, numeric compatibility and the existing conservative lexical gate. Estimated copies remain visible and do not establish independent confirmation. Scores are not calibrated probabilities. Related events with different numbers can be missed; cross-language pairs without shared lexical anchors can be missed. Editorial validation remains pending.

For each country, continent and world, street topic groups come from the existing closure. The same worldwide reference corpus is compared with each geography. Share denominators use estimated distinct texts, with different editorial breadth; reference matches can belong to multiple street groups, so reference topic shares are not additive. Source country denotes publisher geography, not the location of the event. Worldwide counts are computed directly, never by summing countries.

## Frontend contract

`data/explorer/manifest.json`: closed `closures[]` entries expose `reference_comparison` (relative JSON path), or `reference_status=waiting_for_comparison`. A pending record must not display zero matches as if processing had completed.

The comparison JSON contains schema_version, version, closure_id, day, cutoff, generated_at, counts, reference_manifest, source_coverage, method, articles, reference_without_match and scope_files. `scope_files.country/continent/globe` link to geography objects with totals and topics. Each topic includes street/reference article IDs, distinct-text counts, shares, matched sources and all pair evidence. `articles` maps IDs to public titles, source URLs and publisher metadata. All paths resolve relative to `data/explorer/`. Cloudflare data files contain no storage object keys or credentials.

Each evidence pair has street_id, reference_id, decision, reason, title_similarity, lead_similarity, lead_jaccard, similarity_score and an explicitly uncalibrated probability marker. Decisions distinguish estimated copies, possible republication and same-subject candidates. No stance/angle inference is implemented; angle_analysis is null. `no_match_observed` and reference_without_match mean only no match within the acquired corpus and conservative rules, never proof of publisher silence.

Source checks are bounded by the civil day plus closing-midnight slot and frozen acquisition cutoff. Checks overwritten after cutoff cannot reconstruct history and are marked partial/unverifiable. Five successful slots do not prove exhaustive publisher coverage. The UI exposes article/body counts and collection gaps for all 15 sources.

The current integration is `/references.html`, linked from the main dashboard. A future site can consume these static contracts without direct database credentials.
