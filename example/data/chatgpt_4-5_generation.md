# Notes Towards Better Maps of Codebase Territories

## Introduction

Effective documentation is akin to creating maps of a constantly shifting territory. As codebases evolve, the documentation frequently falls out of sync, especially during extensive refactoring. This disconnect motivates employing the metaphor of map versus territory, where the documentation (map) must remain relevant despite changes in the underlying codebase (territory).

## The Territory Problem

### Explosive Number of Ways to Partition Documentation

The variety and complexity in documentation partitioning highlight the necessity for an **opinionated model**. Current methods are numerous yet often insufficiently structured, creating confusion and redundancy. This proliferation of approaches underscores the need for clear, consistent documentation frameworks that explicitly define their organizational assumptions.

### The Refactoring Challenge

Refactoring regularly disrupts documentation, leading to broken links, outdated references, and confusion among developers. Stable documentation references must endure despite code restructuring, motivating documentation models resilient to structural changes.

## Content Addressing as a Solution

### Principles from Content Addressable Storage (CAS)

Content-addressable storage principles, prominently exemplified by Git, inspire an approach to documentation where content is referenced by stable semantic identifiers rather than transient textual or positional indicators. By shifting from syntactic to semantic addressing, documentation systems become capable of tracking code intent rather than mere form.

### High-Level Approach with Spanning Trees

A robust documentation solution leverages a high-level, semantic-centric approach using module and member relationships as stable reference points. By employing spanning trees that map out these semantic relationships, documentation can remain intact through refactors. Such systems propose a global namespace of documented objects that maintain relevance through structural reorganizations.

## Philosophical Foundations

### Bergson’s Memory Theory as a Parallel

Henri Bergson’s theory of memory distinguishes between pure memory (the complete, unstructured past or pre-image) and memory-images (selectively recalled representations). Similarly, documentation should aim at capturing developer intent (pure memory) rather than mere implementation details (memory-images), ensuring that core meaning survives even extensive code transformations.

### Documentation as Snapshot

Like snapshot testing in software development, documentation acts as a snapshot of a codebase's current state or form. Adopting a cybernetic mindset, where the documentation actively "steers" the evolving structure, helps manage and maintain coherence amidst continuous code evolution.

## Implementation Framework

To operationalize this philosophy, three clear layers should be defined:

- **Territory**: The repository-grounded truth—the source tree.
- **Map**: A structured representation using mkdocstrings, documenting modules, classes, and their members, enhanced by explicit options and flags.
- **UI**: An intuitive navigation structure that clearly exposes the semantic map to the user, implemented through tools like MkDocs.

## Practical Steps

Implementing this approach involves specific, manageable actions:

1. Ensure all docstring requirements are fully satisfied.
2. Complete and standardize README files as accessible entry points.
3. Automate documentation generation using robust tools such as `mkdocstrings`.

## Conclusion

By focusing on stable semantic relationships and clear structuring principles, documentation can effectively navigate refactoring and structural changes in codebases. Ultimately, this approach facilitates recognizing semantic equivalences, paving the way toward documentation resilience and accuracy in capturing evolving code territories.

