from typing import List, Dict, Any
from src.utils.logger import setup_logger

"""Provides functionality for interacting with a ChromaDB vector database.

This module contains utilities for upserting document chunks and their corresponding
embeddings into a persistent ChromaDB collection, handling data sanitization
to ensure compatibility.
"""

logger = setup_logger()

def upsert_to_vector_db(chunks: List[Dict[str, Any]], embeddings: List[List[float]], project_name: str):
    """
    Upserts document chunks and their embeddings into a ChromaDB collection.

    This function connects to a persistent ChromaDB client, sanitizes the metadata
    associated with each chunk to ensure it is ChromaDB-compatible, and then
    upserts the data. A unique ID is generated for each chunk.

    Args:
        chunks (List[Dict[str, Any]]): A list of dictionaries, where each
            dictionary represents a chunk of a document.
        embeddings (List[List[float]]): A list of embedding vectors, where each
            vector corresponds to a chunk in the `chunks` list.
        project_name (str): The name of the ChromaDB collection to upsert to.
    """
    try:
        import chromadb
        # Use a persistent client to save data to disk
        client = chromadb.PersistentClient(path="chroma_db")
        collection = client.get_or_create_collection(name=project_name)
        logger.info(f"Upserting {len(chunks)} chunks to ChromaDB collection '{project_name}'...")
        ids = []
        metadatas = []
        documents = []
        for chunk in chunks:
            # Use a unique id for each chunk (e.g., based on entry id and chunk index)
            base_id = chunk.get("id") or chunk.get("link") or str(hash(str(chunk)))
            chunk_id = f"{base_id}_chunk{chunk.get('chunk_index', 0)}"
            ids.append(chunk_id)

            # Sanitize metadata: convert lists and dicts to strings for ChromaDB
            sanitized_meta = {}
            for key, value in chunk.items():
                if isinstance(value, list):
                    sanitized_meta[key] = ", ".join(map(str, value))
                elif isinstance(value, dict):
                    sanitized_meta[key] = str(value)
                else:
                    sanitized_meta[key] = value
            
            metadatas.append(sanitized_meta)
            documents.append(chunk.get("chunk_text", ""))
        # ChromaDB upsert
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )
        logger.info(f"Successfully upserted {len(ids)} chunks to ChromaDB collection '{project_name}'.")
    except ImportError:
        logger.error("chromadb is not installed. Please install it to use vector DB upsert.")
    except Exception as e:
        logger.error(f"Failed to upsert to ChromaDB: {e}")

# Example usage
if __name__ == "__main__":
    # Minimal example
    chunks = [
        {"id": "doc1", "chunk_index": 0, "chunk_text": "This is a test chunk."},
        {"id": "doc1", "chunk_index": 1, "chunk_text": "This is another chunk."}
    ]
    embeddings = [[0.1]*384, [0.2]*384]  # Example embeddings (should match model dim)
    upsert_to_vector_db(chunks, embeddings, "test_project") 