# PRD: Unstructured + Weaviate RAG Application

## 1. Goal

Build a Streamlit app that demonstrates a full end-to-end RAG (Retrieval-Augmented Generation) pipeline: upload documents, parse and chunk them via the Unstructured API, embed the chunks via OpenAI, index them into a local Weaviate instance, run hybrid search queries over the indexed content, and generate natural language answers using Claude (Anthropic).

---

## 2. Scope

**In scope:**

- Document ingestion via Unstructured Serverless API
- Chunked output stored in a local Weaviate instance (Docker, `localhost:8080`)
- Hybrid (vector + BM25) search with configurable alpha
- Natural language answer generation via Claude (`claude-sonnet-4-6`)
- Deduplication: re-ingesting a file replaces its existing chunks
- Streamlit frontend
- Support for `.pdf`, `.docx`, `.txt`, `.html`
- Metadata display per source chunk: source file, page number, element type, score

**Out of scope:**

- Authentication or multi-user support
- Production error handling or SLAs
- Custom or fine-tuned embedding models
- Multi-turn chat or agentic workflows

---

## 3. Architecture

Pipeline flow:

```
Raw Documents (PDF / DOCX / TXT / HTML)
         |
         v
  [Unstructured Serverless API]
   - Partition into typed elements
   - Extract metadata (filename, page_number, element_id)
   - Chunk using by_title strategy (max 500 chars, no overlap)
         |
         v
  [Embedding Layer]
   - Batch embed chunks via OpenAI text-embedding-3-small
         |
         v
  [Local Weaviate (Docker)]
   - Delete existing chunks for source file (deduplication)
   - BYOV insertion into DocumentChunk collection
   - BM25 + HNSW indexed on text property
         |
         v
  [Query]
   - Embed query via OpenAI text-embedding-3-small
   - Hybrid search (vector + BM25), top 5 chunks
         |
         v
  [Generation]
   - Retrieved chunks passed as context to Claude (claude-sonnet-4-6)
   - Natural language answer grounded in document content
         |
         v
  [Streamlit UI]
   - File upload, ingest trigger
   - Query input + alpha slider
   - Generated answer + expandable source chunks
```

### Component Summary

| Component              | Technology                                   |
| ---------------------- | -------------------------------------------- |
| Document Parsing + ETL | Unstructured Serverless API                  |
| Vector Database        | Weaviate local via Docker (`localhost:8080`) |
| Embedding Model        | OpenAI `text-embedding-3-small` (1536 dims)  |
| Search Mode            | Hybrid (vector + BM25), configurable alpha   |
| Answer Generation      | Anthropic Claude (`claude-sonnet-4-6`)        |
| Frontend               | Streamlit                                    |
| Language               | Python 3.10+                                 |
| Config                 | python-dotenv                                |

---

## 4. Functional Requirements

### Ingestion

**FR-01: Document Upload**

- Accept one or more files via Streamlit file uploader
- Supported formats: `.pdf`, `.docx`, `.txt`, `.html`

**FR-02: Unstructured Parsing**

- Call the Unstructured Serverless API with `strategy="hi_res"` for PDFs, `"auto"` for all others
- Post-chunking elements are type `CompositeElement` or `Table`
- Retain metadata per element: filename, page_number, element_id

**FR-03: Chunking**

- Use `chunking_strategy="by_title"` via the API request parameters
- Max chunk size: 500 characters, no overlap
- Each chunk must carry metadata from its source elements

**FR-04: Embedding**

- Embed chunks using `text-embedding-3-small`
- Batch in groups of 100 to respect rate limits

**FR-05: Weaviate Indexing**

- Connect to local Weaviate via `weaviate.connect_to_local()`
- Use Weaviate v4 client (`weaviate-client>=4.0`)
- Create `DocumentChunk` collection if it does not exist, with no built-in vectorizer (BYOV)
- Before inserting, delete all existing chunks where `source_file` matches the filename
- Batch insert using `collection.batch.dynamic()`

### Query

**FR-06: Hybrid Search**

- Embed the query with `text-embedding-3-small`
- Run `collection.query.hybrid()` with configurable alpha (default 0.5)
- Return top 5 results with score metadata

**FR-07: Answer Generation**

- Pass retrieved chunks as context to Claude (`claude-sonnet-4-6`)
- Prompt instructs Claude to answer using only the provided context
- If context is insufficient, Claude should say so honestly

**FR-08: Streamlit UI**

- File uploader widget (multi-file)
- "Ingest" button with progress spinner
- Text input for search query
- Alpha slider: 0 = pure BM25, 1 = pure vector
- Generated answer displayed prominently above source chunks
- Source chunks as expandable cards showing: chunk text, source file, page number, element type, score

---

## 5. Data Model

### Weaviate Collection: `DocumentChunk`

| Property       | Type        | Notes                              |
| -------------- | ----------- | ---------------------------------- |
| `text`         | text        | Chunk content; BM25 indexed        |
| `source_file`  | text        | Original filename; used for dedup  |
| `page_number`  | int         | From Unstructured metadata         |
| `element_type` | text        | e.g. CompositeElement, Table       |
| vector         | float[1536] | Passed in via BYOV on insert       |

---

## 6. Tech Stack

### Dependencies (`requirements.txt`)

| Package                | Purpose                               |
| ---------------------- | ------------------------------------- |
| `anthropic>=0.40.0`    | Claude API for answer generation      |
| `unstructured-client`  | Unstructured Python SDK               |
| `weaviate-client>=4.0` | Weaviate v4 Python client             |
| `openai`               | Embeddings via text-embedding-3-small |
| `streamlit`            | UI                                    |
| `python-dotenv`        | Load env vars                         |
| `tqdm`                 | Progress during batch ops             |

### Environment Variables (`.env`)

```
UNSTRUCTURED_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

`.env` must be in `.gitignore`. Never hardcode keys.

---

## 7. File Structure

```
unstructured-weaviate/
├── app.py                    # Streamlit entry point
├── pipeline/
│   ├── __init__.py           # pipeline() orchestrator with deduplication
│   ├── ingest.py             # Unstructured API call + chunking
│   ├── embed.py              # OpenAI embedding batching
│   ├── weaviate_client.py    # Connect, create schema, batch insert, delete by source
│   ├── search.py             # Hybrid search
│   └── generate.py           # Claude answer generation
├── data/
│   └── sample_docs/          # Sample documents for demo
├── .env
├── .env.example
├── requirements.txt
└── README.md
```

---

## 8. Technical Notes

- Use the **Weaviate v4 client** throughout. Connect with `weaviate.connect_to_local()`, no auth required for local Docker.
- Local Weaviate runs on `localhost:8080` (HTTP) and `localhost:50051` (gRPC). Start it with:
  ```
  docker run -d -p 8080:8080 -p 50051:50051 --name weaviate cr.weaviate.io/semitechnologies/weaviate:latest
  ```
- No `WEAVIATE_URL` or `WEAVIATE_API_KEY` needed since the DB is local.
- Use BYOV: set `vectorizer_config=Configure.Vectorizer.none()` on the collection and pass vectors directly on insert.
- BM25 is enabled by default on text properties in Weaviate v4; no extra config needed.
- Chunking parameters are passed directly in the Unstructured API request, not as a post-processing step.
- `max_characters=500` (no overlap) produces clean, section-level chunks. Using character-based limits because the Unstructured API uses characters, not tokens.
- Deduplication uses `collection.data.delete_many(where=Filter.by_property("source_file").equal(filename))` before each ingest.
- Generation uses `claude-sonnet-4-6` with a context-grounded prompt; max 1024 output tokens.
