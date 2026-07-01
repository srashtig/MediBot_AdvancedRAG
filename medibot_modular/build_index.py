"""Script entry point for building the MediBot hybrid vector index."""

from document_processing import build_pdf_docs
from vector_store import build_vectorstore


def main():
    """Build document chunks and index them into the local Qdrant vector store."""
    pdf_docs = build_pdf_docs()
    print(f"Total documents to index: {len(pdf_docs)}")
    build_vectorstore(pdf_docs)


if __name__ == "__main__":
    main()

