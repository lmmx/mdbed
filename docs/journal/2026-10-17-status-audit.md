# 2026-10-17: Status Audit

mdbed was written in a single day (2025-03-01) as the first stage of a larger idea:
being able to say how a text has changed over time by correlating parts of one
version with parts of another. When a person edits a document they can easily see
what went where; a machine cannot. The plan was to break a markdown document into
nodes (headings, paragraphs, list items), embed each node, and compare nodes across
documents by embedding similarity. The sibling repo `lmmx/lit-embs` was meant to hold
the higher-level "literate embeddings" framing on top: what went where, and what was
added or removed, "similar to git content-addressing but for embeddings".

This audit was done some 19 months later to recover the state of the project. The
git history has seven substantive commits, all on 2025-03-01 (initial commit, two
lint passes, packaging, the polars-ls dependency fix, "stop at leaf nodes to avoid
too many nodes", and a revert of a temporary dedup fix). Every commit since then is
an automated pre-commit hook update (#13 through #42). Nothing substantive has moved.

## How the audit was run

The package was installed into a scratch Python 3.12 venv with `uv pip install -e
'.[polars]'`. The unpinned install failed: the newest polars-fastembed (0.1.17) has no
x86_64 Linux wheel, so uv tried to build it from source and the build failed (see
`2026-10-17-polars-fastembed-wheels.md`). Pinning `polars-fastembed==0.1.3`, the
release closest to when mdbed was written that still ships an x86_64 manylinux wheel,
together with `polars<2` (polars 2.0 removed a method mdbed calls), got a working
install. The CLI was then run against `example/data/` and against a
scratch directory with a mix of `.md` and `.txt` files. The parser was probed with
minimal markdown snippets, and the polars-fastembed `retrieve()` signature was checked
on 0.1.2 (the declared minimum), 0.1.3 and 0.1.17 (from the sdist source).

## Verdict

mdbed is not usable. It gets as far as turning markdown into embedded nodes, which is
the input to the step that matters, and then crashes in that step. The headline
problems, each with its own entry:

- The similarity step crashes: a leftover `breakpoint()`, then a `TypeError` from a
  `retrieve()` keyword that has never existed. Even if it ran, it would pair the
  wrong nodes, because it reads ranks from a sorted result as if they were row ids
  (`2026-10-17-similarity-search.md`).
- Matching is all-against-all, including within the same file. There is no notion
  of "document A at time t against document A at t+1"
  (`2026-10-17-cross-document-pairing.md`).
- The markdown parser drops content: inline formatting text, nested bullets, and any
  structural path (`2026-10-17-markdown-node-extraction.md`).
- File discovery and the CLI diverge from their own help text: `mdbed list` does not
  exist, the `.md` filter is broken, and non-markdown files get embedded
  (`2026-10-17-cli-file-discovery.md`).
- The project no longer installs on x86_64 Linux without a polars-fastembed pin, and
  on polars ≥ 2.0 it crashes even earlier, on a removed `with_row_count`
  (`2026-10-17-polars-fastembed-wheels.md`).
- The README is a copy of lit-embs's README, and the package metadata claims Beta
  (`2026-10-17-readme-and-metadata.md`).

What was built is the embed half: comrak markdown-to-HTML parsing, an `HTMLParser`
subclass that pulls text-bearing nodes into a polars DataFrame, embedding through
polars-fastembed with `Xenova/bge-small-en-v1.5`, file discovery through polars-ls, and
a click CLI. What was never built is the matching half: alignment ("this node in v1
became that node in v2"), classification into moved, edited, split, merged, added and
deleted, and anything in lit-embs.

The framing is sound, but embedding similarity alone will not get there. The hard
part is the matching step with the right constraints. That design work, and the prior
art it should draw on (GumTree, Vecalign, WikiWho, git's move detection, edit-intent
datasets), is recorded in lit-embs: `docs/journal/2026-10-17-prior-art.md`,
`2026-10-17-node-matching-algorithm.md` and `2026-10-17-version-lineage.md`.

## Current State

- Seven substantive commits dated 2025-03-01 make up the authored history, followed by pre-commit-ci autoupdate commits #13 through #42 only
- Markdown parsing renders markdown to HTML with comrak, then extracts nodes with an `HTMLParser` subclass (src/mdbed/markdown.py:111-125, markdown.py:11-108)
- Node extraction returns a polars DataFrame with columns `file`, `tag`, `text`, `attrs`, `path` (src/mdbed/markdown.py:128-166)
- Embedding computes a 384-dimensional `Array(Float32)` column through polars-fastembed `df.fastembed.embed` with default model `Xenova/bge-small-en-v1.5` (src/mdbed/embedding.py:15, embedding.py:33-70)
- Embedding succeeds end to end on the 20 nodes of `example/data/claude_3-7_generation.md` with polars-fastembed 0.1.3 and polars 2.0.0
- File discovery wraps polars-ls `ls` (src/mdbed/utils.py:12-79)
- The click group `mdbed` exposes two subcommands, `embed` and `list-files` (src/mdbed/cli.py:38-39, cli.py:43-119, cli.py:212-242)
- `example/example.py` runs the same parse → embed → similarity pipeline as the CLI over `example/data/`

## Stubbed

- No placeholder implementations: every function in src/mdbed/ contains a full implementation attempt

## Missing

- Similarity search over embeddings produces no output — under polars 2.0.0 `with_row_count` raises `AttributeRemovedError`, and under polars 1.x `retrieve(raw_embedding=...)` raises `TypeError` (src/mdbed/embedding.py:96, embedding.py:104-110)
- Cross-version matching of document A against document B has no code — `find_similar_nodes` compares every node with every other node regardless of file (src/mdbed/embedding.py:73-162)
- Edit classification (moved, edited, split, merged, added, deleted) has no code in mdbed or lit-embs
- Tests have no code — `pytest` appears in the `dev` extra of pyproject.toml but the repository contains no test files

## Divergence

- README describes "What went where" and "What was added/removed" but no code in src/mdbed/ computes either (README.md)
- pyproject.toml classifies the package as "Development Status :: 4 - Beta" while `mdbed embed` crashes on every input that produces nodes (pyproject.toml:12)
