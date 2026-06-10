import os

import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-sonnet-4-6"


def generate_answer(query: str, chunks: list[dict]) -> str:
    context = "\n\n---\n\n".join(
        f"Source: {c['source_file']} | Page: {c['page_number']}\n{c['text']}"
        for c in chunks
    )

    prompt = f"""You are a helpful assistant. Answer the user's question using only the context provided below.
If the context doesn't contain enough information to answer, say so honestly.

<context>
{context}
</context>

Question: {query}"""

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text
