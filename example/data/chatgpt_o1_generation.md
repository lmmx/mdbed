# Notes Towards Better Maps of Codebase Territories

## Introduction

Modern software development treats codebases as **living systems**: they grow, shrink, reorganize, and evolve. Documentation, by contrast, often lags behind, either ballooning into chaos or stagnating until it no longer reflects reality.

This tension presents a core challenge: **How do we maintain documentation that accurately “maps” a codebase while the “territory” keeps shifting beneath our feet?**

- **Refactoring** is a prime culprit. Rename or move a function, and references to that function’s old location in your docs now break. Even conceptually trivial changes—like reorganizing a package—can wreak havoc on your doc links.
  
- Enter the **map/territory** metaphor. The territory is the source code, and the map is the documentation (or, more broadly, the system of references that describes the code). The question becomes: **Can we build a map that gracefully follows and updates itself as the territory changes?**

This note outlines the major challenges of keeping code documentation in sync and proposes an approach—grounded in content-addressing principles and philosophical insights—that might help create more resilient, refactor-friendly docs.

---

## The Territory Problem

### Explosive Number of Ways to Partition Docs

In any sizable codebase, there are countless ways to present and organize documentation. You can sort by:

- **Functionality**: APIs, classes, and functions
- **Concepts**: architectural concerns or domain-level topics
- **Audience**: user guides vs. developer references

This *explosive number of possible partitions* can lead to a kind of decision paralysis—and once a partitioning scheme is chosen, reorganizing can become a major project in itself. 

1. **Opinionated Model of Documentation**  
   Adopting an **opinionated approach** forces some trade-offs early on but pays off in long-term maintainability. Decide firmly: Are your docs module-oriented? Do you group them by domain concept? Lock in a consistent scheme so that the docs remain structured and stable as the code evolves.

2. **Current Approaches & Their Limitations**  
   - **Scattered docstrings**: Great for immediate reference but easily go stale if you rely purely on in-line comments.  
   - **Standalone doc sites**: More cohesive but risk drifting out of date if not well integrated.  
   - **Wiki pages/Confluence**: Flexible but often untethered from the code itself, leading to duplication and fragmentation.

Without a unifying vision and tooling to keep references stable, the odds of a doc meltdown during every refactor increase dramatically.

### The Refactoring Challenge

Refactors typically break doc references in two ways:

1. **Rename or Move**  
   If a function or class moves (or simply changes its name), every link pointing to that original reference is now outdated.  
2. **Structural Reorganization**  
   Entire modules or packages can be rearranged—especially in large projects—making references ephemeral unless the doc system “understands” these moves.

To address these issues, we need a strategy that:

- **Decouples** references from fragile file paths or explicit symbol names, when possible.
- Allows “high-level anchors” that remain stable, even if you move code around beneath them.

---

## Content Addressing as a Solution

### Content Addressable Storage (CAS) Principles

**Content-addressable storage** is a concept made famous by Git, where the content (or its hash) is primary, not its location. Renames and moves are trivial if the underlying content is recognized as the same. Extending this principle to documentation means:

- **Stable references**: Link to an object or concept based on a unique content-based identifier, so that if code moves, the docs can still find it.
- **Beyond Syntactic to Semantic Addressing**: Ideally, we wouldn’t just rely on hash-based checks but track *semantic equivalences*. For example, rewriting a loop as a list comprehension (while preserving logic) shouldn’t break or change the doc references if the “meaning” of the code remains the same. This is aspirational but points the way toward more advanced doc systems that track the *intention* of code, not merely its text.

### High-Level Approach with Spanning Trees

One practical application is the **“high-level, spanning-tree”** approach:

1. **Module/Member Documentation**  
   Focus your docs primarily around modules or key classes/functions, rather than every single detail. These top-level nodes act as stable anchors when you reorganize.  
2. **Global Namespace Inventory**  
   Use tooling (e.g., mkdocstrings, Sphinx “inventory”) that generates a **global index** of objects. This inventory can automatically update references when code moves, or at least warn you when references become invalid.  
3. **Semantic or Content-Based References**  
   Over time, this approach could be extended to look at the meaning of code rather than just the name or path. This is still an area of research, but the principle stands: the better your doc system can identify “same or equivalent object,” the fewer broken links appear after refactor.

---

## Philosophical Foundations

### Bergson’s Memory Theory as a Parallel

French philosopher **Henri Bergson** introduced a concept of “pure memory” (unextended, virtual) vs. “memory-images” (what we selectively bring into conscious perception). We might think of a codebase as a swirling potential of logic and meaning—like Bergson’s “pure memory.” By the time it’s rendered in doc form or user-facing interfaces, it’s already a *filtered* or *crystallized* representation—like a “memory-image.”

- **Pre-image setting and stimuli**: The code is a complex territory, potentially restructured at any moment.  
- **Application to code documentation**: If we treat docs as a direct reflection, we’re capturing a partial view from a pool of deeper intent. This aligns with the idea of content addressing, where the doc can always *point back* to a deeper well of meaning.

### Documentation as Snapshot

In testing, a **snapshot** is a literal “photograph” of output at a particular time, automatically checked against current behavior. Similarly, **documentation** can be a snapshot of the code’s structure and semantics. When the code changes, the doc-snapshot can either update or warn us that it’s out of sync. This perspective encourages us to:

- **Adopt a versioned approach**: Each doc iteration can be “diffed” against the current code structure.  
- **Stay aware of drift**: If the doc snapshot no longer matches the code, we know the map is out of date.

Embracing these ideas positions docs as more *dynamic*, actively tracking refactors like a cybernetic system that senses changes and steers toward alignment.

---

## Implementation Framework

Below is a simplified model for how we might implement a documentation framework that ties back to the map/territory metaphor.

1. **Territory**: The Source Tree  
   - This is the actual code repository—modules, sub-packages, classes, methods, etc.  
   - Tools: Git (for version control), standard Python packaging or your language ecosystem.

2. **Map**: The mkdocstrings Configuration  
   - The “map” is how we conceptualize and parse the territory. mkdocstrings auto-discovers modules and classes, pulls docstrings, and builds references.  
   - You can fine-tune it with “options flags” (e.g., whether to show private members) or tailor how docstrings are rendered.

3. **UI**: Navigation Layer  
   - Typically set in `mkdocs.yml` (or the equivalent config in other doc generators).  
   - This is what users see: the top-level “nav,” subsections, etc. It’s the final, user-facing shape of your doc site.  
   - The UI is still part of the “map,” but it’s more about how you *present* it than how you *collect* it.

In essence: **territory** (raw source) → **map** (structured doc config) → **UI** (website or doc output). This separation gives clarity on where each piece lives and how it can be updated or restructured.

---

## Practical Steps

Here are three immediate, tangible steps you can take to move toward a more robust and refactor-ready documentation system:

1. **Fulfill All Docstring Requirements**  
   - At a minimum, ensure every public module, class, and function has a docstring.  
   - Adhere to a consistent style (e.g., Google-style, NumPy-style) for clarity and tooling compatibility.

2. **Fill Out a Standard README**  
   - Provide a concise overview of your project: purpose, core features, quickstart instructions.  
   - This serves as a “front door” for new readers and sets the context for the deeper API docs.

3. **Autogenerate Docs**  
   - Use tools like **MkDocs + mkdocstrings** or Sphinx to automatically ingest docstrings.  
   - Configure them to produce a living site that updates as your code changes.  
   - This ensures references remain stable (or at least you’ll get warnings when they break).

As you refine your process, these steps can be further augmented:

- Adding **automated checks** (e.g., in CI) that detect broken doc references.  
- Versioning your docs in parallel with your code releases.  
- Potentially exploring content-hashing or more advanced “semantic-diff” tools to see if code changes are purely refactors vs. changes in functionality.

---

## Conclusion

Maintaining documentation in the face of constant refactoring can be daunting. By borrowing ideas from **content-addressable storage**, adopting a **high-level anchor system** (modules/classes as stable references), and acknowledging a philosophical stance (Bergson’s idea of “pure memory” vs. “memory-image”), we can start building **resilient “maps”** that remain aligned with an evolving “territory.”

Ultimately, the goal is a doc system that **knows** your code structure, automatically **tracks** changes, and can gracefully **pivot** without collapsing under every rename or move. Moving beyond purely syntactic references into the realm of semantic awareness is challenging, but it points us toward a future where docs truly keep pace with code—ensuring that the “map” is a continuous and faithful guide to the “territory.”

---

**Working Title:** *Notes Towards Better Maps of Codebase Territories*
