"""Utility functions for mdbed."""

from __future__ import annotations

from pathlib import Path

import polars as pl

from pols import ls  # type: ignore


def get_files(
    paths: str | list[str],
    filter_expr: str | None = None,
    recursive: bool = False,
    merge_all: bool = True,
) -> pl.DataFrame:
    """Get files from paths using polars-ls.

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

    # Build ls arguments - note that paths need to be unpacked as *args
    path_objects = [Path(p) for p in paths]

    # Call ls with correct parameter mapping
    result = ls(
        *path_objects,  # Unpack paths as positional arguments
        R=recursive,  # Use R for recursive instead of 'recursive'
        with_filter=filter_expr,  # This parameter exists in ls
        merge_all=merge_all,
        as_path=True,
        keep="path,name,is_dir",
        to_dict=True,  # Always get dict result for consistent handling
    )

    # Handle the result based on merge_all setting
    if merge_all:
        # With merge_all, we should get a single DataFrame in the "" key
        if "" in result:
            return result[""]
        elif len(result) == 1:
            # If there's only one source, return that DataFrame
            return next(iter(result.values()))
        else:
            # Merge manually if needed
            dfs = []
            for source, df in result.items():
                if not df.is_empty():
                    dfs.append(df.with_columns(pl.lit(source).alias("source")))

            if not dfs:
                return pl.DataFrame({"path": [], "name": [], "is_dir": []})

            return pl.concat(dfs)
    else:
        # If not merging, manually process the dict result
        if not result:
            return pl.DataFrame({"path": [], "name": [], "is_dir": []})

        # Merge all DataFrames manually with source column
        dfs = []
        for source, df in result.items():
            if not df.is_empty():
                dfs.append(df.with_columns(pl.lit(source).alias("source")))

        if not dfs:
            return pl.DataFrame({"path": [], "name": [], "is_dir": []})

        return pl.concat(dfs)

    return pl.DataFrame({"path": [], "name": [], "is_dir": []})


def read_file_content(file_path: str | Path) -> str:
    """Read file content as text.

    Args:
        file_path: Path to file

    Returns:
        File content as string

    """
    with open(file_path, encoding="utf-8") as f:
        return f.read()
