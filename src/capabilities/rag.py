"""
Optional project capability: Retrieval-Augmented Generation (RAG).

Implement this module only if this capability is relevant to your application's
user problem. Remove the file if the capability is not used.

Conceptual Overview:
-------------------
Retrieval-Augmented Generation (RAG) enhances model responses by retrieving
relevant external information before passing the prompt to the LLM.

Key concepts to consider when implementing RAG:
1. Document Ingestion: Loading custom domain documents (PDFs, text, markdown).
2. Embeddings & Vector Store: Converting text into dense vector embeddings and
   storing them in a vector database or local index.
3. Retrieval: Searching the vector store for text chunks semantically similar
   to the user query.
4. Grounding: Constructing a prompt that supplies retrieved context to the model,
   reducing hallucinations and grounding answers in verified factual data.

Note:
-----
Do not implement RAG unless your project requires answering questions over
specific custom documents or static domain knowledge bases.
"""

# Implement custom RAG pipeline below if selected for your project.
import re

import chromadb
from sentence_transformers import SentenceTransformer

from src.config import config
from src.capabilities.web_documents import load_course_documents




DOCUMENTS = load_course_documents("https://mazarbaloch.github.io/dev-ai-course/")


def make_chunks(documents):
    chunks = []
    target_words = 120

    for document_number, document in enumerate(documents, start=1):
        paragraphs = [
            paragraph.strip()
            for paragraph in document["text"].split("\n\n")
            if paragraph.strip()
        ]

        grouped_paragraphs = []
        current_paragraphs = []
        current_words = 0

        for paragraph in paragraphs:
            paragraph_words = len(paragraph.split())

            current_paragraphs.append(paragraph)
            current_words += paragraph_words

            if current_words >= target_words:
                grouped_paragraphs.append(
                    "\n\n".join(current_paragraphs)
                )
                current_paragraphs = []
                current_words = 0

        if current_paragraphs:
            remaining_text = "\n\n".join(current_paragraphs)
            if grouped_paragraphs and current_words < 40:
                grouped_paragraphs[-1] += "\n\n" + remaining_text
            else:
                grouped_paragraphs.append(remaining_text)
          

        for number, text in enumerate(grouped_paragraphs, start=1):
            chunks.append({
                "id": f'{document["course"]}-doc{document_number}-c{number}',
                "text": f'{document["title"]}\n\n{text}',
                "metadata": {
                    "title": document["title"],
                    "course": document["course"],
                    "url": document["url"],
                },
            })

    return chunks


embedding_model = SentenceTransformer(config.embedding_model)
chunks = make_chunks(DOCUMENTS)

vectors = embedding_model.encode(
    [chunk["text"] for chunk in chunks],
    normalize_embeddings=True,
).tolist()

client = chromadb.Client()
collection = client.get_or_create_collection(
    name="course_web_documents",
    metadata={"hnsw:space": "cosine"},
)

collection.upsert(
    ids=[chunk["id"] for chunk in chunks],
    embeddings=vectors,
    documents=[chunk["text"] for chunk in chunks],
    metadatas=[chunk["metadata"] for chunk in chunks],
)


def retrieve(question: str, course="DEV-AI", top_k=3):
    sample_projects_match = re.search(
        r"\bsample\s+projects?\b",
        question,
        flags=re.IGNORECASE,
    )

    if sample_projects_match:
        for document in DOCUMENTS:
            if (
                document["course"] == course
                and document["url"].rstrip("/").endswith(
                    "/docs/sample-projects"
                )
            ):
                return [{
                    "id": f"{course}-sample-projects-page",
                    "text": document["text"],
                    "title": document["title"],
                    "url": document["url"],
                }]
            
    query_vector = embedding_model.encode(
        [question],
        normalize_embeddings=True,
    ).tolist()[0]

    where = {"course": course}

    exercise_match = re.search(
        r"\bexercise\s*0?([1-8])\b",
        question,
        flags=re.IGNORECASE,
    )

    if exercise_match:
        exercise_number = int(exercise_match.group(1))
        exercise_url = (
            "https://mazarbaloch.github.io/dev-ai-course/"
            f"docs/exercises/exercise-{exercise_number:02d}"
        )

        where = {
            "$and": [
                {"course": course},
                {"url": exercise_url},
            ],
        }

    matching = collection.get(
        where=where,
        include=[],
    )

    if not matching["ids"]:
        return []

    result = collection.query(
        query_embeddings=[query_vector],
        n_results=min(top_k, len(matching["ids"])),
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    evidence = []

    for chunk_id, text, metadata, distance in zip(
        result["ids"][0],
        result["documents"][0],
        result["metadatas"][0],
        result["distances"][0],
    ):
        evidence.append({
            "id": chunk_id,
            "text": text,
            "title": metadata["title"],
            "url": metadata["url"],
            "distance": round(float(distance), 3),
        })

    return evidence