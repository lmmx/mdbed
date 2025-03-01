"""Embedding functionality using polars-fastembed."""

from __future__ import annotations

from typing import Dict, List, Optional, Union

import polars as pl

try:
    from polars_fastembed import register_model  # type: ignore
except ImportError:
    raise ImportError(
        "polars-fastembed is required. Install with `pip install polars-fastembed[polars]`"
    )


DEFAULT_MODEL = "Xenova/bge-small-en-v1.5"


def register_embedding_model(model_name: str = DEFAULT_MODEL, use_gpu: bool = False) -> None:
    """
    Register embedding model.
    
    Args:
        model_name: Name of the model to use
        use_gpu: Whether to use GPU for embedding
    """
    providers = ["CUDAExecutionProvider"] if use_gpu else ["CPUExecutionProvider"]
    register_model(model_name, providers=providers)


def compute_embeddings(
    df: pl.DataFrame, 
    text_column: str = "text", 
    model_name: str = DEFAULT_MODEL,
    output_column: str = "embedding",
) -> pl.DataFrame:
    """
    Compute embeddings for text in a DataFrame.
    
    Args:
        df: DataFrame containing text to embed
        text_column: Name of column containing text
        model_name: Name of the model to use
        output_column: Name of column to store embeddings
        
    Returns:
        DataFrame with embeddings
    """
    # Check if model is registered
    try:
        # Compute embeddings
        df_emb = df.fastembed.embed(
            columns=text_column,
            model_name=model_name,
            output_column=output_column,
        )
        return df_emb
    except Exception as e:
        # If model is not registered, register it and try again
        register_embedding_model(model_name)
        
        # Try again
        df_emb = df.fastembed.embed(
            columns=text_column,
            model_name=model_name,
            output_column=output_column,
        )
        return df_emb


def find_similar_nodes(
    df: pl.DataFrame,
    embedding_column: str = "embedding",
    similarity_threshold: float = 0.7,
    model_name: str = DEFAULT_MODEL,
) -> pl.DataFrame:
    """
    Find similar nodes in a DataFrame.
    
    Args:
        df: DataFrame containing embeddings
        embedding_column: Name of column containing embeddings
        similarity_threshold: Threshold for similarity
        model_name: Name of the model to use
        
    Returns:
        DataFrame with similarity information
    """
    # First get all pairs by comparing each embedding with all others
    n_rows = df.height
    all_pairs = []
    
    # Get the node IDs for reference
    node_ids = df.with_row_count("id").select("id").to_series().to_list()
    
    # For each node, find similar nodes
    for i in range(n_rows):
        query_embedding = df.select(embedding_column).row(i)[0]
        
        # Convert single embedding to DataFrame for retrieval
        result = df.fastembed.retrieve(
            query=None,  # Use raw embedding
            raw_embedding=query_embedding,
            model_name=model_name,
            embedding_column=embedding_column,
            k=n_rows,  # Get all nodes
        )
        
        # Filter by similarity threshold and exclude self-similarity
        for j, sim in enumerate(result.select("similarity").to_series()):
            if i != j and sim >= similarity_threshold:
                all_pairs.append({
                    "source_id": node_ids[i],
                    "target_id": node_ids[j],
                    "similarity": sim,
                })
    
    # Create DataFrame from pairs
    if not all_pairs:
        return pl.DataFrame({
            "source_id": [],
            "target_id": [],
            "similarity": [],
        })
    
    pairs_df = pl.DataFrame(all_pairs)
    
    # Join with original DataFrame to get node information
    result = (
        pairs_df
        .join(
            df.with_row_count("id").select(["id", "file", "tag", "text", "path"]),
            left_on="source_id",
            right_on="id",
            how="left"
        )
        .rename({"file": "source_file", "tag": "source_tag", "text": "source_text", "path": "source_path"})
        .join(
            df.with_row_count("id").select(["id", "file", "tag", "text", "path"]),
            left_on="target_id",
            right_on="id",
            how="left"
        )
        .rename({"file": "target_file", "tag": "target_tag", "text": "target_text", "path": "target_path"})
        .sort("similarity", descending=True)
    )
    
    return result