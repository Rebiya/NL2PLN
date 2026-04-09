"""Qdrant-backed vector store for NL2PLN retrieval - Compatible with qdrant-client 1.17.1"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer


@dataclass
class RetrievedExample:
    score: float
    sentences: List[str]
    query: str
    expected_answer: str
    source_id: str


class QdrantPLNStore:
    """Qdrant store using Docker HTTP interface - compatible with v1.17.1"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "nl2pln_examples",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    ) -> None:
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model

        self.embedder = SentenceTransformer(self.embedding_model_name)
        self.client = QdrantClient(host=host, port=port, prefer_grpc=False)

        self._ensure_collection()

    def _ensure_collection(self) -> None:
        vector_size = self.embedder.get_sentence_embedding_dimension()
        collections = self.client.get_collections().collections
        existing_names = {c.name for c in collections}

        if self.collection_name not in existing_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )

    def _embed(self, texts: List[str]) -> List[List[float]]:
        vectors = self.embedder.encode(texts, normalize_embeddings=True)
        return [vector.tolist() for vector in vectors]

    @staticmethod
    def _build_document_text(example: Dict[str, Any]) -> str:
        sentence_blob = " ".join(example.get("sentences", []))
        question = example.get("question", "")
        expected_answer = example.get("expected_answer", "")
        return f"sentences: {sentence_blob}\nquestion: {question}\nexpected_answer: {expected_answer}".strip()

    def load_examples_from_json(self, dataset_path: str) -> List[Dict[str, Any]]:
        with open(dataset_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        flattened: List[Dict[str, Any]] = []
        for item_idx, item in enumerate(raw_data):
            sentences = item.get("sentences", [])
            for query_idx, query in enumerate(item.get("queries", [])):
                flattened.append({
                    "id": f"{item_idx}-{query_idx}",
                    "sentences": sentences,
                    "question": query.get("question", ""),
                    "expected_answer": query.get("expected_answer", ""),
                })
        return flattened

    def index_examples(self, examples: List[Dict[str, Any]], force_reindex: bool = False) -> None:
        if force_reindex:
            try:
                self.client.delete_collection(self.collection_name)
            except:
                pass
            self._ensure_collection()

        if not examples:
            return

        points: List[PointStruct] = []
        documents = [self._build_document_text(ex) for ex in examples]
        vectors = self._embed(documents)

        for example, vector in zip(examples, vectors):
            points.append(
                PointStruct(
                    id=str(uuid.uuid5(uuid.NAMESPACE_DNS, example["id"])),
                    vector=vector,
                    payload={
                        "source_id": example["id"],
                        "sentences": example.get("sentences", []),
                        "question": example.get("question", ""),
                        "expected_answer": example.get("expected_answer", ""),
                    },
                )
            )

        self.client.upsert(collection_name=self.collection_name, points=points, wait=True)

    def search(self, query_text: str, top_k: int = 5) -> List[RetrievedExample]:
        """Search using Qdrant with compatibility across 1.17.1 client variants."""
        if not query_text.strip():
            return []

        query_vector = self._embed([query_text])[0]
        result = None

        # Preferred stable call for qdrant-client 1.17.1 (HTTP mode).
        if hasattr(self.client, "search"):
            result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                with_payload=True,
            )
        else:
            # Compatibility fallback for environments exposing query_points only.
            query_res = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=top_k,
                with_payload=True,
            )
            result = getattr(query_res, "points", query_res)

        retrieved: List[RetrievedExample] = []
        for hit in result:
            payload = hit.payload or {}
            retrieved.append(
                RetrievedExample(
                    score=float(hit.score),
                    sentences=list(payload.get("sentences", [])),
                    query=str(payload.get("question", "")),
                    expected_answer=str(payload.get("expected_answer", "")),
                    source_id=str(payload.get("source_id", "")),
                )
            )
        return retrieved