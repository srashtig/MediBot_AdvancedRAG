"""Qdrant vector store creation and loading helpers."""

import json
from pathlib import Path

from langchain_qdrant import QdrantVectorStore, RetrievalMode
from qdrant_client import QdrantClient

from config import QDRANT_COLLECTION, VECTORSTORE_PATH
from embeddings import get_embeddings


def build_vectorstore(
    documents,
    path=VECTORSTORE_PATH,
    collection_name=QDRANT_COLLECTION,
):
    """Index documents into a local Qdrant vector store in hybrid retrieval mode."""
    dense_embeddings, sparse_embeddings = get_embeddings()
    vectorstore = QdrantVectorStore.from_documents(
        documents=documents,
        embedding=dense_embeddings,
        sparse_embedding=sparse_embeddings,
        path=str(path),
        collection_name=collection_name,
        retrieval_mode=RetrievalMode.HYBRID,
    )

    print(f"Indexed {len(documents)} documents into Qdrant collection '{collection_name}'")
    print("Both dense (semantic) and sparse (BM25) vectors stored.")
    return vectorstore


def collection_exists(path=VECTORSTORE_PATH, collection_name=QDRANT_COLLECTION):
    """Return whether the named Qdrant collection exists in the local store."""
    path = Path(path)
    meta_path = path / "meta.json"
    collection_storage = path / "collection" / collection_name / "storage.sqlite"

    if meta_path.exists():
        with meta_path.open() as file:
            metadata = json.load(file)
        collections = metadata.get("collections", {})
        if collection_name in collections:
            return collection_storage.exists()

    if collection_storage.exists():
        return True

    client = QdrantClient(path=str(path))
    try:
        return client.collection_exists(collection_name)
    finally:
        client.close()


def load_vectorstore(
    path=VECTORSTORE_PATH,
    collection_name=QDRANT_COLLECTION,
    build_if_missing: bool = True,
):
    """Load a local Qdrant vector store, building it first when missing."""
    if not collection_exists(path=path, collection_name=collection_name):
        if not build_if_missing:
            raise ValueError(f"Qdrant collection '{collection_name}' was not found at {path}")

        print(f"Qdrant collection '{collection_name}' not found. Building index now...")
        from document_processing import build_pdf_docs

        documents = build_pdf_docs()
        return build_vectorstore(
            documents=documents,
            path=path,
            collection_name=collection_name,
        )

    dense_embeddings, sparse_embeddings = get_embeddings()
    return QdrantVectorStore.from_existing_collection(
        embedding=dense_embeddings,
        sparse_embedding=sparse_embeddings,
        path=str(path),
        collection_name=collection_name,
        retrieval_mode=RetrievalMode.HYBRID,
    )
