"""Hybrid RAG retrieval, answering, and cross-encoder reranking."""

from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_core.prompts import ChatPromptTemplate
from qdrant_client.models import FieldCondition, Filter, MatchValue

from config import RERANKER_MODEL


SYSTEM_PROMPT = """You are a helpful TelecomCo customer support assistant.
Answer the customer's question using ONLY the information provided in the context below.
If the answer is not in the context, say "I don't have that information."
Keep answers concise and friendly.

Context:
{context}"""


def filtered_retriever(vectorstore, role: str, k: int = 3):
    """Create a hybrid retriever filtered to chunks accessible by a role."""
    filter = Filter(
        must=[
            FieldCondition(
                key="metadata.access_roles",
                match=MatchValue(value=role),
            )
        ]
    )

    hybrid_retriever = vectorstore.as_retriever(
        search_kwargs={"filter": filter, "k": k}
    )
    return hybrid_retriever


def ask_hybrid(question: str, vectorstore, llm, role: str = "admin", k: int = 3):
    """Answer a question with role-filtered hybrid retrieval and an LLM."""
    hybrid_retriever = filtered_retriever(vectorstore=vectorstore, role=role, k=k)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", "{input}"),
        ]
    )

    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    hybrid_rag_chain = create_retrieval_chain(hybrid_retriever, question_answer_chain)
    result = hybrid_rag_chain.invoke({"input": question})
    #print(f"Question: {question}")
    print(f"\nAnswer: {result['answer']}")
    print("\nSources retrieved:")
    for i, doc in enumerate(result["context"], 1):
        src = doc.metadata.get("collection", "unknown")
        cat = doc.metadata.get("source_document", "unknown")
        print(f"  [{i}] collection = {src},  file = {cat}")
        print(f"Document Content:\n{doc.page_content}")
    print("-" * 60)
    return result


def get_cross_encoder(model_name=RERANKER_MODEL):
    """Load the cross-encoder model used to rerank hybrid retrieval candidates."""
    return HuggingFaceCrossEncoder(model_name=model_name)


def ask_hybrid_reranked(
    question: str,
    vectorstore,
    llm,
    role: str = "admin",
    n: int = 3,
    show_reranking_scores: bool = True,
    cross_encoder=None,
):
    """Answer a question with hybrid retrieval followed by cross-encoder reranking."""
    if cross_encoder is None:
        cross_encoder = get_cross_encoder()

    reranker = CrossEncoderReranker(
        model=cross_encoder,
        top_n=n,
    )

    broad_retriever = filtered_retriever(vectorstore=vectorstore, role=role, k=10)

    reranking_retriever = ContextualCompressionRetriever(
        base_compressor=reranker,
        base_retriever=broad_retriever,
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", "{input}"),
        ]
    )

    reranking_rag_chain = create_retrieval_chain(
        reranking_retriever,
        create_stuff_documents_chain(llm, prompt),
    )
    result = reranking_rag_chain.invoke({"input": question})
    print(f"Question: {question}")
    print(f"\nAnswer: {result['answer']}")
    print("\nSources retrieved:")
    for i, doc in enumerate(result["context"], 1):
        src = doc.metadata.get("collection", "unknown")
        cat = doc.metadata.get("source_document", "unknown")
        print(f"  [{i}] collection = {src},  file = {cat}")
        print(f"Document Content:\n{doc.page_content}")
    print("-" * 60)

    if show_reranking_scores:
        print("\nReranking scores:")
        print("-----------------")
        query = question
        candidates = broad_retriever.invoke(query)
        print(f"Retrieved {len(candidates)} candidates. Now scoring each with cross-encoder...\n")

        pairs = [[query, doc.page_content] for doc in candidates]
        scores = cross_encoder.score(pairs)

        scored = sorted(zip(scores, candidates), reverse=True)

        for rank, (score, doc) in enumerate(scored, 1):
            cat = doc.metadata.get("category", "")
            print(f"Rank {rank}  score={score:.4f}  category={cat}")
            print(f"  {doc.page_content[:200]}...")
            print()

    return result

