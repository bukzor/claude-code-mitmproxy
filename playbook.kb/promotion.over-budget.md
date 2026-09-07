# promotion.over-budget

The nearest-sibling search took longer than `DIFF_BUDGET_SECONDS` over the
pass, and the line carries what it measured: fixtures compared, seconds
spent. The search is exhaustive by ruling and quadratic in the collection;
this is the tripwire for a size nobody had seen when that was cheap
(`design/040-design.kb/loudness-policy.md`). The pass still finished -- the
budget is reported, never enforced.

Addressing it is deciding, with the figures in hand, whether the collection
has outgrown exhaustive: an index over the fixtures, pruning the collection,
or a larger budget if the seconds are still nothing against an hourly wake.
Not urgent, and not a reason to skip the glance.
