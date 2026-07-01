"""Embedding model setup for dense and sparse hybrid retrieval."""

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import FastEmbedSparse

from config import EMBED_MODEL, SPARSE_MODEL


def get_dense_embeddings():
    """Create the dense embedding model used for semantic retrieval."""
    return HuggingFaceEmbeddings(
        model_name=EMBED_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def get_sparse_embeddings():
    """Create the sparse embedding model used for BM25 keyword retrieval."""
    return FastEmbedSparse(model_name=SPARSE_MODEL, batch_size=32)


def get_embeddings():
    """Return the dense and sparse embedding models used by the vector store."""
    dense_embeddings = get_dense_embeddings()
    sparse_embeddings = get_sparse_embeddings()
    print("Dense embedding model:", EMBED_MODEL)
    print("Sparse embedding model: Qdrant/BM25")
    return dense_embeddings, sparse_embeddings

