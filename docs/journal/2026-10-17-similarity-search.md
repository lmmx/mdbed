# 2026-10-17: Similarity Search

`find_similar_nodes` (src/mdbed/embedding.py:73-162) is where the "what went where"
step was supposed to start: given a DataFrame of embedded nodes, return the pairs
whose cosine similarity clears a threshold. It is the step that crashes, and it is
wrong in three separate ways beyond the crash.

## The crash, three times over

On polars ≥ 2.0 the function never reaches its loop. The first line of real work,
`df.with_row_count("id")` (embedding.py:96), raises `AttributeRemovedError` because
polars 2.0 removed `with_row_count` in favour of `with_row_index` (details in
`2026-10-17-polars-fastembed-wheels.md`). On polars 1.x it only warns, and the
function carries on to the next two failures.

Inside the per-row loop there is a leftover `breakpoint()` (embedding.py:101). Run
normally, that drops into pdb on the first node. With `PYTHONBREAKPOINT=0` the loop
moves on to the real failure:

```
TypeError: FastEmbedPlugin.retrieve() got an unexpected keyword argument 'raw_embedding'
```

The call passes `query=None, raw_embedding=query_embedding` (embedding.py:104-110),
hoping to look up neighbours of an existing vector. polars-fastembed's `retrieve()`
only takes a text `query`, which it embeds itself. The signature is identical on
0.1.2 (the version pinned as the minimum, and the latest release on the day mdbed was
written), 0.1.3, and 0.1.17 (the current release, checked in the sdist source):

```
retrieve(query: str, model_name=None, embedding_column="embedding", k=None,
         threshold=None, similarity_metric="cosine", add_similarity_column=True)
```

So the keyword was never part of the API. This was a call against an API that was
imagined, not one that had been removed.

## Wrong even if it ran

Reading the 0.1.17 source of `retrieve()` shows what it does: it cross-joins the
query embedding onto every row, computes `1 - cosine_distance` as `similarity`,
filters by `threshold`, then **sorts by similarity descending** and takes `head(k)`.
That breaks the loop that consumes it:

- `for j, sim in enumerate(result.select("similarity").to_series())`
  (embedding.py:113) treats `j` as a row index, but after the sort `j` is a *rank*.
  The `target_id` recorded for each pair is therefore the j-th most similar row's
  rank, which the join (embedding.py:136-161) then resolves as row `j`. Every pair
  points at the wrong target node.
- `if i != j` (embedding.py:114) was meant to exclude self-similarity. The node's
  match with itself (similarity 1.0) is always rank 0, so the check excludes rank i
  instead. That is the self-match only when `i == 0`. For every other row the
  self-pair survives and some genuine neighbour at rank `i` is dropped.
- Using the text-query `retrieve` API at all means re-embedding the query text
  once per node. That is n extra embedding calls plus n cross-joins of size n, for
  O(n²) similarity work done in Python-driven chunks.

## What the fix looks like

None of this needs `retrieve()`. The embeddings are already in a column. L2-normalise
the matrix once, take one matrix product (`E_a @ E_b.T`) to get every cosine
similarity, and read pairs out of that with their true row indices. Self-pairs drop
out naturally once matching is restricted to *different* documents
(`2026-10-17-cross-document-pairing.md`). At this document size (tens to low hundreds
of nodes per file) the full similarity matrix is trivially small. Approximate nearest
neighbours are not needed.

The same rewrite removes all three `with_row_count` calls (embedding.py:96, 138,
152), which also clears the polars 2.0 crash.

## Current State

- `find_similar_nodes` loops over every row of the embedded DataFrame and calls `df.fastembed.retrieve` once per row with `k=n_rows` (src/mdbed/embedding.py:99-110)
- `compute_embeddings` retries once after re-registering the model when `df.fastembed.embed` raises any exception (src/mdbed/embedding.py:52-70)

## Stubbed

- A `breakpoint()` call sits inside the per-row loop of `find_similar_nodes`, halting every run in pdb unless `PYTHONBREAKPOINT=0` is set (src/mdbed/embedding.py:101)

## Missing

- polars 2.0 compatibility for row numbering has no code — `find_similar_nodes` calls `DataFrame.with_row_count`, which raises `AttributeRemovedError` under polars 2.0.0 before the per-row loop starts (src/mdbed/embedding.py:96)
- Similarity search over precomputed embeddings has no working code — `retrieve(query=None, raw_embedding=...)` raises `TypeError` because polars-fastembed 0.1.2, 0.1.3 and 0.1.17 all define `retrieve(query: str, ...)` with no `raw_embedding` parameter (src/mdbed/embedding.py:104-110)
- Row-index tracking through retrieval has no code — `retrieve` returns rows sorted by similarity descending, so the `enumerate` index `j` used as `target_id` is a rank, not a row id (src/mdbed/embedding.py:113-121)
- Self-pair exclusion compares row index `i` against rank `j`, so the self-match at rank 0 is excluded only for row 0 and kept for every other row (src/mdbed/embedding.py:114)

## Divergence

- The `embed` help text promises "find similar nodes" but `mdbed embed` raises `TypeError` in `find_similar_nodes` after embedding completes (src/mdbed/cli.py:43-69, embedding.py:104)
