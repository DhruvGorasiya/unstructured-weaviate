# PRD: Unstructured + Weaviate Demo Application

## 1. Goal

Build a Streamlit app that demonstrates an end-to-end RAG ingestion pipeline: upload documents, parse and chunk them via the Unstructured API, embed the chunks via OpenAI, index them into a local Weaviate instance, and run hybrid search queries over the indexed content.

---

## 2. Scope

**In scope:**

- Document ingestion via Unstructured Serverless API
- Chunked output stored in a local Weaviate instance (Docker, `localhost:8080`)
- Hybrid (vector + BM25) search with configurable alpha
- Streamlit frontend
- Support for `.pdf`, `.docx`, `.txt`, `.html`
- Metadata display per result: source file, page number, element type, score

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
   - Chunk using by_title strategy (max 500 tokens, 50 overlap)
         |
         v
  [Embedding Layer]
   - Batch embed chunks via OpenAI text-embedding-3-small
         |
         v
  [Local Weaviate (Docker)]
   - BYOV insertion into DocumentChunk collection
   - BM25 indexed on text property
         |
         v
  [Streamlit UI]
   - File upload, ingest trigger, hybrid search, results display
```

### Component Summary

| Component              | Technology                                   |
| ---------------------- | -------------------------------------------- |
| Document Parsing + ETL | Unstructured Serverless API                  |
| Vector Database        | Weaviate local via Docker (`localhost:8080`) |
| Embedding Model        | OpenAI `text-embedding-3-small` (1536 dims)  |
| Search Mode            | Hybrid (vector + BM25), configurable alpha   |
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

- Call the Unstructured Serverless API with `strategy="hi_res"` for PDFs
- Filter elements to: `NarrativeText`, `Title`, `Table`, `ListItem`, `FigureCaption`
- Retain metadata per element: filename, page_number, element_id

**FR-03: Chunking**

- Use `chunking_strategy="by_title"` via the API request parameters
- Max chunk size: 500 tokens, overlap: 50 tokens
- Each chunk must carry metadata from its source elements

**FR-04: Embedding**

- Embed chunks using `text-embedding-3-small`
- Batch in groups of 100 to respect rate limits

**FR-05: Weaviate Indexing**

- Connect to local Weaviate via `weaviate.connect_to_local()`
- Use Weaviate v4 client (`weaviate-client>=4.0`)
- Create `DocumentChunk` collection if it does not exist, with no built-in vectorizer (BYOV)
- Enable BM25 on the `text` property
- Batch insert using `collection.batch.dynamic()`

### Query

**FR-06: Hybrid Search**

- Embed the query with `text-embedding-3-small`
- Run `collection.query.hybrid()` with configurable alpha (default 0.5)
- Return top 5 results with score metadata

**FR-07: Streamlit UI**

- File uploader widget (multi-file)
- "Ingest" button with progress spinner
- Text input for search query
- Alpha slider: 0 = pure BM25, 1 = pure vector
- Results as expandable cards showing: chunk text, source file, page number, element type, score

---

## 5. Data Model

### Weaviate Collection: `DocumentChunk`

| Property       | Type        | Notes                            |
| -------------- | ----------- | -------------------------------- |
| `text`         | text        | Chunk content; BM25 indexed      |
| `source_file`  | text        | Original filename                |
| `page_number`  | int         | From Unstructured metadata       |
| `element_type` | text        | e.g. NarrativeText, Table, Title |
| vector         | float[1536] | Passed in via BYOV on insert     |

---

## 6. Tech Stack

### Dependencies (`requirements.txt`)

| Package                | Purpose                               |
| ---------------------- | ------------------------------------- |
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
```

`.env` must be in `.gitignore`. Never hardcode keys.

---

## 7. File Structure

```
unstructured-weaviate-demo/
├── app.py                    # Streamlit entry point
├── pipeline/
│   ├── __init__.py
│   ├── ingest.py             # Unstructured API call + chunking
│   ├── embed.py              # OpenAI embedding batching
│   ├── weaviate_client.py    # Connect, create schema, batch insert
│   └── search.py             # Hybrid search
├── data/
│   └── sample_docs/          # Sample documents for demo
├── .env
├── .env.example
├── requirements.txt
└── README.md
```

---

## 8. Implementation Order

1. Set up project structure, virtual environment, `requirements.txt`, `.env`
2. `weaviate_client.py`: connect via `connect_to_local()`, create `DocumentChunk` schema, batch insert helper
3. `ingest.py`: call Unstructured API, apply element type filter, return chunks with metadata
4. `embed.py`: batch embed chunks, expose `embed_texts(list[str])` and `embed_text(str)`
5. Wire ingest + embed + insert into a single `pipeline(file_path)` function
6. `search.py`: embed query, run `collection.query.hybrid()`, return results
7. `app.py`: Streamlit UI wiring all pipeline functions together
8. Place 2-3 sample documents in `data/sample_docs/` (one multi-column PDF, one DOCX with tables, one plain text)
9. End-to-end test: ingest all samples, run 4-5 queries, verify results are relevant
10. `README.md`: setup steps (including `docker run` command for local Weaviate), how to run the app

---

## 9. Technical Notes

- Use the **Weaviate v4 client** throughout. The v3 API is deprecated. Connect with `weaviate.connect_to_local()`, no auth required for local Docker.
- Local Weaviate runs on `localhost:8080` (HTTP) and `localhost:50051` (gRPC). Start it with:
  ```
  docker run -d -p 8080:8080 -p 50051:50051 --name weaviate cr.weaviate.io/semitechnologies/weaviate:latest
  ```
- No `WEAVIATE_URL` or `WEAVIATE_API_KEY` needed since the DB is local.
- Use BYOV (bring-your-own-vector): set `vectorizer_config=Configure.Vectorizer.none()` on the collection and pass vectors directly on insert.
- BM25 is enabled by default on text properties in Weaviate v4; no extra config needed.
- `chunk_by_title` parameters are passed directly in the Unstructured API request, not as a post-processing step.
