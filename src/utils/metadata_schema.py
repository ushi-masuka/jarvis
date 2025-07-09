from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Metadata(BaseModel):
    """
    Unified metadata schema for all data sources (papers, articles, blogs, web, etc.).
    Fields are designed to be as inclusive as possible for academic and web content.
    """
    id: str = Field(..., description="Unique identifier (DOI, PMID, arXiv ID, URL hash, etc.)")
    title: str = Field(..., description="Title of the work")
    authors: List[str] = Field(default_factory=list, description="List of author names")
    published: str = Field(..., description="ISO 8601 date or year of publication")
    summary: str = Field(..., description="Abstract, summary, or snippet of the work")
    source: str = Field(..., description="Source/fetcher name (arxiv, pubmed, semanticscholar, web, blog, etc.)")
    link: str = Field(..., description="Canonical URL to the work (PDF, landing page, etc.)")
    pdf_url: Optional[str] = Field(None, description="Direct link to PDF (if available)")
    doi: Optional[str] = Field(None, description="DOI (if available)")
    pmid: Optional[str] = Field(None, description="PubMed ID (if available)")
    paperId: Optional[str] = Field(None, description="Semantic Scholar ID (if available)")
    citationCount: Optional[int] = Field(None, description="Number of citations (if available)")
    displayLink: Optional[str] = Field(None, description="Display domain (for web/blog/news)")
    tags: Optional[List[str]] = Field(None, description="List of tags, keywords, or categories")
    fetch_date: Optional[str] = Field(None, description="When this record was fetched (ISO 8601)")
    paywalled: Optional[bool] = Field(None, description="True if the content is behind a paywall")
    extra: Optional[Dict[str, Any]] = Field(None, description="Any additional source-specific metadata")

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