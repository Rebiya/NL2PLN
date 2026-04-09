"""Text preprocessing utilities for RAG-based NL2PLN conversion."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

import nltk
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer


def _ensure_nltk_resource(resource_path: str, download_name: str) -> None:
    """Download an NLTK resource when missing."""
    try:
        nltk.data.find(resource_path)
    except LookupError:
        nltk.download(download_name, quiet=True)


def _to_wordnet_pos(treebank_tag: str) -> str:
    """Map treebank POS tags to wordnet POS tags."""
    if treebank_tag.startswith("J"):
        return wordnet.ADJ
    if treebank_tag.startswith("V"):
        return wordnet.VERB
    if treebank_tag.startswith("N"):
        return wordnet.NOUN
    if treebank_tag.startswith("R"):
        return wordnet.ADV
    return wordnet.NOUN


@dataclass
class PreprocessedSample:
    """Container for normalized text and extracted features."""

    original: List[str]
    normalized: List[str]
    concepts: List[str]
    retrieval_text: str


class RAGPreprocessor:
    """Aggressive normalization + concept extraction for retrieval quality."""

    _STOPWORDS = {
        "a",
        "an",
        "the",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "to",
        "of",
        "in",
        "on",
        "at",
        "for",
        "with",
        "and",
        "or",
        "but",
        "if",
        "then",
        "than",
        "that",
        "this",
        "those",
        "these",
        "all",
        "any",
        "some",
        "every",
        "each",
        "who",
        "what",
        "when",
        "where",
        "why",
        "how",
    }

    def __init__(self) -> None:
        _ensure_nltk_resource("tokenizers/punkt", "punkt")
        _ensure_nltk_resource("taggers/averaged_perceptron_tagger", "averaged_perceptron_tagger")
        _ensure_nltk_resource("corpora/wordnet", "wordnet")
        _ensure_nltk_resource("corpora/omw-1.4", "omw-1.4")
        self._lemmatizer = WordNetLemmatizer()

    @staticmethod
    def _clean_text(text: str) -> str:
        cleaned = text.strip().replace("-", " ")
        cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned.lower().strip()

    def normalize_sentence(self, sentence: str) -> str:
        """Normalize sentence with lowercasing and POS-aware lemmatization."""
        cleaned = self._clean_text(sentence)
        if not cleaned:
            return ""

        tokens = nltk.word_tokenize(cleaned)
        tagged = nltk.pos_tag(tokens)

        lemmas: List[str] = []
        for token, tag in tagged:
            if not token:
                continue
            lemma = self._lemmatizer.lemmatize(token, _to_wordnet_pos(tag))
            lemmas.append(lemma)

        return " ".join(lemmas)

    def extract_concepts(self, normalized_sentences: List[str]) -> List[str]:
        """Extract concept-like nouns/entities from normalized text."""
        concepts = set()
        for sentence in normalized_sentences:
            if not sentence:
                continue
            tokens = nltk.word_tokenize(sentence)
            tagged = nltk.pos_tag(tokens)
            for token, tag in tagged:
                if token in self._STOPWORDS:
                    continue
                if len(token) <= 1:
                    continue
                if tag.startswith("NN") or tag.startswith("VB") or tag.startswith("JJ"):
                    concepts.add(token)
        return sorted(concepts)

    def preprocess(self, texts: List[str]) -> PreprocessedSample:
        """Preprocess a list of NL sentences for retrieval/generation."""
        normalized = [self.normalize_sentence(text) for text in texts]
        concepts = self.extract_concepts(normalized)
        retrieval_text = " ".join([*normalized, " ".join(concepts)]).strip()
        return PreprocessedSample(
            original=texts,
            normalized=normalized,
            concepts=concepts,
            retrieval_text=retrieval_text,
        )
