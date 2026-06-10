from openai import OpenAI
from tqdm import tqdm

MODEL = "text-embedding-3-small"


def embed_texts(texts: list[str], api_key: str, batch_size: int = 100) -> list[list[float]]:
    client = OpenAI(api_key=api_key)
    all_vectors = []
    for i in tqdm(range(0, len(texts), batch_size), desc="Embedding"):
        batch = texts[i : i + batch_size]
        response = client.embeddings.create(input=batch, model=MODEL)
        batch_vecs = [e.embedding for e in sorted(response.data, key=lambda e: e.index)]
        all_vectors.extend(batch_vecs)
    return all_vectors


def embed_text(text: str, api_key: str) -> list[float]:
    return embed_texts([text], api_key)[0]
