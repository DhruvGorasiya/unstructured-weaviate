import os

from dotenv import load_dotenv
from weaviate.classes.query import MetadataQuery

from .embed import embed_text
from .weaviate_client import get_client, get_collection

load_dotenv()


def search_chunks(query: str, alpha: float = 0.5, limit: int = 5) -> list[dict]:
    openai_key = os.environ["OPENAI_API_KEY"]
    query_vector = embed_text(query, openai_key)

    client = get_client()
    try:
        collection = get_collection(client)
        response = collection.query.hybrid(
            query=query,
            vector=query_vector,
            alpha=alpha,
            limit=limit,
            return_metadata=MetadataQuery(score=True),
        )
    finally:
        client.close()

    results = []
    for obj in response.objects:
        results.append(
            {
                "text": obj.properties.get("text", ""),
                "source_file": obj.properties.get("source_file", ""),
                "page_number": obj.properties.get("page_number", 0),
                "element_type": obj.properties.get("element_type", ""),
                "score": obj.metadata.score if obj.metadata else None,
            }
        )
    return results
