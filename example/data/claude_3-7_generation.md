# Notes towards better maps of codebase territories

## Introduction
- The challenge: Documentation as mapping a constantly changing territory
- The problem of code refactoring breaking documentation
- Introducing the map/territory metaphor for documentation systems

## The Territory Problem
- **Explosive number of ways to partition docs**
  - Why this necessitates an **opinionated** model of documentation
  - Current approaches and their limitations

- **The refactoring challenge**
  - How code changes break documentation links
  - The need for stable references across code reorganization

## Content Addressing as a Solution
- **Content Addressable Storage (CAS) principles**
  - Lessons from git's content-addressing model
  - Moving beyond syntactic to semantic addressing

- **High-level approach with spanning trees**
  - Module/member documentation that survives refactoring
  - Creating stable references through semantic content addressing
  - Global namespace of objects that persists through reorganization

## Philosophical Foundations
- **Bergson's memory theory as a parallel**
  - Pure memory vs. memory-images
  - Pre-image setting and stimuli
  - Application to code documentation: capturing intent vs. implementation

- **Documentation as snapshot**
  - Docs as snapshots of state (form) similar to how tests capture behavior
  - The cybernetic approach to steering documentation through changes

## Implementation Framework
1. **Territory**: Source tree (repository-grounding)
2. **Map**: mkdocstrings modules/classes - members (+options flags)
3. **UI**: Navigation layer

## Practical Steps
1. Fulfill all docstring requirements
2. Fill out standard readme
3. Autogenerate docs

## Conclusion
- Documentation that follows code through refactoring
- Detecting semantically equivalent code despite syntactic differences
- Creating resilient maps of evolving code territories
