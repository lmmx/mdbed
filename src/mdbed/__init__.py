"""mdbed - Markdown embedding and similarity tool."""

from __future__ import annotations

from .cli import mdbed
from .embedding import compute_embeddings, find_similar_nodes, register_embedding_model
from .markdown import markdown_to_dataframe, parse_markdown
from .utils import get_files, read_file_content

__all__ = [
    "mdbed",
    "compute_embeddings",
    "find_similar_nodes",
    "register_embedding_model",
    "markdown_to_dataframe",
    "parse_markdown",
    "get_files",
    "read_file_content",
]
