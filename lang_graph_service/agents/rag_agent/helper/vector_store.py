import os
from pathlib import Path
from urllib.parse import urlparse

import chromadb
import httpx
from dotenv import load_dotenv

load_dotenv()

CHROMA_PATH = Path(__file__).parents[1] / "chroma_db"
COLLECTION = "protocol"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")


def ollama_host() -> str:
    url = urlparse(os.getenv("BASE_URL"))
    return f"{url.scheme}://{url.netloc}"


def embed(texts: list[str], prefix: str) -> list[list[float]]:
    response = httpx.post(
        f"{ollama_host()}/api/embed",
        json={"model": EMBEDDING_MODEL, "input": [prefix + text for text in texts]},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["embeddings"]


def embed_documents(texts: list[str]) -> list[list[float]]:
    return embed(texts, "search_document: ")


def embed_query(text: str) -> list[float]:
    return embed([text], "search_query: ")[0]


def get_client() -> chromadb.ClientAPI:
    return chromadb.PersistentClient(path=str(CHROMA_PATH))


def get_collection():
    return get_client().get_collection(COLLECTION)
