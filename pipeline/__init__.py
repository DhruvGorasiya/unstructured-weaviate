import os

from dotenv import load_dotenv

from .embed import embed_texts
from .ingest import parse_file
from .weaviate_client import batch_insert, get_client, get_collection

load_dotenv()


def pipeline(file_bytes: bytes, filename: str) -> int:
    unstructured_key = os.environ["UNSTRUCTURED_API_KEY"]
    openai_key = os.environ["OPENAI_API_KEY"]

    chunks = parse_file(file_bytes, filename, unstructured_key)
    if not chunks:
        return 0

    texts = [c["text"] for c in chunks]
    vectors = embed_texts(texts, openai_key)

    for chunk, vector in zip(chunks, vectors):
        chunk["vector"] = vector

    client = get_client()
    try:
        collection = get_collection(client)
        inserted = batch_insert(collection, chunks)
    finally:
        client.close()

    return inserted
