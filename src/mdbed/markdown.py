"""Markdown parsing functionality using comrak."""

from __future__ import annotations

from html.parser import HTMLParser

import comrak
import polars as pl


class HTMLNodeExtractor(HTMLParser):
    """HTML Parser to extract text from HTML nodes."""

    LEAF_TAGS = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote", "code"}

    def __init__(self):
        super().__init__()
        self.nodes = []
        self.current_node = {"tag": None, "text": "", "attrs": {}, "children": []}
        self.node_stack = []
        self.path = []
        self.leaf_depth = 0  # Track depth of nesting inside leaf tags

    def handle_starttag(self, tag, attrs):
        """Handle start tag."""
        if tag in self.LEAF_TAGS:
            self.leaf_depth += 1

        parent = self.current_node
        self.node_stack.append(parent)

        # Create new node
        self.current_node = {
            "tag": tag,
            "text": "",
            "attrs": dict(attrs),
            "children": [],
        }

        # Add to nodes list if it's a root or leaf tag
        # Only add to parent's children if we're not already inside a leaf tag
        # Add to parent's children
        if parent["tag"] is None:
            # Root node
            self.nodes.append(self.current_node)
        elif (
            self.leaf_depth <= 1
        ):  # Current tag might be a leaf tag, but not nested inside another
            parent["children"].append(self.current_node)

            # If this is a leaf tag, also add it to the main nodes list
            if tag in self.LEAF_TAGS:
                self.nodes.append(self.current_node)

        # Always update path for tracking
        self.path.append(tag)

    def handle_endtag(self, tag):
        """Handle end tag."""
        # Check if we're exiting a leaf tag
        if tag in self.LEAF_TAGS and self.leaf_depth > 0:
            self.leaf_depth -= 1

        # Restore parent as current node
        if self.node_stack:
            self.current_node = self.node_stack.pop()

        # Update path
        if self.path and self.path[-1] == tag:
            self.path.pop()

    def handle_data(self, data):
        """Handle text data."""
        # Restore parent as current node
        if self.current_node["tag"] is not None:
            # Append text to current node
            self.current_node["text"] += data

            # Create separate text nodes only outside of leaf tags
            if data.strip() and self.leaf_depth == 0:
                text_node = {
                    "tag": "text",
                    "text": data.strip(),
                    "attrs": {},
                    "children": [],
                    "path": "/".join(self.path),
                }
                self.nodes.append(text_node)

    def get_nodes_with_text(self) -> list[dict]:
        """Get all nodes that contain text."""
        result = []

        for node in self.nodes:
            if node["text"].strip():
                # Create a clean copy without circular references
                node_path = (
                    "/".join(self.path) if node["tag"] == "text" else node["text"]
                )
                clean_node = {
                    "tag": node["tag"],
                    "text": node["text"].strip(),
                    "attrs": node["attrs"],
                    "path": node.get("path", node_path),
                }
                result.append(clean_node)

        return result


def parse_markdown(content: str) -> list[dict]:
    """Parse markdown content into nodes with text.

    Args:
        content: Markdown content as string

    Returns:
        List of nodes with text

    """
    # Parse markdown to HTML
    html_content = comrak.render_markdown(content)

    # Extract nodes with text from HTML
    parser = HTMLNodeExtractor()
    parser.feed(html_content)

    return parser.get_nodes_with_text()


def markdown_to_dataframe(
    content: str, file_path: str | None = None, deduplicate: bool = True
) -> pl.DataFrame:
    """Convert markdown content to a DataFrame of nodes.

    Args:
        content: Markdown content
        file_path: Optional file path to include in DataFrame
        deduplicate: Whether to duplicate (default: True)

    Returns:
        DataFrame with node information

    """
    nodes = parse_markdown(content)

    # Create DataFrame
    node_data = [
        {
            "file": file_path,
            "tag": node["tag"],
            "text": node["text"],
            "attrs": str(node.get("attrs", {})),  # Convert dict to string for DataFrame
            "path": node.get("path", ""),  # Include node path
        }
        for node in nodes
    ]

    if not node_data:
        # Return empty DataFrame with correct schema
        df = pl.DataFrame(
            {
                "file": [] if file_path is None else [file_path],
                "tag": [""],
                "text": [""],
                "attrs": ["{}"],
                "path": [""],
            },
        )
    else:
        df = pl.DataFrame(node_data)
    if deduplicate:
        df = df.unique("text", maintain_order=True)
    return df
