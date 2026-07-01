"""SQL RAG helpers for analytical questions over MediAssist data."""

import re

from langchain_classic.chains import create_sql_query_chain
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate

from config import DB_PATH


SYSTEM_PROMPT = """You are a Medical Hospital support analytics assistant.
Given a user question and the SQL query result from our tickets database,
provide a clear, concise natural language answer.
Be specific with numbers and facts from the data."""


def get_database(db_path=DB_PATH):
    """Create a LangChain SQLDatabase connection for the MediAssist SQLite DB."""
    return SQLDatabase.from_uri(f"sqlite:///{db_path}")


def clean_sql(raw: str) -> str:
    """Strip markdown fences and any preamble, leaving only the SQL statement."""
    raw = re.sub(r"```(?:sql)?", "", raw).strip("`").strip()
    if "SQLQuery:" in raw:
        raw = raw.split("SQLQuery:")[-1].strip()
    return raw


def sql_rag_chain(question: str, llm, db=None, debug: bool = False) -> str:
    """Generate SQL, execute it, and summarize the result as a natural answer."""
    if db is None:
        db = get_database()

    sql_query_chain = create_sql_query_chain(llm, db)
    raw_sql = sql_query_chain.invoke({"question": question})
    sql = clean_sql(raw_sql)
    if debug:
        print(f"[debug] cleaned SQL -> {sql}")

    result = db.run(sql)

    answer_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", "Question: {question}\nSQL Result: {result}\n\nAnswer:"),
        ]
    )
    response = answer_prompt | llm
    return response.invoke({"question": question, "result": result}).content


def ask_sql(question: str, llm, role: str = "admin", debug: bool = False):
    """Answer an analytical question when the role is allowed to use SQL RAG."""
    if role not in ["admin", "billing_executive"]:
        print(f"Role '{role}' does not have access to billing data. Please use a different role.")
        return None

    answer = sql_rag_chain(question, llm=llm, debug=debug)
    print(f"Answer:   {answer}")
    print("-" * 60)
    return answer

