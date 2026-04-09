"""RAG-based NL2PLN pipeline (DSPy-free) - OpenRouter + Qdrant Docker."""
# PIPELINE SUMMARY:
# 1. Preprocess input text (normalize + extract concepts)
# 2. Retrieve similar examples from Qdrant (RAG)
# 3. Build controlled prompt using PLN specification
# 4. Use LLM to generate structured PLN (statements + queries)
# 5. Clean and deduplicate output
# 6. Return results for symbolic reasoning (MeTTa / PeTTaChainer)
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from openai import OpenAI
# Loads PLN language specification (rules, syntax, constraints for logic generation)
from pettachainer.pettachainer import get_language_spec

from pln_prompt import build_prompts
from qdrant_store import QdrantPLNStore
from rag_preprocessor import RAGPreprocessor


@dataclass
class NL2PLNResult:
    statements: List[str]
    queries: List[List[str]]


class RAGNL2PLN:
    """RAG-based NL2PLN using OpenRouter and Qdrant Docker."""
    # Core pipeline class:
    # Combines preprocessing + retrieval + LLM + symbolic-ready output
    def __init__(
        self,
        data_file: str = "data/all.json",
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        collection_name: str = "nl2pln_examples",
        top_k: int = 6,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> None:
        self.top_k = top_k
        self.data_file = Path(data_file)
        self.model = model or os.getenv("NL2PLN_MODEL", "openrouter/deepseek/deepseek-v3.2")
        self.pln_spec = get_language_spec(llm_focused=True)

        self.preprocessor = RAGPreprocessor()# Initializes vector database connection (Qdrant)

        # Initializes vector database connection (Qdrant)
        self.store = QdrantPLNStore(
            host=qdrant_host,
            port=qdrant_port,
            collection_name=collection_name,
        )

        # OpenRouter client
        self.client = OpenAI(
            api_key=api_key or os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
        )

        # Index examples on startup
        examples = self.store.load_examples_from_json(str(self.data_file))
        self.store.index_examples(examples, force_reindex=False)


    # Removes duplicates while preserving original order
    # Important because LLM may generate repeated statements
    @staticmethod
    def _dedupe_preserve_order(items: List[str]) -> List[str]:
        seen = set()
        deduped: List[str] = []
        for item in items:
            key = item.strip()
            if not key or key in seen:
                continue
            seen.add(key)
            deduped.append(key)
        return deduped
    # Extract structured JSON from LLM output
    # Handles cases where LLM returns:
    # - pure JSON good
    # - JSON wrapped in text is bad but we can regex out the JSON part
    @staticmethod
    def _extract_json(raw_text: str) -> Dict[str, List[str]]:
        raw_text = raw_text.strip()# Fallback: extract JSON substring using regex
        try:
            parsed = json.loads(raw_text)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        # Fallback: extract JSON substring using regex
        import re
        match = re.search(r"\{.*\}", raw_text, flags=re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, dict):
                    return parsed
            except:
                pass
        return {"statements": [], "queries": []}

    def _generate_once(
        self,
        *,
        sentences: List[str],
        question: str,
        context_statements: List[str],
    ) -> Dict[str, List[str]]:
        input_texts = list(sentences)
        if question:
            input_texts.append(question)

        preprocessed = self.preprocessor.preprocess(input_texts)
        normalized_question = preprocessed.normalized[-1] if question else ""
        normalized_sentences = preprocessed.normalized[:-1] if question else preprocessed.normalized

        retrieved = self.store.search(preprocessed.retrieval_text, top_k=self.top_k)

        prompts = build_prompts(
            pln_spec=self.pln_spec,
            sentences=sentences,
            question=question,
            normalized_sentences=normalized_sentences,
            normalized_question=normalized_question,
            concepts=preprocessed.concepts,
            context_statements=context_statements,
            retrieved_examples=retrieved,
        )

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0.1,
            max_tokens=2048,      # strongly reduced
            messages=[
                {"role": "system", "content": prompts.system_prompt},
                {"role": "user", "content": prompts.user_prompt},
            ],
        )
        text = response.choices[0].message.content or "{}"
        parsed = self._extract_json(text)

        statements = self._dedupe_preserve_order(list(parsed.get("statements", [])))
        queries = self._dedupe_preserve_order(list(parsed.get("queries", [])))

        return {"statements": statements, "queries": queries}

    def convert(self, sentences: List[str], queries: List[dict]) -> NL2PLNResult:
        base = self._generate_once(sentences=sentences, question="", context_statements=[])

        statements = self._dedupe_preserve_order(base.get("statements", []))
        query_outputs: List[List[str]] = []

        for item in queries:
            question = str(item.get("question", "")).strip()
            if not question:
                query_outputs.append([])
                continue

            generated = self._generate_once(
                sentences=sentences,
                question=question,
                context_statements=statements,
            )
            for stmt in generated.get("statements", []):
                if stmt not in statements:
                    statements.append(stmt)
            query_outputs.append(generated.get("queries", []))

        return NL2PLNResult(statements=statements, queries=query_outputs)