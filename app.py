import streamlit as st
from dotenv import load_dotenv
from weaviate.exceptions import WeaviateConnectionError

from pipeline import pipeline
from pipeline.search import search_chunks

load_dotenv()

st.set_page_config(page_title="Unstructured + Weaviate RAG Demo", layout="wide")
st.title("Unstructured + Weaviate RAG Demo")

# --- Sidebar: Ingest ---
with st.sidebar:
    st.header("Ingest Documents")
    uploaded_files = st.file_uploader(
        "Upload documents",
        type=["pdf", "docx", "txt", "html"],
        accept_multiple_files=True,
    )
    if st.button("Ingest", disabled=not uploaded_files):
        for uf in uploaded_files:
            with st.spinner(f"Ingesting {uf.name}..."):
                try:
                    n = pipeline(uf.getvalue(), uf.name)
                    st.success(f"{uf.name}: {n} chunks indexed")
                except WeaviateConnectionError:
                    st.error("Cannot connect to Weaviate. Is Docker running?")
                except Exception as e:
                    st.error(f"{uf.name}: {e}")

# --- Main: Search ---
st.header("Search")
query = st.text_input("Enter search query", placeholder="What is...")
alpha = st.slider("Alpha (0 = BM25 only, 1 = vector only)", 0.0, 1.0, 0.5, step=0.05)

if query:
    try:
        results = search_chunks(query, alpha=alpha)
    except WeaviateConnectionError:
        st.error("Cannot connect to Weaviate. Is Docker running?")
        results = []

    if not results:
        st.info("No results found.")
    else:
        for r in results:
            score_str = f"{r['score']:.4f}" if r["score"] is not None else "n/a"
            label = f"{r['source_file']} | p.{r['page_number']} | {r['element_type']} | score: {score_str}"
            with st.expander(label):
                st.write(r["text"])
