import re
from typing import List, Dict, Optional, Any

"""
Provides functionality for filtering metadata based on semantic similarity.

This module uses sentence transformers to compute embeddings for both a query and
metadata summaries, allowing for semantic filtering of search results. It is designed
to refine datasets by retaining only the entries that are most relevant to a
given query.
"""

def filter_metadata_semantic(
    metadata_list: List[Dict[str, Any]],
    query: str,
    min_year: Optional[int] = None,
    min_similarity: float = 0.5,
    model_name: str = 'all-MiniLM-L6-v2',
) -> List[Dict[str, Any]]:
    """
    Filters a list of metadata entries based on semantic similarity to a query.

    This function computes the cosine similarity between the embedding of the query
    and the embedding of the summary for each metadata entry. Entries with a
    similarity score below the specified threshold are discarded.

    Args:
        metadata_list (List[Dict]): A list of metadata dictionaries, where each
            dictionary is expected to have a 'summary' key.
        query (str): The query string to compare against.
        min_year (int, optional): Only keep entries published after this year.
        min_similarity (float): Minimum semantic similarity (0-1) to keep an entry.
        model_name (str): The name of the sentence-transformer model to use for
            embeddings. Defaults to 'all-MiniLM-L6-v2'.

    Returns:
        List[Dict]: A filtered list of metadata dictionaries that meet the
        similarity threshold.
    """
    from sentence_transformers import SentenceTransformer, util
    model = SentenceTransformer(model_name)
    query_emb = model.encode(query, convert_to_tensor=True)
    filtered = []
    for entry in metadata_list:
        # --- Year filter ---
        if min_year:
            pub = entry.get("published", "")
            year_match = re.match(r"(\d{4})", pub)
            if not year_match or int(year_match.group(1)) < min_year:
                continue
        # --- Semantic similarity filter ---
        text = entry.get("title", "") + " " + entry.get("summary", "")
        if not text.strip():
            continue
        score = util.pytorch_cos_sim(query_emb, model.encode(text, convert_to_tensor=True)).item()
        if score < min_similarity:
            continue
        entry["semantic_similarity"] = score
        filtered.append(entry)
    return filtered

# Example usage:
if __name__ == "__main__":
    import json
    # Load some metadata
    with open("data/test_project/deduplicated/metadata.json", "r", encoding="utf-8") as f:
        meta = json.load(f)
    filtered = filter_metadata_semantic(
        meta,
        query="machine learning",
        min_year=2020,
        min_similarity=0.5,
        model_name='all-MiniLM-L6-v2'
    )
    print(f"Filtered down to {len(filtered)} entries.")
    # Optionally, print top results by similarity
    filtered = sorted(filtered, key=lambda x: x["semantic_similarity"], reverse=True)
    for entry in filtered[:5]:
        print(entry["title"], entry["semantic_similarity"]) 