import os
from typing import List
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone

load_dotenv()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

pinecone_client = Pinecone(
    api_key=os.getenv("PINECONE_API_KEY")
)

INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

if not INDEX_NAME:
    raise ValueError("PINECONE_INDEX_NAME is missing in .env")

index = pinecone_client.Index(INDEX_NAME)


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


def create_embedding(text: str) -> List[float]:
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )

    return response.data[0].embedding


def upsert_company_text(
    company_id: str,
    website: str,
    text: str
) -> int:
    chunks = chunk_text(text)

    vectors = []

    for i, chunk in enumerate(chunks):
        embedding = create_embedding(chunk)

        vectors.append({
            "id": f"{company_id}-{i}",
            "values": embedding,
            "metadata": {
                "company_id": company_id,
                "website": website,
                "chunk_index": i,
                "text": chunk
            }
        })

    if vectors:
        index.upsert(vectors=vectors)

    return len(vectors)


def search_company_context(
    company_id: str,
    question: str,
    top_k: int = 5
) -> List[str]:
    question_embedding = create_embedding(question)

    results = index.query(
        vector=question_embedding,
        top_k=top_k,
        include_metadata=True,
        filter={
            "company_id": {"$eq": company_id}
        }
    )

    contexts = []

    for match in results.get("matches", []):
        metadata = match.get("metadata", {})
        text = metadata.get("text")

        if text:
            contexts.append(text)

    return contexts