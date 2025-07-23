import os
import sys
import json
import re
from typing import List, Dict, Any, Callable, Optional
from tqdm import tqdm

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.utils.logger import setup_logger

"""
Handles the data ingestion pipeline for a project.

This module is responsible for taking processed and deduplicated metadata,
extracting the associated text, chunking it, generating embeddings, and finally
upserting the data into a vector database for retrieval.
"""

logger = setup_logger()

def sanitize_metadata(entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Sanitizes and validates a single metadata entry.

    This function performs critical data cleaning before ingestion. It ensures
    that essential fields like 'id' and 'title' exist and are well-formed.
    It also cleans non-printable characters from text fields.

    Args:
        entry (Dict[str, Any]): The metadata dictionary for a single document.

    Returns:
        Optional[Dict[str, Any]]: The sanitized metadata dictionary, or None if
        the entry is invalid and should be discarded.
    """
    # ID is critical. Try to create one if missing, but it must exist.
    entry_id = entry.get('id') or entry.get('link')
    if not entry_id:
        logger.error(f"Entry missing 'id' and 'link', cannot process. Title: {entry.get('title', 'N/A')[:50]}")
        return None
    # Clean the ID to be safe for databases/filenames
    entry['id'] = re.sub(r'[^a-zA-Z0-9_.-]', '_', str(entry_id))

    # Ensure 'title' is a non-empty string
    if not entry.get('title') or not isinstance(entry.get('title'), str):
        entry['title'] = "No Title Provided"
        logger.warning(f"Missing or invalid 'title' for entry id: {entry['id']}. Using default.")

    # Ensure 'authors' is a list of strings
    authors = entry.get('authors')
    if not isinstance(authors, list) or not all(isinstance(a, str) for a in authors):
        entry['authors'] = []

    # Sanitize string fields by removing non-printable characters
    for key in ['title', 'summary']:
        if isinstance(entry.get(key), str):
            entry[key] = ''.join(c for c in entry[key] if c.isprintable())

    return entry

def default_imports():
    """
    Lazily imports and returns the default utility functions for the pipeline.

    This helper function attempts to import the standard implementations for each
    stage of the ingestion pipeline. This allows the main `ingest_project` function
    to be decoupled and easily testable with mock components.

    Returns:
        A tuple containing the callable functions for each pipeline stage:
        (extract_text, chunk_text, embed_chunks, enrich_chunk_metadata, upsert_to_vector_db).
        If an import fails, the corresponding item in the tuple will be None.
    """
    try:
        from src.utils.extraction import extract_text
    except ImportError:
        extract_text = None
    try:
        from src.utils.chunking import chunk_text
    except ImportError:
        chunk_text = None
    try:
        from src.utils.embedding import embed_chunks
    except ImportError:
        embed_chunks = None
    try:
        from src.utils.enrichment import enrich_chunk_metadata
    except ImportError:
        enrich_chunk_metadata = None
    try:
        from src.utils.vector_db import upsert_to_vector_db
    except ImportError:
        upsert_to_vector_db = None
    return extract_text, chunk_text, embed_chunks, enrich_chunk_metadata, upsert_to_vector_db

def ingest_project(
    project_name: str,
    embedding_model: str = 'all-MiniLM-L6-v2',
    max_tokens: int = 512,
    extract_text: Optional[Callable] = None,
    chunk_text: Optional[Callable] = None,
    embed_chunks: Optional[Callable] = None,
    enrich_chunk_metadata: Optional[Callable] = None,
    upsert_to_vector_db: Optional[Callable] = None,
):
    """
    Executes the full ingestion pipeline for a given project.

    This function orchestrates the process of converting raw documents into searchable
    vector embeddings. It reads the deduplicated metadata, then for each entry, it
    extracts text, creates chunks, generates embeddings, and enriches the metadata
    for each chunk. Finally, it upserts the results into the vector database.

    The pipeline stages are customizable via dependency injection, allowing for
    flexible configurations and testing.

    Args:
        project_name (str): The name of the project to ingest data for.
        embedding_model (str): The name of the sentence-transformer model for embeddings.
        max_tokens (int): The maximum number of tokens per text chunk.
        extract_text (Optional[Callable]): Function to extract text from a metadata entry.
        chunk_text (Optional[Callable]): Function to split text into chunks.
        embed_chunks (Optional[Callable]): Function to generate embeddings for chunks.
        enrich_chunk_metadata (Optional[Callable]): Function to add chunk-level metadata.
        upsert_to_vector_db (Optional[Callable]): Function to save data to the vector DB.
    """
    # Import utilities if not provided (for normal use, not for testing)
    if not all([extract_text, chunk_text, embed_chunks, enrich_chunk_metadata, upsert_to_vector_db]):
        extract_text, chunk_text, embed_chunks, enrich_chunk_metadata, upsert_to_vector_db = default_imports()

    dedup_path = os.path.join("data", project_name, "deduplicated", "metadata_with_fulltext.json")
    if not os.path.exists(dedup_path):
        logger.error(f"No deduplicated metadata found at {dedup_path}")
        return

    with open(dedup_path, "r", encoding="utf-8") as f:
        original_metadata = json.load(f)
    
    # Sanitize metadata before processing
    metadata_list = [sanitized for entry in original_metadata if (sanitized := sanitize_metadata(entry)) is not None]
    if len(metadata_list) != len(original_metadata):
        logger.warning(f"Sanitization removed {len(original_metadata) - len(metadata_list)} invalid entries.")

    all_chunks = []
    all_embeddings = []
    logger.info(f"Starting ingestion for {len(metadata_list)} entries...")

    for entry in tqdm(metadata_list, desc="Ingesting entries"):
        if not extract_text:
            logger.error("extract_text function not implemented. Skipping entry.")
            continue
        text = extract_text(entry)
        if not text or not text.strip():
            logger.warning(f"No text extracted for entry: {entry.get('title', 'No title')}")
            continue

        if not chunk_text:
            logger.error("chunk_text function not implemented. Skipping entry.")
            continue
        chunks = chunk_text(text, max_tokens=max_tokens)
        if not chunks:
            logger.warning(f"No chunks produced for entry: {entry.get('title', 'No title')}")
            continue

        if not embed_chunks:
            logger.error("embed_chunks function not implemented. Skipping entry.")
            continue
        embeddings = embed_chunks(chunks, model_name=embedding_model)
        if len(embeddings) != len(chunks):
            logger.error(f"Embedding count does not match chunk count for entry: {entry.get('title', 'No title')}")
            continue

        for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            if not enrich_chunk_metadata:
                logger.error("enrich_chunk_metadata function not implemented. Skipping chunk.")
                continue
            chunk_meta = enrich_chunk_metadata(entry, chunk, idx)
            all_chunks.append(chunk_meta)
            all_embeddings.append(emb)

    if not upsert_to_vector_db:
        logger.warning("upsert_to_vector_db function not implemented. Skipping upsert step.")
    else:
        upsert_to_vector_db(all_chunks, all_embeddings, project_name)
        logger.info(f"Upserted {len(all_chunks)} chunks to vector DB for project '{project_name}'.")

    logger.info(f"Ingestion complete: {len(all_chunks)} chunks processed.")

if __name__ == "__main__":
    from src.utils.text_utils import extract_text
    from src.utils.chunking import chunk_text
    from src.utils.embedding import embed_chunks
    from src.utils.enrichment import enrich_chunk_metadata
    from src.utils.vector_db import upsert_to_vector_db

    ingest_project(
        project_name="test_project",
        extract_text=extract_text,
        chunk_text=chunk_text,
        embed_chunks=embed_chunks,
        enrich_chunk_metadata=enrich_chunk_metadata,
        upsert_to_vector_db=upsert_to_vector_db,
    )