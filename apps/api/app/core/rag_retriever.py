"""
Career RAG retriever.

Builds a local vector index from career/project YAML data and returns
top-k context chunks relevant to a user query.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

import yaml

from apps.api.app.core.config import settings


class CareerRAGRetriever:
    """Retrieves relevant context chunks from career data using local embeddings."""

    def __init__(self):
        self._vectorstore: Optional[Any] = None
        self._index_signature: Optional[str] = None
        self._index_error: Optional[str] = None
        self._docs_cache: list[dict[str, Any]] = []

    def retrieve(self, query: str, top_k: Optional[int] = None) -> dict[str, Any]:
        """
        Retrieve top-k context chunks for the user query.

        Returns:
            {
                "chunks": [
                    {"text": "...", "source": "experience", "id": "..."},
                    ...
                ],
                "error": "..." | None,
            }
        """
        if not settings.rag_enabled:
            return {"chunks": [], "error": "RAG disabled by configuration"}

        if not query or not query.strip():
            return {"chunks": [], "error": None}

        try:
            self._ensure_index()
        except Exception as exc:
            self._index_error = str(exc)
            fallback_chunks = self._keyword_fallback(query, top_k or settings.rag_top_k)
            return {
                "chunks": fallback_chunks,
                "error": f"Vector retrieval unavailable, using keyword fallback: {self._index_error}",
            }

        if self._vectorstore is None:
            fallback_chunks = self._keyword_fallback(query, top_k or settings.rag_top_k)
            return {
                "chunks": fallback_chunks,
                "error": f"RAG index not available, using keyword fallback: {self._index_error or 'unknown error'}",
            }

        k = top_k or settings.rag_top_k

        try:
            docs = self._vectorstore.similarity_search(query, k=k)
        except Exception as exc:
            return {"chunks": [], "error": f"RAG query failed: {str(exc)}"}

        chunks: list[dict[str, str]] = []
        for doc in docs:
            source = (doc.metadata or {}).get("source", "unknown")
            chunk_id = (doc.metadata or {}).get("id", "unknown")
            chunks.append(
                {
                    "text": doc.page_content,
                    "source": source,
                    "id": chunk_id,
                }
            )

        return {"chunks": chunks, "error": None}

    def _keyword_fallback(self, query: str, top_k: int) -> list[dict[str, str]]:
        if not self._docs_cache:
            self._docs_cache = self._build_documents()

        q_tokens = self._tokenize(query)
        if not q_tokens:
            return []

        scored: list[tuple[int, dict[str, Any]]] = []
        for doc in self._docs_cache:
            text = doc.get("text", "")
            d_tokens = self._tokenize(text)
            if not d_tokens:
                continue
            score = len(q_tokens.intersection(d_tokens))
            if score > 0:
                scored.append((score, doc))

        scored.sort(key=lambda item: item[0], reverse=True)

        chunks: list[dict[str, str]] = []
        for _, doc in scored[:top_k]:
            metadata = doc.get("metadata", {})
            chunks.append(
                {
                    "text": doc.get("text", ""),
                    "source": metadata.get("source", "unknown"),
                    "id": metadata.get("id", "unknown"),
                }
            )

        return chunks

    def _tokenize(self, text: str) -> set[str]:
        tokens = re.findall(r"[a-zA-Z0-9_]+", (text or "").lower())
        return {t for t in tokens if len(t) > 2}

    def _ensure_index(self) -> None:
        signature = self._compute_data_signature()

        if self._vectorstore is not None and signature == self._index_signature:
            return

        docs = self._build_documents()
        self._docs_cache = docs

        if not docs:
            self._vectorstore = None
            self._index_signature = signature
            self._index_error = "No documents available for indexing"
            return

        # Local imports keep optional dependency failures isolated to this module.
        from langchain_community.embeddings import OllamaEmbeddings
        from langchain_community.vectorstores import Chroma

        texts = [d["text"] for d in docs]
        metadatas = [d["metadata"] for d in docs]

        embeddings = OllamaEmbeddings(
            model=settings.rag_embedding_model,
            base_url=settings.ollama_base_url,
        )

        self._vectorstore = Chroma.from_texts(
            texts=texts,
            embedding=embeddings,
            metadatas=metadatas,
            collection_name="career_rag",
        )
        self._index_signature = signature
        self._index_error = None

    def _compute_data_signature(self) -> str:
        career_path, projects_path = self._data_paths()
        parts = []
        for path in [career_path, projects_path]:
            if path.exists():
                stat = path.stat()
                parts.append(f"{path}:{stat.st_mtime_ns}:{stat.st_size}")
            else:
                parts.append(f"{path}:missing")
        return "|".join(parts)

    def _data_paths(self) -> tuple[Path, Path]:
        root_dir = Path(__file__).resolve().parents[4]
        data_dir = root_dir / "data"
        return data_dir / "career.yaml", data_dir / "projects.yaml"

    def _load_yaml(self) -> tuple[dict[str, Any], dict[str, Any]]:
        career_path, projects_path = self._data_paths()
        career_data: dict[str, Any] = {}
        projects_data: dict[str, Any] = {}

        if career_path.exists():
            with open(career_path, "r", encoding="utf-8") as f:
                career_data = yaml.safe_load(f) or {}

        if projects_path.exists():
            with open(projects_path, "r", encoding="utf-8") as f:
                projects_data = yaml.safe_load(f) or {}

        return career_data, projects_data

    def _build_documents(self) -> list[dict[str, Any]]:
        career_data, projects_data = self._load_yaml()
        docs: list[dict[str, Any]] = []

        def add_doc(source: str, doc_id: str, text: str) -> None:
            for idx, chunk in enumerate(self._chunk_text(text)):
                docs.append(
                    {
                        "text": chunk,
                        "metadata": {
                            "source": source,
                            "id": f"{doc_id}:{idx}",
                        },
                    }
                )

        profile = career_data.get("profile", {})
        if profile:
            add_doc("profile", "profile", json.dumps(profile, ensure_ascii=True, indent=2))

        skills = career_data.get("skills", {})
        for category, values in skills.items():
            if isinstance(values, list) and values:
                text = f"Skill category: {category}\nSkills: {', '.join(str(v) for v in values)}"
                add_doc("skills", f"skills:{category}", text)

        for idx, exp in enumerate(career_data.get("experience", [])):
            if not isinstance(exp, dict):
                continue
            add_doc("experience", f"experience:{idx}", json.dumps(exp, ensure_ascii=True, indent=2))

        for idx, proj in enumerate(projects_data.get("projects", [])):
            if not isinstance(proj, dict):
                continue
            add_doc("projects", f"project:{idx}", json.dumps(proj, ensure_ascii=True, indent=2))

        return docs

    def _chunk_text(self, text: str, chunk_size: int = 700, overlap: int = 120) -> list[str]:
        clean = (text or "").strip()
        if not clean:
            return []

        if len(clean) <= chunk_size:
            return [clean]

        chunks = []
        start = 0
        while start < len(clean):
            end = min(start + chunk_size, len(clean))
            chunks.append(clean[start:end])
            if end >= len(clean):
                break
            start = max(0, end - overlap)

        return chunks


_retriever: Optional[CareerRAGRetriever] = None


def get_career_retriever() -> CareerRAGRetriever:
    global _retriever
    if _retriever is None:
        _retriever = CareerRAGRetriever()
    return _retriever
