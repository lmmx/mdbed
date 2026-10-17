# 2026-10-17: Cross-Document Pairing

The motivating question is "how did this document change between version t and
version t+1?". That is a bipartite question: nodes of A on one side, nodes of A′ on
the other, with an edge wherever one became the other. mdbed never frames it that
way. The CLI and `example/example.py` concatenate every node from every input file
into one DataFrame (cli.py:163) and hand the whole thing to `find_similar_nodes`,
which compares each node with every other node. That includes nodes from the same
file.

Within-file pairs are noise for the purpose of tracking edits. A document's
"Introduction" heading and its first bullet about the introduction will score highly
against each other, and that says nothing about what changed. Worse, with four
example files the output mixes every pairing of files (source prompt ↔ Claude, Claude
↔ o1, o1 ↔ GPT-4.5, …) into one ranked list, with no column that marks a pair as
cross-version, and no way to say which file is "before" and which is "after".

There is also no assignment step. Even if similarity worked, the output is "every pair
above 0.7", not "each node in A maps to at most k nodes in A′ (or to nothing)". A
heading like "Introduction" will clear 0.7 against several unrelated short nodes. The
result is a soup of edges, not an alignment. Turning edges into an alignment (an
injective matching with unmatched = added/deleted, or a bounded many-to-many for
splits and merges) is the real algorithmic content of the project. Its design space
(GumTree-style tree matching, Vecalign-style monotone DP, Hungarian with a null cost,
optimal transport) is recorded in lit-embs `docs/journal/2026-10-17-node-matching-algorithm.md`.

The single fixed cosine threshold of 0.7 (cli.py:79-84, example.py:76) is a related
gap. A global constant cannot separate "edited" from "replaced". bge-small cosine
scores between *unrelated* sentences in the same domain sit well above zero, and that
baseline varies by document. Vecalign's answer to the same problem, normalising each
pair's cosine against randomly sampled pairs and setting the skip cost as a quantile
of the observed 1-1 cost distribution, is the most directly reusable idea and is
written up in lit-embs `docs/journal/2026-10-17-prior-art.md`.

The minimal version of this task is: accept exactly two inputs (or an ordered list of
versions), compute the similarity matrix between consecutive versions only, and emit
pairs tagged with `source_file`/`target_file` in before → after order.

## Current State

- `mdbed embed` concatenates nodes from every input file into one DataFrame before similarity search (src/mdbed/cli.py:146-163)
- `find_similar_nodes` takes a single DataFrame and compares each row against all rows of the same DataFrame (src/mdbed/embedding.py:73-121)
- Pair selection keeps every pair with similarity at or above a fixed threshold, default 0.7 (src/mdbed/cli.py:79-84, src/mdbed/embedding.py:114, example/example.py:76)
- `example/example.py` runs the same all-against-all comparison over all four files in `example/data/`, including same-file pairs

## Missing

- Version ordering has no code — no CLI argument or function parameter identifies one input as the earlier version and another as the later version (src/mdbed/cli.py:110-118)
- Same-file pair exclusion has no code — `find_similar_nodes` never compares the `file` column of the two nodes in a pair (src/mdbed/embedding.py:113-121)
- One-to-one or bounded many-to-many assignment has no code — output keeps every pair above threshold, so one node can pair with any number of nodes (src/mdbed/embedding.py:113-121)
- Unmatched-node reporting (nodes with no counterpart, i.e. added or deleted content) has no code
- Per-document threshold calibration has no code — the threshold applies as one global constant (src/mdbed/cli.py:79-84)

## Divergence

- README promises "What was added/removed" but no code identifies nodes without a counterpart in another document (README.md)
