import os
import sys
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.utils.logger import setup_logger

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(project_root)

logger = setup_logger()
logger.info("Deduplicator logger initialized")

def deduplicate_metadata(project_name: str) -> list:
    """
    Deduplicate metadata from all fetchers and save the unique entries.

    Args:
        project_name (str): The name of the project to process data from.

    Returns:
        list: A list of dictionaries containing unique metadata entries.
    """
    data_dir = os.path.join("data", project_name)
    unique_entries = []
    seen_identifiers = set()

    # Dynamically get all source directories, excluding 'deduplicated'
    source_dirs = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d)) and d != "deduplicated"]
    
    if not source_dirs:
        logger.info(f"No source directories found in {data_dir}")
        return []

    for source in source_dirs:
        source_path = os.path.join(data_dir, source)
        logger.info(f"Processing metadata from {source}")
        json_files = [f for f in os.listdir(source_path) if f.endswith(".json")]
        
        if not json_files:
            logger.info(f"No JSON files found in {source_path}")
            continue
        
        for filename in json_files:
            file_path = os.path.join(source_path, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Handle different possible formats
                    if isinstance(data, list):
                        entries = data
                    elif isinstance(data, dict):
                        entries = [data]  # Treat single dict as a list of one entry
                    else:
                        logger.warning(f"Unsupported data format in {file_path}, skipping")
                        continue

                    for entry in entries:
                        identifier = None
                        for field in ["doi", "pmid", "paperId", "pdf_url", "id", "link"]:
                            value = entry.get(field)
                            if value:
                                if field in ["link", "pdf_url"]:
                                    value = value.replace("http://", "").replace("https://", "").replace("/", "_")
                                identifier = value
                                break
                        if identifier:
                            identifier_hash = hash(str(identifier))
                            if identifier_hash not in seen_identifiers:
                                seen_identifiers.add(identifier_hash)
                                unique_entries.append(entry)
                                logger.info(f"Added entry: {entry.get('title', 'No title')} from {source}")
                            else:
                                logger.info(f"Duplicate found and skipped: {entry.get('title', 'No title')} from {source}")
                        else:
                            logger.warning(f"No valid identifier found in {file_path}, skipping entry")
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON in {file_path}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error processing {file_path}: {e}")

    # Save deduplicated metadata
    dedup_dir = os.path.join(data_dir, "deduplicated")
    os.makedirs(dedup_dir, exist_ok=True)
    dedup_path = os.path.join(dedup_dir, "metadata.json")
    with open(dedup_path, "w", encoding="utf-8") as f:
        json.dump(unique_entries, f, indent=4, ensure_ascii=False)
    logger.info(f"Deduplicated {len(unique_entries)} entries, saved to {dedup_path}")

    return unique_entries

if __name__ == "__main__":
    project_name = "test_project"
    deduplicate_metadata(project_name)