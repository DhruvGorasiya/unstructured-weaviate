# Unstructured + Weaviate RAG Demo

A Streamlit app that demonstrates an end-to-end RAG ingestion pipeline: upload documents,
parse and chunk them via the Unstructured API, embed via OpenAI, index into a local
Weaviate instance, and run hybrid search queries over the indexed content.

## Prerequisites

- Python 3.10+
- Docker

## 1. Start Local Weaviate

```bash
docker run -d -p 8080:8080 -p 50051:50051 --name weaviate \
  cr.weaviate.io/semitechnologies/weaviate:latest
```

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

## 3. Configure API Keys

```bash
cp .env.example .env
```

Edit `.env` and fill in your keys:

```
UNSTRUCTURED_API_KEY=your_unstructured_key
OPENAI_API_KEY=your_openai_key
```

Get your Unstructured API key at [unstructured.io](https://unstructured.io).

## 4. Run the App

```bash
streamlit run app.py
```

## Usage

1. **Ingest**: Use the sidebar to upload one or more `.pdf`, `.docx`, `.txt`, or `.html`
   files, then click **Ingest**. Each file is parsed and chunked via the Unstructured
   API, embedded via OpenAI `text-embedding-3-small`, and indexed into Weaviate.

2. **Search**: Enter a query in the main area. Adjust the **Alpha** slider to control
   the hybrid search balance (0 = pure BM25 keyword, 1 = pure vector semantic).
   Results appear as expandable cards showing the chunk text, source file, page number,
   element type, and relevance score.

## Sample Documents

Two sample `.txt` documents are included in `data/sample_docs/` for quick testing:

- `sample_readme.txt` — overview of machine learning concepts
- `sample_guide.txt` — guide to vector databases and RAG

## Architecture

```
Raw Documents (PDF / DOCX / TXT / HTML)
         |
         v
  [Unstructured Serverless API]
   - Partition into typed elements
   - Chunk using by_title strategy (max 2000 chars, 200 overlap)
         |
         v
  [OpenAI text-embedding-3-small]
   - Batch embed chunks (groups of 100)
         |
         v
  [Local Weaviate (Docker)]
   - BYOV insertion into DocumentChunk collection
   - BM25 + HNSW indexed
         |
         v
  [Streamlit UI]
   - File upload, ingest trigger, hybrid search, results display
```
