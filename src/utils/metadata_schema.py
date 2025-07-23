"""
Defines the Pydantic-based unified metadata schema for the application.

This schema standardizes the structure of metadata collected from various sources,
including academic databases (e.g., arXiv, PubMed) and general web content.
Using Pydantic ensures data validation, type enforcement, and clear documentation
for all data interchange operations.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Metadata(BaseModel):
    """
    A Pydantic model representing a single metadata entry.

    This model serves as the canonical structure for any document, article, or resource
    processed by the system. It includes fields for academic citations, web sources,
    and internal tracking.
    """
    id: str = Field(..., description="A unique identifier for the metadata entry. Can be a DOI, PMID, arXiv ID, or a hash of the URL.")
    title: str = Field(..., description="The primary title of the document or resource.")
    authors: List[str] = Field(default_factory=list, description="A list of author names associated with the work.")
    published: str = Field(..., description="The publication date in ISO 8601 format or year as a string.")
    summary: str = Field(..., description="A summary, abstract, or snippet of the content.")
    source: str = Field(..., description="The name of the source fetcher (e.g., 'arxiv', 'websearch').")
    link: str = Field(..., description="The canonical URL linking to the resource's landing page or main entry.")
    pdf_url: Optional[str] = Field(None, description="A direct URL to the PDF version of the document, if available.")
    doi: Optional[str] = Field(None, description="The Digital Object Identifier (DOI) of the work, if available.")
    pmid: Optional[str] = Field(None, description="The PubMed ID (PMID) for biomedical literature, if available.")
    paperId: Optional[str] = Field(None, description="The Semantic Scholar Paper ID, if available.")
    citationCount: Optional[int] = Field(None, description="The citation count for the work, if available.")
    displayLink: Optional[str] = Field(None, description="The display URL or domain name, typically for web search results.")
    tags: Optional[List[str]] = Field(None, description="A list of keywords, tags, or categories associated with the work.")
    fetch_date: Optional[str] = Field(None, description="The ISO 8601 timestamp indicating when the metadata was fetched.")
    paywalled: Optional[bool] = Field(None, description="A boolean flag indicating if the content is behind a paywall.")
    extra: Optional[Dict[str, Any]] = Field(None, description="A dictionary for any other source-specific metadata fields.")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "2507.02864v1",
                "title": "MultiGen: Using Multimodal Generation in Simulation to Learn Multimodal Policies in Real",
                "authors": ["Renhao Wang", "Haoran Geng", "Tingle Li"],
                "published": "2025-07-03T17:59:58+00:00",
                "summary": "Robots must integrate multiple sensory modalities ...",
                "source": "arxiv",
                "link": "http://arxiv.org/abs/2507.02864v1",
                "pdf_url": "http://arxiv.org/pdf/2507.02864v1",
                "fetch_date": "2025-07-08T12:00:00Z"
            }
        } 