from typing import List
from src.utils.logger import setup_logger

"""Provides a utility for generating vector embeddings from text.

This module contains a function that leverages the 'sentence-transformers'
library to convert text chunks into high-dimensional vector representations,
which are essential for semantic search and other NLP tasks.
"""

logger = setup_logger()

def embed_chunks(chunks: List[str], model_name: str = 'all-MiniLM-L6-v2') -> List[List[float]]:
    """
    Generates vector embeddings for a list of text chunks.

    This function uses a specified sentence-transformer model to encode a list
    of text strings into a corresponding list of floating-point vectors.

    Args:
        chunks (List[str]): A list of text chunks to be embedded.
        model_name (str): The name of the sentence-transformer model to use.
            Defaults to 'all-MiniLM-L6-v2'.

    Returns:
        List[List[float]]: A list of embedding vectors. Returns an empty list
        if the input is empty or if an error occurs during the process.
    """
    if not chunks:
        logger.warning("No chunks provided to embed_chunks.")
        return []
    try:
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading embedding model: {model_name}")
        model = SentenceTransformer(model_name)
        logger.info(f"Embedding {len(chunks)} chunks...")
        embeddings = model.encode(chunks, show_progress_bar=False)
        return embeddings.tolist()
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        return []

# Example usage
if __name__ == "__main__":
    sample_chunks = ["This is the first chunk.", "This is the second chunk."]
    embs = embed_chunks(sample_chunks)
    print(f"Produced {len(embs)} embeddings.")
    for i, emb in enumerate(embs):
        print(f"Embedding {i+1}: {emb[:5]} ...") 