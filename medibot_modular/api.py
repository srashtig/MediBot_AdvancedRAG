"""FastAPI backend for the MediBot assignment."""

from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from config import ACCESS_ROLES, ALL_ROLES
from hybrid_rag import ask_hybrid_reranked
from llm import get_llm
from router import is_analytical_question
from sql_rag import ask_sql
from vector_store import load_vectorstore


app = FastAPI(title="MediBot API")
bearer_scheme = HTTPBearer()


DEMO_USERS = {
    "dr.mehta": {"password": "doctor123", "role": "doctor"},
    "nurse.priya": {"password": "nurse123", "role": "nurse"},
    "billing.ravi": {"password": "billing123", "role": "billing_executive"},
    "tech.anand": {"password": "tech123", "role": "technician"},
    "admin.sys": {"password": "admin123", "role": "admin"},
}

SESSIONS = {}
_llm = None
_vectorstore = None


class LoginRequest(BaseModel):
    """Request body for user login."""

    username: str
    password: str


class LoginResponse(BaseModel):
    """Response body returned after successful login."""

    token: str
    username: str
    role: str


class ChatRequest(BaseModel):
    """Request body for a MediBot chat question."""

    question: str
    role: str | None = None
    k: int = 3


class Source(BaseModel):
    """Source citation returned for a retrieved document chunk."""

    source_document: str
    section_title: str | list | None
    collection: str


class ChatResponse(BaseModel):
    """Response body returned by the chat endpoint."""

    answer: str
    sources: list[Source]
    retrieval_type: str
    role: str


def get_runtime():
    """Lazily load the LLM and vector store used by chat requests."""
    global _llm, _vectorstore

    if _llm is None:
        _llm = get_llm()
    if _vectorstore is None:
        _vectorstore = load_vectorstore()
    return _llm, _vectorstore


def get_accessible_collections(role: str):
    """Return the document collections accessible to a role."""
    if role not in ALL_ROLES:
        raise HTTPException(status_code=400, detail=f"Unknown role: {role}")

    return [
        collection
        for collection, roles in ACCESS_ROLES.items()
        if role in roles
    ]


def get_current_session(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    """Resolve the bearer token from the Authorization header."""
    if credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Missing bearer token, enter token to authorize at top right corner.")

    token = credentials.credentials.strip()
    session = SESSIONS.get(token)
    if session is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return session


def format_sources(docs):
    """Convert LangChain documents into API source citation objects."""
    sources = []
    for doc in docs:
        sources.append(
            Source(
                source_document=doc.metadata.get("source_document", "unknown"),
                section_title=doc.metadata.get("section_title"),
                collection=doc.metadata.get("collection", "unknown"),
            )
        )
    return sources


@app.get("/")
def root():
    """Return available API routes for quick browser checks."""
    return {
        "message": "MediBot API is running",
        "docs": "/docs",
        "health": "/health",
        "login": "POST /login",
        "chat": "POST /chat",
        "collections": "GET /collections/{role}",
    }


@app.get("/health")
def health():
    """Return a simple health check response."""
    return {"status": "ok"}


@app.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    """Accept username and password, then return a role-tagged session token."""
    user = DEMO_USERS.get(payload.username)
    if user is None or user["password"] != payload.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = uuid4().hex
    SESSIONS[token] = {
        "username": payload.username,
        "role": user["role"],
    }
    return LoginResponse(token=token, username=payload.username, role=user["role"])


@app.get("/collections/{role}")
def collections(role: str):
    """Return the list of document collections accessible to a role."""
    return {
        "role": role,
        "collections": get_accessible_collections(role),
    }


@app.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, session=Depends(get_current_session)):
    """Route a question to SQL RAG or Hybrid+Rerank RAG with role-based access."""
    llm, vectorstore = get_runtime()
    role = payload.role or session["role"]

    if role != session["role"]:
        raise HTTPException(
            status_code=403,
            detail="Requested role does not match the logged-in session role.",
        )

    if role not in ALL_ROLES:
        raise HTTPException(status_code=400, detail=f"Unknown role: {role}")

    if is_analytical_question(payload.question, llm=llm):
        if role not in ["admin", "billing_executive"]:
            answer = (
                f"As a {role}, you do not have access to analytical billing or "
                "maintenance data. Please use an admin or billing_executive role."
            )
        else:
            answer = ask_sql(payload.question, llm=llm, role=role)
        return ChatResponse(
            answer=answer or "I could not generate an answer.",
            sources="Databases: claims, maintenance_tickets",
            retrieval_type="sql_rag",
            role=role,
        )

    result = ask_hybrid_reranked(
        payload.question,
        vectorstore=vectorstore,
        llm=llm,
        role=role,
        n=payload.k,
        show_reranking_scores=False,
    )
    return ChatResponse(
        answer=result["answer"],
        sources=format_sources(result["context"]),
        retrieval_type="hybrid_rag",
        role=role,
    )
