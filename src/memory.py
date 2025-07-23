"""
Provides a class for managing project-specific conversational memory.

This module defines the Memory class, which handles the storage and retrieval
of interactions, metadata, and user preferences for a given project. All data
is persisted to a JSON file.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from src.utils.logger import setup_logger

logger = setup_logger()

class Memory:
    """
    Manages the memory for a single project, stored in a JSON file.

    This class provides an interface to load, save, and manipulate the memory
    data, which includes a history of user interactions, project-level metadata,
    and user-defined preferences.

    Attributes:
        project_name (str): The name of the project.
        memory_path (str): The file path to the project's memory JSON file.
        data (Dict[str, Any]): The in-memory representation of the JSON data.
    """

    def __init__(self, project_name: str, memory_dir: str = "data"):
        """
        Initializes the Memory instance for a specific project.

        Args:
            project_name (str): The identifier for the project.
            memory_dir (str): The root directory where project data is stored.
        """
        self.project_name = project_name
        self.memory_path = os.path.join(memory_dir, project_name, "memory.json")
        self.data = {
            "project": project_name,
            "metadata": {},
            "interactions": [],
            "preferences": {}
        }
        self._load()

    def _load(self):
        """Loads the memory data from the JSON file if it exists."""
        if os.path.exists(self.memory_path):
            try:
                with open(self.memory_path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                logger.info(f"Loaded memory for project '{self.project_name}'.")
            except Exception as e:
                logger.error(f"Failed to load memory: {e}")
        else:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.memory_path), exist_ok=True)
            self.save()

    def save(self):
        """Saves the current in-memory data to the JSON file."""
        try:
            with open(self.memory_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            logger.info(f"Memory saved for project '{self.project_name}'.")
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")

    def add_interaction(self, query: str, response: str, sources: Optional[List[Dict[str, Any]]] = None, feedback: Optional[Dict[str, Any]] = None):
        """
        Adds a new user interaction to the memory.

        Args:
            query (str): The user's query.
            response (str): The system's response.
            sources (Optional[List[Dict[str, Any]]]): A list of source documents
                used to generate the response.
            feedback (Optional[Dict[str, Any]]): User feedback on the interaction.
        """
        interaction = {
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "response": response,
            "sources": sources or [],
            "feedback": feedback or {}
        }
        self.data["interactions"].append(interaction)
        self.save()

    def get_recent_interactions(self, n: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieves the most recent interactions.

        Args:
            n (int): The number of recent interactions to retrieve.

        Returns:
            List[Dict[str, Any]]: A list of the n most recent interactions.
        """
        return self.data.get("interactions", [])[-n:]

    def search_memory(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Searches interactions for a specific keyword.

        Args:
            keyword (str): The keyword to search for in queries and responses.

        Returns:
            List[Dict[str, Any]]: A list of interactions matching the keyword.
        """
        return [
            inter for inter in self.data.get("interactions", [])
            if keyword.lower() in inter.get("query", "").lower() or
               keyword.lower() in inter.get("response", "").lower()
        ]

    def clear_memory(self):
        """Clears all interactions from the memory."""
        self.data["interactions"] = []
        self.save()
        logger.info(f"Cleared memory for project '{self.project_name}'.")

    def set_project_metadata(self, metadata: Dict[str, Any]):
        """
        Sets or updates the project-level metadata.

        Args:
            metadata (Dict[str, Any]): A dictionary of metadata to store.
        """
        self.data["metadata"] = metadata
        self.save()

    def get_project_metadata(self) -> Dict[str, Any]:
        """Retrieves the project-level metadata."""
        return self.data.get("metadata", {})

    def set_preferences(self, preferences: Dict[str, Any]):
        """
        Sets or updates the user preferences for the project.

        Args:
            preferences (Dict[str, Any]): A dictionary of user preferences.
        """
        self.data["preferences"] = preferences
        self.save()

    def get_preferences(self) -> Dict[str, Any]:
        """Retrieves the user preferences for the project."""
        return self.data.get("preferences", {})

# Example usage (remove or comment out in production)
if __name__ == "__main__":
    mem = Memory("demo_project")
    mem.add_interaction(
        query="What is AI?",
        response="AI stands for Artificial Intelligence.",
        sources=[{"type": "wikipedia", "id": "AI"}],
        feedback={"rating": 5}
    )
    print(mem.get_recent_interactions())