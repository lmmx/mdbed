# 2026-10-17: README and Metadata

Housekeeping found during the audit. None of it blocks functionality, but all of it
misleads a reader about what the package is and what state it is in.

The README is byte-for-byte identical to lit-embs's README (`cmp` reports no
difference). It is titled "Lit. Emb's", describes lit-embs's goal, and its install
instructions say `pip install lit-embs[polars]` / `pip install lit-embs[polars-lts-cpu]`.
Nothing in it names mdbed, the `mdbed` CLI, or how to run it. It was presumably copied
across as a starting point when both repos were scaffolded on the same day and never
rewritten. The pyproject description, "Embed markdown documents and compare their
nodes.", is accurate. The README is not.

pyproject.toml carries the classifier "Development Status :: 4 - Beta", copied from
the shared template. For a package whose main command crashes, "2 - Pre-Alpha" would
describe it honestly.

`find_similar_nodes` uses `DataFrame.with_row_count` three times (embedding.py:96,
138, 152). polars deprecated it in favour of `with_row_index` in the 0.20 series, and
polars 2.0 removed it: under polars 2.0.0 the first call raises
`AttributeRemovedError`, while polars 1.44.2 only warns. Since the `polars` extra has
no upper bound, a fresh install today gets polars 2.x and crashes there first. The
crash itself is recorded in `2026-10-17-similarity-search.md` and
`2026-10-17-polars-fastembed-wheels.md`.

`example/example.py` writes `similar_nodes.csv` into whatever the current working
directory is (example.py:97-99), not next to the example. It never gets that far
because of the similarity crash.

## Current State

- README.md is identical to lit-embs README.md, titled "Lit. Emb's" with lit-embs install commands (README.md)
- pyproject.toml description reads "Embed markdown documents and compare their nodes." (pyproject.toml)
- `find_similar_nodes` calls `DataFrame.with_row_count` at three sites, a method that polars 1.44.2 marks deprecated and polars 2.0.0 removes (src/mdbed/embedding.py:96, embedding.py:138, embedding.py:152)
- `example/example.py` writes `similar_nodes.csv` to the current working directory (example/example.py:97-99)

## Missing

- mdbed-specific README content (package name, CLI usage, pipeline description) has no text in README.md

## Divergence

- README install commands name `lit-embs[polars]` and `lit-embs[polars-lts-cpu]`, not `mdbed` (README.md)
- pyproject.toml classifies the package as "Development Status :: 4 - Beta" while `mdbed embed` crashes before producing results (pyproject.toml:12)
