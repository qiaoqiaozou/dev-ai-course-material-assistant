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

import chromadb
from sentence_transformers import SentenceTransformer

from src.config import config
from src.capabilities.web_documents import load_course_documents




DOCUMENTS = load_course_documents("https://mazarbaloch.github.io/dev-ai-course/")


def make_chunks(documents):
    chunks = []

    for document_number, document in enumerate(documents, start=1):
        paragraphs = [
            paragraph.strip()
            for paragraph in document["text"].split("\n\n")
            if paragraph.strip()
        ]

        for number, paragraph in enumerate(paragraphs, start=1):
            chunks.append({
                "id": f'{document["course"]}-doc{document_number}-c{number}',
                "text": paragraph,
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
    query_vector = embedding_model.encode(
        [question],
        normalize_embeddings=True,
    ).tolist()[0]

    result = collection.query(
        query_embeddings=[query_vector],
        n_results=min(top_k, collection.count()),
        where={"course": course},
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