"""Command-line interface for mdbed."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple

import click
import polars as pl

from .embedding import DEFAULT_MODEL, compute_embeddings, find_similar_nodes, register_embedding_model
from .markdown import markdown_to_dataframe
from .utils import get_files, read_file_content


class DefaultCommandGroup(click.Group):
    """A custom Group class to provide a default command."""
    
    def parse_args(self, ctx, args):
        """Intervene to set embed as default command unless user gave no arguments."""
        if not args or ctx.resilient_parsing:
            return super().parse_args(ctx, args)

        # The first token after 'mdbed'
        cmd_name = args[0]

        # Is this first token a recognized subcommand name or a global option?
        recognized_subcommands = list(self.commands.keys())
        if cmd_name not in recognized_subcommands and not cmd_name.startswith("-"):
            # Not a known subcommand, so treat this token as if it were for 'embed'.
            args.insert(0, "embed")

        return super().parse_args(ctx, args)


@click.group(cls=DefaultCommandGroup)
def mdbed():
    """mdbed - Markdown embedding and similarity tool."""


@mdbed.command(
    help="""
    Embed markdown files and find similar nodes.
    
    By default, this processes Markdown files and computes embeddings.
    
      The --recursive/-r flag searches directories recursively.
      
      The --threshold/-t flag sets the similarity threshold (0.0-1.0).
      
      The --model/-m flag sets the embedding model to use.
      
      The --gpu/-g flag enables GPU acceleration.
      
    \b
    Examples
    --------
    
    - Process markdown files in current directory:
        mdbed embed .
        
    - Process specific files:
        mdbed embed file1.md file2.md
        
    - Process all markdown files recursively with a lower threshold:
        mdbed embed . -r -t 0.6
    """,
)
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option(
    "-r", "--recursive", is_flag=True, help="Search directories recursively."
)
@click.option(
    "-t", 
    "--threshold", 
    type=float, 
    default=0.7, 
    help="Similarity threshold (0.0-1.0)."
)
@click.option(
    "-m", 
    "--model", 
    type=str, 
    default=DEFAULT_MODEL, 
    help="Embedding model to use."
)
@click.option(
    "-g", "--gpu", is_flag=True, help="Use GPU acceleration."
)
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    help="Output file for results (CSV format).",
)
@click.option(
    "-f",
    "--filter",
    type=str,
    help="Filter expression for files (e.g. '{name}.str.ends_with(\".md\")')",
)
def embed(
    paths: Tuple[str, ...],
    recursive: bool,
    threshold: float,
    model: str,
    gpu: bool,
    output: Optional[str],
    filter: Optional[str],
) -> None:
    """Embed markdown files and find similar nodes."""
    # Validate paths
    if not paths:
        paths = ["."]
    
    # Default filter to only markdown files if not provided
    if filter is None:
        filter = '{name}.str.ends_with(".md")'
    
    # Register model
    click.echo(f"Registering model: {model}", err=True)
    register_embedding_model(model, use_gpu=gpu)
    
    # Get files
    click.echo(f"Finding files in {paths}", err=True)
    files_df = get_files(
        paths=list(paths),
        filter_expr=filter,
        recursive=recursive,
        merge_all=True,
    )
    
    # Filter out directories
    files_df = files_df.filter(~pl.col("is_dir"))
    
    if files_df.is_empty():
        click.echo("No files found.", err=True)
        return
    
    click.echo(f"Found {files_df.height} files", err=True)
    
    # Process each file
    all_nodes = []
    for file_path in files_df.select("path").to_series():
        file_str = str(file_path)
        try:
            click.echo(f"Processing {file_str}", err=True)
            content = read_file_content(file_path)
            nodes_df = markdown_to_dataframe(content, file_str)
            all_nodes.append(nodes_df)
        except Exception as e:
            click.echo(f"Error processing {file_str}: {e}", err=True)
    
    if not all_nodes:
        click.echo("No nodes extracted from files.", err=True)
        return
    
    # Combine all nodes
    nodes_df = pl.concat(all_nodes)
    click.echo(f"Extracted {nodes_df.height} nodes from {len(all_nodes)} files", err=True)
    
    # Compute embeddings
    click.echo("Computing embeddings...", err=True)
    nodes_with_emb = compute_embeddings(
        nodes_df,
        text_column="text",
        model_name=model,
        output_column="embedding",
    )
    click.echo("Embeddings computed", err=True)
    
    # Find similar nodes
    click.echo(f"Finding similar nodes (threshold: {threshold})...", err=True)
    similar_nodes = find_similar_nodes(
        nodes_with_emb,
        embedding_column="embedding",
        similarity_threshold=threshold,
        model_name=model,
    )
    
    # Display results
    if similar_nodes.is_empty():
        click.echo("No similar nodes found.", err=True)
    else:
        click.echo(f"Found {similar_nodes.height} similar node pairs.", err=True)
        
        # Output results
        if output:
            similar_nodes.write_csv(output)
            click.echo(f"Results written to {output}", err=True)
        else:
            # Print to console in a readable format
            display_df = similar_nodes.select([
                "source_file", 
                "source_text", 
                "target_file", 
                "target_text", 
                "similarity"
            ])
            click.echo(display_df)


@mdbed.command(
    help="""
    List input files without processing.
    
    This command lists input files matching the criteria without processing them.
    
    \b
    Examples
    --------
    
    - List markdown files in current directory:
        mdbed list .
        
    - List specific files:
        mdbed list file1.md file2.md
    """,
)
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option(
    "-r", "--recursive", is_flag=True, help="Search directories recursively."
)
@click.option(
    "-f",
    "--filter",
    type=str,
    help="Filter expression for files (e.g. '{name}.str.ends_with(\".md\")')",
)
def list_files(
    paths: Tuple[str, ...],
    recursive: bool,
    filter: Optional[str],
) -> None:
    """List input files without processing."""
    # Validate paths
    if not paths:
        paths = ["."]
    
    # Default filter to only markdown files if not provided
    if filter is None:
        filter = '{name}.str.ends_with(".md")'
    
    # Get files
    files_df = get_files(
        paths=list(paths),
        filter_expr=filter,
        recursive=recursive,
        merge_all=True,
    )
    
    # Filter out directories
    files_df = files_df.filter(~pl.col("is_dir"))
    
    if files_df.is_empty():
        click.echo("No files found.")
        return
    
    # Display results
    click.echo(f"Found {files_df.height} files:")
    click.echo(files_df.select(["path", "name"]))