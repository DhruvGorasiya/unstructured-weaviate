from unstructured_client import UnstructuredClient

ALLOWED_TYPES = {"CompositeElement", "Table"}


def parse_file(file_bytes: bytes, filename: str, api_key: str) -> list[dict]:
    client = UnstructuredClient(api_key_auth=api_key)
    strategy = "hi_res" if filename.lower().endswith(".pdf") else "auto"

    with client:
        res = client.general.partition(
            request={
                "partition_parameters": {
                    "files": {
                        "content": file_bytes,
                        "file_name": filename,
                    },
                    "strategy": strategy,
                    "chunking_strategy": "by_title",
                    "max_characters": 500,
                    "overlap": 0,
                    "include_orig_elements": False,
                }
            }
        )

    chunks = []
    for el in res.elements or []:
        if el.get("type") not in ALLOWED_TYPES:
            continue
        text = el.get("text", "").strip()
        if not text:
            continue
        meta = el.get("metadata", {})
        chunks.append(
            {
                "text": text,
                "source_file": meta.get("filename", filename),
                "page_number": meta.get("page_number") or 0,
                "element_type": el.get("type", "Unknown"),
                "element_id": el.get("element_id", ""),
            }
        )
    return chunks
