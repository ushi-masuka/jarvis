# Jarvis: AI Multi-Expert Research Assistant

## Vision
Jarvis is an open-source, modular research/study assistant designed to help users explore, learn, and innovate in any field. Each project workspace is isolated, with its own memory and a dedicated expert model. Jarvis autonomously gathers, processes, and reasons over knowledge from diverse sources, providing expert-level answers, teaching, and trend analysis.

## Key Features
- **Project Workspaces**: Each research project is isolated with its own data, memory, and model.
- **Automated Knowledge Acquisition**: Fetches research papers, books, articles, blogs, and media from sources like arXiv, PubMed, Semantic Scholar, Google Books, Wikipedia, and more.
- **Semantic Ingestion**: Cleans, chunks, embeds, and stores data in a vector database or knowledge graph for deep retrieval and understanding.
- **Multi-Expert Reasoning**: Routes queries to the most relevant expert agent for grounded, multi-step answers.
- **Teaching & Explanation**: Explains concepts step-by-step using analogies, diagrams, flashcards, quizzes, and text-to-speech.
- **Trend Analysis**: Identifies research trends, gaps, and consensus/disagreement across sources.
- **Interactive UI**: CLI with rich markdown, color-coded responses, and command flags; GUI planned for the future.
- **Personalized Memory**: Remembers user queries, preferences, and feedback within each project.
- **Security & Extensibility**: Secure secrets management and plugin-friendly architecture for new fetchers, experts, or analysis modules.

## Example User Journey
1. **Create a Project**: Start a new workspace (e.g., "AI in Chemistry") and specify research goals.
2. **Define Focus**: Enter research questions or keywords.
3. **Automated Fetching**: Jarvis gathers relevant documents and media.
4. **Ingestion & Indexing**: Data is processed and stored for efficient retrieval.
5. **Ask Questions**: Query Jarvis via CLI (or GUI in future) for expert-level answers.
6. **Learn & Explore**: Use teaching, explanation, and trend analysis features to deepen understanding and discover new research directions.

## Project Structure & Progress

```
# Top-level
├── data/                    # Project data storage
│   └── [project_name]/      # Each project workspace
│       ├── arxiv/           # [Completed] ArXiv fetcher output
│       ├── pubmed/          # [Completed] PubMed fetcher output
│       ├── web/             # [Partial] Web/Blog fetchers (basic done, needs expansion)
├── transcripts/             # [Planned] Media/audio transcripts
├── src/                     # Source code
│   ├── fetchers/            # Data fetchers
│   │   ├── arxiv_fetcher.py             # [Completed]
│   │   ├── pubmed_fetcher.py            # [Completed]
│   │   ├── semantic_scholar_fetcher.py  # [Completed]
│   │   ├── web_search_fetcher.py        # [Partial]
│   │   ├── blog_fetcher.py              # [Partial]
│   │   ├── medium_fetcher.py            # [Partial]
│   │   └── ...                          # [Planned] More sources (social, paid, etc.)
│   ├── ingest.py            # [Completed] Semantic ingestion pipeline
│   ├── memory.py            # [Planned] Project memory/context
│   ├── rag_cli.py           # [Partial] CLI interface
│   ├── tts.py               # [Partial] Text-to-speech
│   ├── trend_analyzer.py    # [Stub] Trend/gap analysis
│   ├── agent.py             # [Planned] Main agent logic
│   ├── expert_router.py     # [Stub] Query routing
│   ├── data_analyzer.py     # [Stub] Data analysis
│   ├── data_processor.py    # [Stub] Summarization/translation
│   ├── multi_modal_fetcher.py # [Stub] Images/videos fetcher
│   └── utils/               # Utilities
│       ├── chunking.py              # [Completed]
│       ├── deduplicator.py          # [Completed]
│       ├── embedding.py             # [Completed]
│       ├── enrichment.py            # [Completed]
│       ├── extraction.py            # [Completed]
│       ├── logger.py                # [Completed]
│       ├── metadata_filter.py       # [Completed]
│       ├── metadata_schema.py       # [Completed]
│       ├── query_processor.py       # [Partial]
│       ├── vector_db.py             # [Partial]
│       └── ...                      # [Planned] More utils
├── tests/                  # [Partial] Unit tests
├── .env                    # [Completed] Environment config
├── requirements.txt        # [Completed] Dependencies
├── README.md               # [Completed] Project overview
├── user_story.md           # [Completed] User journey
├── function specification.txt # [Completed] System specs
└── working-plan.txt        # [Partial] Planning/tracking
```

**Legend:**
- [Completed] Module is implemented and functional
- [Partial] Module exists but needs more features or polish
- [Stub] Minimal code exists; full implementation needed
- [Planned] Not yet implemented

**Major To-Do (Priority: Core Stability & Data Quality):**
- **Fix Critical Fetcher Bugs**:
  - Address issues in `arxiv_fetcher.py` and `medium_fetcher.py`.
  - Correct `trafilatura` usage in `blog_fetcher.py`.
- **Improve Data Extraction**:
  - Implement a multi-layered extraction pipeline (`trafilatura`, `readability-lxml`, etc.) in `utils/extraction.py`.
  - Add robust PDF extraction using `PyMuPDF`.
- **Stabilize Ingestion Pipeline**:
  - Sanitize metadata in `ingest.py` to prevent database errors.
  - Add logging and reporting to `data_fetcher.py` to monitor success/failure rates.
- **Revamp Query Processing**:
  - Improve the query processor (`query_processor.py`) to handle special words and generate better, source-specific queries.


## Getting Started
1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd jarvis
   ```
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Set up environment variables**
   - Copy `.env.example` to `.env` and fill in API keys, DB URIs, etc.
4. **Run the CLI**
   ```bash
   python src/rag_cli.py --help
   ```

## Development Guidelines
- **Modular Design**: Each module (fetcher, ingest, agent, tts, etc.) should be isolated and importable.
- **Namespace Hygiene**: Use project-specific namespaces for all data and memory.
- **Prompt Safety**: Sanitize and validate all user inputs and tool calls.
- **Observability**: Use structured logging; enable verbose mode with CLI flags.
- **Error Handling**: Wrap all fetch/scrape calls with retries, timeouts, and fallbacks.
- **Testing**: Write unit tests for all modules (see `/tests`).
- **Performance**: Batch embeddings and retrievals; cache frequently-used content.
- **Prompt Templates**: Store in `templates/` with versioning.
- **Config Management**: Centralize in `settings.py` and `.env`.
- **Documentation**: Every module should have docstrings and usage examples.
- **Extensibility**: Add new sources, experts, or modes via plugins.
- **Security**: Respect robots.txt, paywalls, and API quotas; never expose secrets.

## Contributing
Contributions are welcome! Please read the user story (`user_story.md`) and function specifications before submitting pull requests. Open issues for bugs, feature requests, or questions.



---

For more details, see `user_story.md` and `function specification.txt`.
