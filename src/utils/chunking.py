import re
from typing import List
from src.utils.logger import setup_logger

"""Provides a basic utility for chunking text into smaller segments.

This module contains a function for splitting large strings of text into
fixed-size chunks based on word count, which is a common preprocessing step
in NLP workflows.
"""

logger = setup_logger()

def chunk_text(text: str, max_tokens: int = 512, method: str = 'simple') -> List[str]:
    """
    Splits a string of text into smaller chunks based on word count.

    This function implements a simple chunking strategy that splits text by whitespace
    and groups words into chunks of a specified maximum size.

    Args:
        text (str): The input text to be chunked.
        max_tokens (int): The maximum number of words allowed in each chunk.
            Defaults to 512.
        method (str): The chunking method to use. Currently, only 'simple' is
            supported. Defaults to 'simple'.

    Returns:
        List[str]: A list of text chunks. Returns an empty list if the input
        text is empty or the method is unsupported.
    """
    if not text or not text.strip():
        logger.warning("Empty text provided to chunk_text.")
        return []
    if method == 'simple':
        words = re.split(r"\s+", text)
        chunks = []
        for i in range(0, len(words), max_tokens):
            chunk = " ".join(words[i:i+max_tokens])
            if chunk.strip():
                chunks.append(chunk)
        if not chunks:
            logger.warning("No chunks produced from text.")
        return chunks
    else:
        logger.error(f"Unsupported chunking method: {method}")
        return []

# Example usage
if __name__ == "__main__":
    sample_text = "This is a test. " * 300
    chunks = chunk_text(sample_text, max_tokens=50)
    print(f"Produced {len(chunks)} chunks.")
    for i, chunk in enumerate(chunks[:2]):
        print(f"Chunk {i+1}: {chunk[:60]}...") 