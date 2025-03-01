"""Utility functions for mdbed."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional, Union

import polars as pl

try:
    from polars_ls import ls  # type: ignore
except ImportError:
    raise ImportError(
        "polars-ls is required. Install with `pip install polars-ls[polars]`"
    )


def get_files(
    paths: Union[str, List[str]], 
    filter_expr: Optional[str] = None, 
    recursive: bool = False,
    merge_all: bool = True,
) -> pl.DataFrame:
    """
    Get files from paths using polars-ls.
    
    Args:
        paths: Path or list of paths to scan
        filter_expr: Optional filter expression
        recursive: Whether to scan recursively
        merge_all: Whether to merge all results into a single DataFrame
        
    Returns:
        DataFrame containing file information
    """
    # Convert single path to list
    if isinstance(paths, str):
        paths = [paths]
    
    # Build arguments for ls
    ls_args = {
        "paths": paths,
        "with_filter": filter_expr,
        "recursive": recursive,
        "merge_all": merge_all,
        "as_path": True,
        "keep": "path,name,is_dir",
    }
    
    # Get files
    result = ls(**ls_args)
    
    # If merge_all is True, result is a DataFrame
    # Otherwise, it's a dict of DataFrames
    if not merge_all and isinstance(result, dict):
        if not result:
            return pl.DataFrame({"path": [], "name": [], "is_dir": []})
        
        # Merge all DataFrames manually
        dfs = []
        for source, df in result.items():
            if not df.is_empty():
                dfs.append(df.with_columns(pl.lit(source).alias("source")))
        
        if not dfs:
            return pl.DataFrame({"path": [], "name": [], "is_dir": []})
        
        return pl.concat(dfs)
    
    return result


def read_file_content(file_path: Union[str, Path]) -> str:
    """
    Read file content as text.
    
    Args:
        file_path: Path to file
        
    Returns:
        File content as string
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()