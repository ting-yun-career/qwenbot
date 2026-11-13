import re
from pathlib import Path

from agents.rag_agent.helper.vector_store import COLLECTION, embed_documents, get_client

SOURCE = Path(__file__).parent / "protocol.txt"
MAX_CHARS = 1500
HEADING = re.compile(r"^\((\d+)\) ([A-Z].*)$")


def read_sections(text: str) -> list[dict]:
    sections = []
    for paragraph in text.split("\n\n"):
        paragraph = paragraph.strip()
        match = HEADING.match(paragraph)
        if match:
            sections.append(
                {"number": int(match[1]), "title": match[2], "paragraphs": []}
            )
        elif paragraph:
            sections[-1]["paragraphs"].append(paragraph)
    return sections


def split_section(section: dict) -> list[str]:
    chunks, current = [], ""
    for paragraph in section["paragraphs"]:
        if current and len(current) + len(paragraph) > MAX_CHARS:
            chunks.append(current)
            current = ""
        current = f"{current}\n\n{paragraph}" if current else paragraph
    if current:
        chunks.append(current)
    return chunks


def build_chunks(text: str) -> list[dict]:
    chunks = []
    for section in read_sections(text):
        heading = f"({section['number']}) {section['title']}"
        for index, body in enumerate(split_section(section)):
            chunks.append(
                {
                    "id": f"s{section['number']}-{index}",
                    "document": f"{heading}\n{body}",
                    "metadata": {
                        "section": section["number"],
                        "title": section["title"],
                        "chunk": index,
                    },
                }
            )
    return chunks


def main() -> None:
    chunks = build_chunks(SOURCE.read_text())
    client = get_client()
    if COLLECTION in [c.name for c in client.list_collections()]:
        client.delete_collection(COLLECTION)
    collection = client.create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})
    documents = [chunk["document"] for chunk in chunks]
    collection.add(
        ids=[chunk["id"] for chunk in chunks],
        documents=documents,
        metadatas=[chunk["metadata"] for chunk in chunks],
        embeddings=embed_documents(documents),
    )
    print(f"Stored {len(chunks)} chunks in {COLLECTION}")


if __name__ == "__main__":
    main()
