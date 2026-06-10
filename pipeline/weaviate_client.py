import weaviate
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.query import Filter

COLLECTION_NAME = "DocumentChunk"


def get_client() -> weaviate.WeaviateClient:
    return weaviate.connect_to_local()


def get_collection(client: weaviate.WeaviateClient):
    if not client.collections.exists(COLLECTION_NAME):
        client.collections.create(
            name=COLLECTION_NAME,
            vectorizer_config=Configure.Vectorizer.none(),
            properties=[
                Property(name="text", data_type=DataType.TEXT),
                Property(name="source_file", data_type=DataType.TEXT),
                Property(name="page_number", data_type=DataType.INT),
                Property(name="element_type", data_type=DataType.TEXT),
            ],
        )
    return client.collections.get(COLLECTION_NAME)


def delete_by_source(collection, source_file: str) -> None:
    collection.data.delete_many(
        where=Filter.by_property("source_file").equal(source_file)
    )


def batch_insert(collection, chunks: list[dict]) -> int:
    inserted = 0
    with collection.batch.dynamic() as batch:
        for chunk in chunks:
            batch.add_object(
                properties={
                    "text": chunk["text"],
                    "source_file": chunk["source_file"],
                    "page_number": chunk["page_number"],
                    "element_type": chunk["element_type"],
                },
                vector=chunk["vector"],
            )
            inserted += 1
    return inserted
