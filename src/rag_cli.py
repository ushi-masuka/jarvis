"""
Provides a command-line interface (CLI) for interacting with the RAG system.

This module contains the main entry point for running queries against the
Retrieval-Augmented Generation (RAG) pipeline from the command line. It handles
argument parsing for specifying the project, query, and other parameters.
"""

import argparse

def main():
    """
    The main entry point for the RAG command-line interface.

    This function parses command-line arguments, including the project name and
    the user's query, and will eventually orchestrate the call to the RAG pipeline.
    """
    parser = argparse.ArgumentParser(description='Jarvis RAG CLI')
    parser.add_argument('--project', type=str, required=True, help='Project name')
    parser.add_argument('--query', type=str, help='User question/query')
    # Add more arguments as needed (e.g., --mode, --tts, etc.)
    args = parser.parse_args()
    print(f"[Stub] Would run RAG for project '{args.project}' with query '{args.query}'")

if __name__ == "__main__":
    main()
