# 2026-10-17: Markdown Node Extraction

Everything downstream depends on what counts as a "node", so the parser deserves the
closest look. `parse_markdown` renders markdown to HTML with comrak
(markdown.py:122) and walks the HTML with an `HTMLParser` subclass,
`HTMLNodeExtractor` (markdown.py:11-108). That class treats a fixed set of tags as
leaves, `{"p", "h1".."h6", "li", "blockquote", "code"}` (markdown.py:14). The
"stop at leaf nodes to avoid too many nodes" commit added a `leaf_depth` counter so
that nested elements inside a leaf would not be emitted separately.

The intent was reasonable: one node per paragraph, heading or list item, and not one
node per `<strong>` fragment. The implementation loses text.

## What gets lost

Text is appended to whichever node is *current* when `handle_data` fires
(markdown.py:77). When a `<strong>`, `<em>` or `<code>` opens inside a paragraph or
list item, `handle_starttag` makes a new child node current. The inline text lands in
that child, and with `leaf_depth > 1` the child is never attached to the parent or to
`self.nodes`. The parent only ever receives the text *around* the inline element.
Minimal reproductions with the current code:

| Input markdown | Extracted `(tag, text)` |
|---|---|
| ``Para with *em* and `code` end.`` | `('p', 'Para with  and  end.')` |
| `- **Bold** tail` / `  - nested child` / `- plain` | `('li', 'tail')`, `('li', 'plain')` |
| `See [the link text](http://x) here.` | `('p', 'See  here.')` |

So:

- Inline-formatted text (bold, italic, inline code, and links via `<a>`) is deleted
  from the node text, leaving double spaces where it was. In
  `example/data/claude_3-7_generation.md`, `1. **Territory**: Source tree
  (repository-grounding)` comes out as `": Source tree (repository-grounding)"`.
  The bolded words are often the most semantically loaded words in the line.
- Nested list items vanish entirely. The inner `<li>` opens at `leaf_depth == 2`,
  so the `leaf_depth <= 1` branch (markdown.py:46-54) never adds it to `self.nodes`.
  Because a nested list is exactly how outlines express hierarchy, this hits the
  example data hard.

Per-file counts on the example data, with bullets and headings counted from the raw
markdown:

| File | Lines | Bullets | Headings | Nodes extracted |
|---|---|---|---|---|
| `chatgpt_4-5_generation.md` | 55 | 6 | 14 | 30 |
| `chatgpt_o1_generation.md` | 151 | 46 | 14 | 52 |
| `claude_3-7_generation.md` | 50 | 32 | 8 | 20 |
| `source_prompt.md` | 63 | 3 | 0 | 21 |

The Claude rewrite has 40 bullets and headings and yields 20 nodes. Every sub-bullet
under the bolded parent bullets in "The Territory Problem" section is gone. (An
earlier verbal summary said "~40 bullets". The precise figure is 32 bullets plus 8
headings.)

## The `path` column is not a path

The `path` column was meant to say where a node sits in the document tree, which is
the structural signal needed to tell a *moved* node from an *edited* one. For non-text
nodes, `get_nodes_with_text` sets `node_path = node["text"]` (markdown.py:97-99), so
`path` just repeats the node's text. For bare text nodes (text outside any leaf tag) a
real `"/".join(self.path)` is recorded (markdown.py:79-86). Those are rare in
comrak's output, which wraps nearly everything in `<p>`/`<li>`. In practice the
DataFrame carries no structural information at all: no parent heading, no list depth,
no ordinal position.

## Empty-document branch

`markdown_to_dataframe` has a fallback for a document with no text nodes. With
`file_path=None` it builds `"file": []` alongside length-1 lists for the other columns
(markdown.py:157-166), which raises
`ShapeError: height of column 'tag' (1) does not match height of column 'file' (0)`.
With a file path the fallback returns one row of empty strings, which then gets
embedded as a node.

## Design question this leaves open: what should be embedded?

Even with the text-loss bugs fixed, embedding a bare list item throws away the heading
it sits under. "Current approaches and their limitations" means something different
under "The Territory Problem" than under "Content Addressing". Two options to weigh:

- Embed each node with its heading path prepended (`Territory Problem > Explosive
  number of ways… > Current approaches…`). Context-aware matching, at the cost of
  making a node look "moved" whenever its parent heading is reworded.
- Embed node text alone, carry the heading path as a separate structural feature, and
  let the matcher combine content similarity with structural similarity. This is
  closer to how GumTree separates label from position (see lit-embs
  `docs/journal/2026-10-17-prior-art.md`).

Short nodes are the other half of the problem. A heading like "Introduction" carries
almost no meaning on its own when embedded, and will clear any fixed threshold against
many unrelated short nodes. Headings may be better matched by the content of their
section (the GumTree bottom-up idea: two containers match if their descendants
match) than by their own text.

## Current State

- `parse_markdown` renders markdown to HTML with `comrak.render_markdown` and feeds the HTML to `HTMLNodeExtractor` (src/mdbed/markdown.py:111-125)
- `HTMLNodeExtractor` treats `p`, `h1`–`h6`, `li`, `blockquote`, `code` as leaf tags and tracks nesting inside leaf tags with a `leaf_depth` counter (src/mdbed/markdown.py:14, markdown.py:24-28, markdown.py:59-62)
- `HTMLNodeExtractor.handle_data` appends text only to the node that is current at the moment the data arrives (src/mdbed/markdown.py:73-87)
- `markdown_to_dataframe` returns one row per extracted node with columns `file`, `tag`, `text`, `attrs` (stringified dict), `path` (src/mdbed/markdown.py:128-166)
- Node extraction on `example/data/` yields 30, 52, 20 and 21 nodes for `chatgpt_4-5_generation.md`, `chatgpt_o1_generation.md`, `claude_3-7_generation.md` and `source_prompt.md` respectively

## Missing

- Inline-element text capture has no code — text inside `<strong>`, `<em>`, `<code>` and `<a>` within a leaf tag goes to a child node that is never emitted, so `Para with *em* and \`code\` end.` extracts as `'Para with  and  end.'` (src/mdbed/markdown.py:40-54, markdown.py:77)
- Nested list item extraction has no code — an `<li>` opened at `leaf_depth == 2` fails the `leaf_depth <= 1` check and never reaches `self.nodes`, so `claude_3-7_generation.md` with 32 bullets and 8 headings yields 20 nodes (src/mdbed/markdown.py:46-54)
- Structural path tracking for leaf nodes has no code — `get_nodes_with_text` assigns `node_path = node["text"]`, so the `path` column repeats the node text for every non-`text` node (src/mdbed/markdown.py:97-104)
- Heading context per node (parent heading chain, list depth, ordinal position) has no code

## Divergence

- The empty-document fallback raises `ShapeError` when `file_path` is `None` because `"file"` gets a length-0 list while the other columns get length-1 lists (src/mdbed/markdown.py:157-166)
- The `path` column name implies a document-tree location, but the column holds the node text for all leaf-tag nodes (src/mdbed/markdown.py:97-104, markdown.py:151)
