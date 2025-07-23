import re
from typing import Callable, Dict, Optional

"""
This module provides functionalities for processing and rewriting user queries to enhance search effectiveness across various data sources. It supports both classic NLP transformations (normalization, stopword removal) and modern LLM-based query rewriting for source-specific optimization.

Key Components:
- Classic Processors: Functions for text normalization, stopword removal, and synonym expansion using NLTK.
- Fetcher-Specific Logic: Tailored processing pipelines for different targets like PubMed, arXiv, and web search.
- LLM-Based Rewriting: Integration with LangChain to leverage large language models for intelligent query rewriting based on predefined prompt templates.
"""

# --- Classic Query Processing ---

def normalize_query(query: str) -> str:
    """
    Normalizes a raw query string.

    Actions:
    1. Converts the string to lowercase.
    2. Removes all non-alphanumeric characters, replacing them with spaces.
    3. Collapses multiple whitespace characters into a single space.

    Args:
        query (str): The raw input query.

    Returns:
        str: The normalized query string.
    """
    query = query.lower()
    query = re.sub(r'\W+', ' ', query)
    return ' '.join(query.split())



# --- Fetcher-Specific Classic Logic ---
def advanced_classic_process(query: str) -> str:
    """
    Processes a query using an advanced pipeline that preserves search operators.

    This function identifies and preserves boolean operators (AND, OR, NOT) and
    quoted phrases, which are critical for academic search engines. Other parts
    of the query are normalized (lowercase, punctuation removal).

    Args:
        query (str): The raw input query.

    Returns:
        str: The processed query, ready for a search engine.
    """
    # Split the query by operators and quotes, keeping them as delimiters
    parts = re.split(r'("[^"_]*"|\bAND\b|\bOR\b|\bNOT\b)', query, flags=re.IGNORECASE)
    
    processed_parts = []
    for part in parts:
        if not part or part.isspace():
            continue

        # Check if the part is a special operator/quote
        if re.fullmatch(r'"[^"_]*"|\bAND\b|\bOR\b|\bNOT\b', part, re.IGNORECASE):
            # Preserve operators in uppercase, and quotes as is
            if part.upper() in ["AND", "OR", "NOT"]:
                processed_parts.append(part.upper())
            else:
                processed_parts.append(part)
        else:
            # Normalize the other parts
            processed_parts.append(normalize_query(part))
            
    # Join parts, ensuring clean spacing
    return ' '.join(filter(None, processed_parts))

def web_query_processor(query: str) -> str:
    """
    Processes a query for web search fetchers (Google, blogs, etc.).

    Args:
        query (str): The input query.

    Returns:
        str: A whitespace-trimmed query.
    """
    return query.strip()

FETCHER_PROCESSORS: Dict[str, Callable[[str], str]] = {
    "pubmed": advanced_classic_process,
    "arxiv": advanced_classic_process,
    "semanticscholar": advanced_classic_process,
    "websearch": web_query_processor,
    "blog": web_query_processor,
    "medium": web_query_processor,
}

def process_query(query: str, fetcher: str = "default", use_classic: bool = True) -> str:
    """
    Selects and applies the appropriate query processor based on the fetcher type.

    If `use_classic` is False, it returns the original query. Otherwise, it looks up
    the processor in the `FETCHER_PROCESSORS` mapping. If no specific processor is
    found, it defaults to `normalize_query`.

    Args:
        query (str): The raw input query.
        fetcher (str): The identifier for the target fetcher (e.g., 'pubmed').
        use_classic (bool): Flag to enable or disable classic processing.

    Returns:
        str: The processed query.
    """
    processor = FETCHER_PROCESSORS.get(fetcher, normalize_query)
    if use_classic:
        return processor(query)
    else:
        return query

# --- LLM-Based Query Rewriting (LangChain) ---
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

PROMPT_TEMPLATES = {
    "pubmed": "Rewrite the following user query for a PubMed search. Use biomedical terminology and MeSH terms if possible.\n\nUser query: {query}",
    "arxiv": "Rewrite the following user query as concise, technical keywords for an arXiv search.\n\nUser query: {query}",
    "semanticscholar": "Rewrite the following user query for Semantic Scholar, using academic phrasing.\n\nUser query: {query}",
    "websearch": "Rewrite the following user query as a natural Google search.\n\nUser query: {query}",
    "default": "Rewrite the following query to optimize it for academic search.\n\nUser query: {query}",
}

def llm_rewrite_query_langchain(
    query: str,
    fetcher: str = "default",
    model: str = "gpt-3.5-turbo",
    api_key: Optional[str] = None,
) -> str:
    """
    Rewrites a query using an LLM via the LangChain framework.

    Selects a prompt template based on the `fetcher` and uses it to guide the LLM
    in rewriting the query for the target data source. Requires a valid OpenAI API key.

    Args:
        query (str): The user's original query.
        fetcher (str): The target fetcher, used to select a prompt template.
        model (str): The name of the OpenAI model to use (e.g., 'gpt-3.5-turbo').
        api_key (Optional[str]): The OpenAI API key. If not provided, it must be
            available in the environment.

    Returns:
        str: The rewritten query from the LLM.
    """
    template_str = PROMPT_TEMPLATES.get(fetcher, PROMPT_TEMPLATES["default"])
    prompt = PromptTemplate.from_template(template_str)
    llm = ChatOpenAI(model=model, openai_api_key=api_key)
    chain = prompt | llm
    rewritten = chain.invoke({"query": query})
    return rewritten.content.strip()

# --- Example usage ---
if __name__ == "__main__":
    sample_query = "What are the latest advances in protein folding using machine learning?"
    for fetcher in ["pubmed", "arxiv", "semanticscholar", "websearch"]:
        print(f"\n[{fetcher.upper()}] Classic: {process_query(sample_query, fetcher)}")
        # Uncomment below to test LLM rewriting (requires OpenAI API key)
    # print("\n[LLM REWRITE]")
    # for fetcher in ["pubmed", "arxiv", "semanticscholar", "websearch"]:
    #     rewritten = llm_rewrite_query_langchain(sample_query, fetcher=fetcher)
    #     print(f"  - {fetcher.upper()}: {rewritten}")