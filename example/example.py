#!/usr/bin/env python
"""Example script for mdbed."""

import os
from pathlib import Path

import polars as pl

from mdbed import (
    compute_embeddings,
    find_similar_nodes,
    get_files,
    markdown_to_dataframe,
    read_file_content,
    register_embedding_model,
)

# Path to example data
DATA_DIR = Path(__file__).parent / "data"

# Model to use
MODEL_NAME = "Xenova/bge-small-en-v1.5"

def main():
    """Run the example."""
    print(f"Processing markdown files in {DATA_DIR}")
    
    # Register the embedding model
    register_embedding_model(MODEL_NAME)
    
    # Get markdown files
    files_df = get_files(
        paths=[str(DATA_DIR)],
        filter_expr='{name}.str.ends_with(".md")',
        recursive=True,
        merge_all=True,
    )
    
    # Filter out directories
    files_df = files_df.filter(~pl.col("is_dir"))
    
    if files_df.is_empty():
        print("No markdown files found.")
        return
    
    print(f"Found {files_df.height} markdown files:")
    print(files_df.select("name"))
    
    # Process each file
    all_nodes = []
    for file_path in files_df.select("path").to_series():
        file_str = str(file_path)
        print(f"Processing {file_str}")
        content = read_file_content(file_path)
        nodes_df = markdown_to_dataframe(content, file_str)
        all_nodes.append(nodes_df)
    
    # Combine all nodes
    nodes_df = pl.concat(all_nodes)
    print(f"Extracted {nodes_df.height} nodes from {len(all_nodes)} files")
    
    # Compute embeddings
    print("Computing embeddings...")
    nodes_with_emb = compute_embeddings(
        nodes_df,
        text_column="text",
        model_name=MODEL_NAME,
        output_column="embedding",
    )
    print("Embeddings computed")
    
    # Find similar nodes with a threshold of 0.7
    print("Finding similar nodes...")
    similar_nodes = find_similar_nodes(
        nodes_with_emb,
        embedding_column="embedding",
        similarity_threshold=0.7,
        model_name=MODEL_NAME,
    )
    
    # Display results
    if similar_nodes.is_empty():
        print("No similar nodes found.")
    else:
        print(f"Found {similar_nodes.height} similar node pairs:")
        display_df = similar_nodes.select([
            "source_file", 
            "source_text", 
            "target_file", 
            "target_text", 
            "similarity"
        ]).sort("similarity", descending=True)
        print(display_df)
        
        # Write results to CSV
        output_file = "similar_nodes.csv"
        similar_nodes.write_csv(output_file)
        print(f"Results written to {output_file}")
        
        # Create a network visualization for similar nodes
        print("\nNode similarity network:")
        for i in range(min(10, similar_nodes.height)):  # Print top 10 most similar pairs
            row = similar_nodes.row(i)
            src_txt = row[similar_nodes.columns.index("source_text")]
            tgt_txt = row[similar_nodes.columns.index("target_text")]
            sim = row[similar_nodes.columns.index("similarity")]
            
            # Truncate text for display
            src_txt = (src_txt[:50] + "...") if len(src_txt) > 50 else src_txt
            tgt_txt = (tgt_txt[:50] + "...") if len(tgt_txt) > 50 else tgt_txt
            
            print(f"{src_txt} <--[{sim:.3f}]--> {tgt_txt}")


if __name__ == "__main__":
    main()