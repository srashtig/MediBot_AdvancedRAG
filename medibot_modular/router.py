"""Question router that chooses SQL RAG or document RAG."""

from langchain_core.prompts import ChatPromptTemplate

from hybrid_rag import ask_hybrid, ask_hybrid_reranked
from sql_rag import ask_sql


def is_analytical_question(question: str, llm) -> bool:
    """Classify whether a question should be routed to SQL RAG."""
    system_prompt = (
        "Tell if the following question is strictly analytical/numbers-based and is "
        "related to claims or maintenance tickets or or not. If it is, answer with "
        "'analytical', else answer with 'non-analytical'."
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{question}"),
        ]
    )

    analytical = llm.invoke(prompt.format(question=question))
    return analytical.content.strip().lower() == "analytical"


def get_answer(
    question: str,
    vectorstore,
    llm,
    role: str = "admin",
    k: int = 3,
    rerank: bool = False,
    show_reranking_scores=True,
    debug_sql: bool = False,
):
    """Route a user question to SQL RAG or hybrid document RAG and return its answer."""
    print(f"Question: {question}")
    if is_analytical_question(question=question, llm=llm):
        print("Using SQL RAG chain for analytical question...")
        answer = ask_sql(question, llm=llm, role=role, debug=debug_sql)
        return answer

    print("Using Hybrid RAG chain for non-analytical question...")
    if rerank:
        answer = ask_hybrid_reranked(
            question,
            vectorstore=vectorstore,
            llm=llm,
            role=role,
            n=k,
            show_reranking_scores=show_reranking_scores,
        )
    else:
        answer = ask_hybrid(question, vectorstore=vectorstore, llm=llm, role=role, k=k)
        return answer

