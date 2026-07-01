"""Document loading, Docling parsing, and chunk preparation helpers."""

import os
from pathlib import Path

from docling.chunking import HybridChunker
from docling.document_converter import DocumentConverter
from langchain_core.documents import Document
from transformers import AutoTokenizer

from config import ACCESS_ROLES, COLLECTION_DIRS, DIR, EMBED_MODEL


tokenizer = AutoTokenizer.from_pretrained(EMBED_MODEL)
chunker = HybridChunker(
    tokenizer=tokenizer,
    max_tokens=128,
    merge_peers=True,
)


def load_documents_from_directory(directory_path):
    """Return all file paths found under a directory tree."""
    documents = []
    for root, _, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            documents.append(file_path)
    return documents


def get_collection_docs(base_dir=DIR, collection_dirs=COLLECTION_DIRS):
    """Build a mapping of collection name to document paths."""
    return {
        collection: load_documents_from_directory(str(Path(base_dir) / collection))
        for collection in collection_dirs
    }


def load_document(source: str):
    """Parse a source document with Docling and return its Docling document."""
    converter = DocumentConverter()
    result = converter.convert(source)
    return result.document


def chunk_doc(
    source: str,
    chunker: HybridChunker = HybridChunker(
        tokenizer=tokenizer,
        max_tokens=128,
        merge_peers=True,
    ),
):
    """Load a document and chunk it into smaller pieces for embedding."""
    doc = load_document(source)
    doc_chunks = chunker.chunk(dl_doc=doc)
    return doc_chunks


def get_metadata_chunk(chunk):
    """Extract the chunk label and heading metadata from a Docling chunk."""
    label = chunk.meta.dict()["doc_items"][0]["label"]
    headings = chunk.meta.dict()["headings"]
    return label, headings


def build_pdf_docs(
    collection_docs=None,
    collection_dirs=COLLECTION_DIRS,
    access_roles=ACCESS_ROLES,
    chunker=chunker,
):
    """Convert collection documents into LangChain documents with RBAC metadata."""
    if collection_docs is None:
        collection_docs = get_collection_docs()

    pdf_docs = []
    for collection_dir in collection_dirs:
        accesible = access_roles[collection_dir]
        for doc_path in collection_docs[collection_dir]:
            chunk_iter = chunk_doc(doc_path, chunker)
            for chunk in chunk_iter:
                label, headings = get_metadata_chunk(chunk)
                pdf_docs.append(
                    Document(
                        page_content=chunker.serialize(chunk=chunk),
                        metadata={
                            "source_document": doc_path,
                            "collection": collection_dir,
                            "chunk_type": label,
                            "section_title": headings,
                            "access_roles": accesible,
                        },
                    )
                )

            print(f"Created {len(pdf_docs)} chunks for {doc_path}")
            print("\nSample chunk (note the heading prepended by serialize()):")
            print(pdf_docs[0].page_content[:300])
    return pdf_docs

