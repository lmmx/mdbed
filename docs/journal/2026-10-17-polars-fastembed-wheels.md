# 2026-10-17: polars-fastembed Wheels and polars 2.0

mdbed depends on `polars-fastembed>=0.1.2` (pyproject.toml:28), a Rust/pyo3 polars
plugin from the same author, and on `polars` through the `polars` / `polars-lts-cpu`
extras with only a lower bound (`>=1.21.0`). Both open-ended bounds now break a fresh
install, in different ways.

## No x86_64 Linux wheel since polars-fastembed 0.1.4

During the audit a fresh `uv pip install -e '.[polars]'` on x86_64 Linux (Python 3.12)
failed: uv resolved polars-fastembed 0.1.17, found no compatible wheel, fell back to
building the sdist, and the Rust build failed.

The PyPI file listing shows why. 0.1.1 through 0.1.3 ship a
`cp38-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64` wheel. Every release from
0.1.4 (2025-12-13) onwards ships none:

| polars-fastembed | Released | Linux wheels (cp38-abi3 unless noted) |
|---|---|---|
| 0.1.2, 0.1.3 | 2025-02-28, 2025-03-04 | x86_64 (manylinux2014), aarch64, i686, armv7l, s390x, ppc64le |
| 0.1.4 – 0.1.13 | 2025-12-13 → 2025-12-22 | aarch64, i686, plus PyPy 3.9/3.10 aarch64 |
| 0.1.15 – 0.1.17 | 2025-12-26 | i686 only |

Between 0.1.3 and 0.1.4 the x86_64, armv7l, s390x and ppc64le targets all dropped out
of the Linux build matrix, while i686 and aarch64 stayed. From 0.1.15 aarch64 went too.
(A first pass at this table, which only looked at six filenames per release, suggested
an `i686`-for-`x86_64` typo. The full listing shows i686 was always built alongside
x86_64, so the more likely story is that the x86_64 jobs started failing or were
removed from the release workflow in December 2025. That has not been checked against
the polars-fastembed repo.) Either way, ordinary x86_64 Linux machines, the most
common deployment target, cannot install any polars-fastembed release made since
December 2025 without a Rust toolchain that can build the sdist. That is a
polars-fastembed packaging problem worth fixing upstream for its own sake,
independent of mdbed.

## polars 2.0 removed `with_row_count`

The audit environment was first built with `polars-fastembed==0.1.3` and `polars<1.25`
(polars 1.24.0). A later check with polars 2.0.0 showed that polars-fastembed 0.1.3
still embeds correctly there. But `DataFrame.with_row_count`, which
`find_similar_nodes` calls at embedding.py:96, 138 and 152, was **removed** in polars
2.0:

```
AttributeRemovedError: `with_row_count` was removed in version 2.0; use `with_row_index` instead.
```

On polars 1.x (checked on 1.44.2) the same call only emits a `DeprecationWarning`.
So on any polars ≥ 2.0, `mdbed embed` fails at embedding.py:96, one line before it
would hit the leftover `breakpoint()` and the `raw_embedding` `TypeError` (see
`2026-10-17-similarity-search.md`). A working audit environment needs both
`polars-fastembed==0.1.3` and `polars<2`.

The `retrieve()` API mdbed calls into is unchanged across polars-fastembed 0.1.2,
0.1.3 and 0.1.17, so the polars-fastembed pin does not change mdbed's behaviour. It
only makes it installable.

## Current State

- pyproject.toml declares `polars-fastembed>=0.1.2` with no upper bound (pyproject.toml:28)
- pyproject.toml declares `polars>=1.21.0` and `polars-lts-cpu>=1.21.0` in the `polars` and `polars-lts-cpu` extras with no upper bound (pyproject.toml)
- polars-fastembed 0.1.3 installs from a `cp38-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64` wheel on x86_64 Linux and embeds `example/data/claude_3-7_generation.md` into a 384-dimensional `Array(Float32)` column under both polars 1.24.0 and polars 2.0.0
- polars-fastembed `retrieve()` has the same signature `retrieve(query: str, model_name=None, embedding_column="embedding", k=None, threshold=None, similarity_metric="cosine", add_similarity_column=True)` in 0.1.2, 0.1.3 and 0.1.17
- `DataFrame.with_row_count` emits `DeprecationWarning` under polars 1.44.2 and raises `AttributeRemovedError` under polars 2.0.0

## Missing

- x86_64 Linux wheels for polars-fastembed have no published artifact from 0.1.4 onwards — PyPI lists `manylinux_2_28_i686` and (0.1.4 through 0.1.13) `manylinux_2_28_aarch64` wheels only, so `pip install mdbed` on x86_64 Linux resolves 0.1.17 and attempts an sdist build
- A dependency pin or upper bound protecting mdbed from the polars-fastembed x86_64 wheel gap has no entry in pyproject.toml (pyproject.toml:28)
- An upper bound below polars 2.0 has no entry in pyproject.toml — polars 2.0.0 resolves by default and `find_similar_nodes` raises `AttributeRemovedError` at the first `with_row_count` call (src/mdbed/embedding.py:96)

## Divergence

- The README installation section shows `pip install lit-embs[polars]`, which installs neither mdbed nor (on x86_64 Linux without a Rust toolchain) polars-fastembed (README.md)
