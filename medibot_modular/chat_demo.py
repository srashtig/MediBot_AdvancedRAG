"""Small script entry point for asking MediBot a question from the terminal."""

import argparse

from llm import get_llm
from router import get_answer
from vector_store import load_vectorstore


def parse_args():
    """Parse command-line arguments for the chat demo."""
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    parser.add_argument("--role", default="admin")
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--rerank", action="store_true")
    parser.add_argument("--show-reranking-scores", action="store_true")
    parser.add_argument("--debug-sql", action="store_true")
    return parser.parse_args()


def main():
    """Load the LLM and vector store, then answer one command-line question."""
    args = parse_args()
    llm = get_llm()
    vectorstore = load_vectorstore()
    get_answer(
        args.question,
        vectorstore=vectorstore,
        llm=llm,
        role=args.role,
        k=args.k,
        rerank=args.rerank,
        show_reranking_scores=args.show_reranking_scores,
        debug_sql=args.debug_sql,
    )


if __name__ == "__main__":
    main()
