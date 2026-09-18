from __future__ import annotations

import chromadb

from backend.retrieval.embedder import embed_text


def get_collection(collection_name: str = "code_chunks"):
    client = chromadb.PersistentClient(path="./chroma_db")
    return client.get_or_create_collection(name=collection_name)


def add_chunks(chunks: list[dict], collection_name: str = "code_chunks") -> None:
    collection = get_collection(collection_name)

    for chunk in chunks:
        if not chunk.get("source"):
            continue

        embedding = embed_text(chunk["source"])
        chunk_id = f"{chunk['file_path']}::{chunk['qualified_name']}"
        metadata = {
            "file_path": chunk["file_path"],
            "qualified_name": chunk["qualified_name"],
            "symbol_type": chunk["symbol_type"],
            "start_line": int(chunk["start_line"]),
            "end_line": int(chunk["end_line"]),
        }

        collection.add(
            ids=[chunk_id],
            embeddings=[embedding],
            documents=[chunk["source"]],
            metadatas=[metadata],
        )


def query_similar(issue_text: str, k: int = 5, collection_name: str = "code_chunks") -> list[dict]:
    collection = get_collection(collection_name)
    query_embedding = embed_text(issue_text)
    results = collection.query(query_embeddings=[query_embedding], n_results=k)

    ids = results["ids"][0]
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    return [
        {
            "id": ids[index],
            "document": documents[index],
            "metadata": metadatas[index],
            "distance": distances[index],
        }
        for index in range(len(ids))
    ]
