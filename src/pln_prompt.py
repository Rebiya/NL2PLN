"""Prompt templates and builders for RAG-based NL2PLN generation."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from dataclasses import dataclass
from typing import List

from qdrant_store import RetrievedExample


@dataclass
class PromptBundle:
    """Container for prompt messages passed to the chat model."""

    system_prompt: str
    user_prompt: str


def _format_retrieved_examples(examples: List[RetrievedExample], max_examples: int = 5) -> str:
    blocks = []
    for idx, example in enumerate(examples[:max_examples], start=1):
        blocks.append(
            "\n".join(
                [
                    f"Example {idx} (score={example.score:.4f}, id={example.source_id})",
                    f"Sentences: {json.dumps(example.sentences, ensure_ascii=True)}",
                    f"Question: {example.query}",
                    f"Expected answer: {example.expected_answer}",
                ]
            )
        )
    return "\n\n".join(blocks) if blocks else "No retrieved examples."


@lru_cache(maxsize=1)
def _load_core_instructions() -> str:
    """Load the exact DSPy signature instructions from simba_all.json."""
    simba_path = Path(__file__).resolve().parent / "simba_all.json"
    with open(simba_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data["nl2pln.predict"]["signature"]["instructions"]


def build_prompts(
    *,
    pln_spec: str,
    sentences: List[str],
    question: str,
    normalized_sentences: List[str],
    normalized_question: str,
    concepts: List[str],
    context_statements: List[str],
    retrieved_examples: List[RetrievedExample],
) -> PromptBundle:
    """Build strict system+user prompts for deterministic JSON PLN output."""
    examples_text = _format_retrieved_examples(retrieved_examples)
    core_instructions = _load_core_instructions()
    system_prompt = f"""
{core_instructions}

PLN specification:
{pln_spec}

Hard constraints:
- Output MUST be JSON object with keys: "statements", "queries".
- "statements": array of PLN strings.
- "queries": array of PLN strings (one or more when question is provided; otherwise empty).
- Never output markdown, prose, or comments.
- Use snake_case constants for entities (e.g., "New York" -> "new_york").
- Use UpperCamelCase predicate names consistently.
- Prefer singular canonical concepts in predicates/types (dog not dogs).
- Keep variable names stable: $x, $y, $z, $tv, $prf.
- Reuse predicates from context when semantically equivalent.
- Use (STV 1.0 1.0) unless uncertainty is explicit in input.
- Ensure each query can be supported by generated or contextual statements.

Retrieved training examples:
{examples_text}
""".strip()

    user_prompt = json.dumps(
        {
            "task": "nl2pln_generation",
            "sentences": sentences,
            "question": question,
            "normalized_sentences": normalized_sentences,
            "normalized_question": normalized_question,
            "concepts": concepts,
            "context_statements": context_statements,
            "required_output_schema": {
                "statements": ["(: fact_name (Predicate arg1 arg2) (STV 1.0 1.0))"],
                "queries": ["(: $prf (Predicate arg1) $tv)"],
            },
        },
        ensure_ascii=True,
    )

    return PromptBundle(system_prompt=system_prompt, user_prompt=user_prompt)
