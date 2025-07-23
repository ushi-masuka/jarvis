import os
import sys
from typing import Dict, Any

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.utils.logger import setup_logger

"""
Provides basic text processing utilities.

This module contains helper functions for common text-related operations,
such as safely extracting text content from metadata dictionaries.
"""

logger = setup_logger()

def extract_text(entry: Dict[str, Any]) -> str:
    """
    Safely extracts the full text content from a metadata entry.

    This function retrieves the value associated with the 'full_text' key
    from a given metadata dictionary. It handles cases where the key is
    missing or the text is empty/whitespace-only.

    Args:
        entry (Dict[str, Any]): A dictionary representing a metadata entry,
            which may contain a 'full_text' field.

    Returns:
        str: The extracted full text. Returns an empty string if 'full_text'
        is not found or is empty.
    """
    text = entry.get("full_text", "")
    if not text or not text.strip():
        logger.warning(f"No full_text found for entry: {entry.get('title', 'No title')}")
        return ""
    return text
