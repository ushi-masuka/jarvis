from typing import Dict, Any
from src.utils.logger import setup_logger

"""Provides a utility for enriching metadata at the text chunk level.

This module contains a function to augment a document's metadata with
chunk-specific information, such as the chunk's text and its index. This
process is vital for creating detailed records for vectorization and retrieval.
"""

logger = setup_logger()

def enrich_chunk_metadata(entry: Dict[str, Any], chunk: str, chunk_idx: int) -> Dict[str, Any]:
    """Enriches a document's metadata with chunk-specific information.

    This function creates a copy of a document's metadata record and adds
    details about a specific text chunk, including its content and index.

    Args:
        entry (Dict[str, Any]): The original metadata dictionary for the document.
        chunk (str): The text content of the chunk.
        chunk_idx (int): The zero-based index of the chunk within the document.

    Returns:
        Dict[str, Any]: A new dictionary containing the enriched metadata.
        Returns an empty dictionary if the operation fails.
    """
    try:
        meta = entry.copy()
        meta["chunk_index"] = chunk_idx
        meta["chunk_text"] = chunk
        # Placeholder for future chunk-level summary/tags
        # meta["chunk_summary"] = "..."
        # meta["chunk_tags"] = ["..."]
        return meta
    except Exception as e:
        logger.error(f"Failed to enrich chunk metadata: {e}")
        return {}

# Example usage
if __name__ == "__main__":
    entry = {"title": "Test Paper", "authors": ["A. Author"], "fulltext_path": "example.pdf"}
    chunk = "This is a chunk of text."
    enriched = enrich_chunk_metadata(entry, chunk, 0)
    print(enriched) 