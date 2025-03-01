"""Markdown parsing functionality using comrak."""

from __future__ import annotations

from html.parser import HTMLParser

import polars as pl

try:
    import comrak  # type: ignore
except ImportError:
    raise ImportError("comrak is required. Install with `pip install comrak`")


class HTMLNodeExtractor(HTMLParser):
    """HTML Parser to extract text from HTML nodes."""

    def __init__(self):
        super().__init__()
        self.nodes = []
        self.current_node = {"tag": None, "text": "", "attrs": {}, "children": []}
        self.node_stack = []
        self.path = []

    def handle_starttag(self, tag, attrs):
        """Handle start tag."""
        parent = self.current_node
        self.node_stack.append(parent)

        # Create new node
        self.current_node = {
            "tag": tag,
            "text": "",
            "attrs": dict(attrs),
            "children": [],
        }

        # Add to parent's children
        if parent["tag"] is not None:
            parent["children"].append(self.current_node)
        else:
            # Root node
            self.nodes.append(self.current_node)

        # Update path
        self.path.append(tag)

    def handle_endtag(self, tag):
        """Handle end tag."""
        # Restore parent as current node
        if self.node_stack:
            self.current_node = self.node_stack.pop()

        # Update path
        if self.path and self.path[-1] == tag:
            self.path.pop()

    def handle_data(self, data):
        """Handle text data."""
        if self.current_node["tag"] is not None:
            # Append text to current node
            self.current_node["text"] += data

            # Also create a text-only node for leaf text
            if data.strip():
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

        def extract_nodes(node, path=""):
            # Include the current node's path
            node_path = f"{path}/{node['tag']}" if path else node["tag"]

            if node["text"].strip():
                # Create a clean copy without circular references
                clean_node = {
                    "tag": node["tag"],
                    "text": node["text"].strip(),
                    "attrs": node["attrs"],
                    "path": node_path,
                }
                result.append(clean_node)

            for child in node["children"]:
                extract_nodes(child, node_path)

        for node in self.nodes:
            if node["tag"] == "text":
                # Text nodes already processed during data handling
                result.append(node)
            else:
                extract_nodes(node)

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


def markdown_to_dataframe(content: str, file_path: str | None = None) -> pl.DataFrame:
    """Convert markdown content to a DataFrame of nodes.

    Args:
        content: Markdown content
        file_path: Optional file path to include in DataFrame

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
        return pl.DataFrame(
            {
                "file": [] if file_path is None else [file_path],
                "tag": [""],
                "text": [""],
                "attrs": ["{}"],
                "path": [""],
            },
        )

    return pl.DataFrame(node_data)
