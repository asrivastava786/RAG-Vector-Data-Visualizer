from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from typing import Protocol

EMBEDDING_DIMENSIONS = 1536
TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


class EmbeddingProvider(Protocol):
    dimensions: int

    def embed_text(self, text: str) -> list[float]:
        ...

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        ...


@dataclass(frozen=True)
class DeterministicLocalEmbeddingProvider:
    """Stable local embedding stand-in for development and tests.

    The provider hashes normalized tokens into a fixed-size signed vector. It is
    deterministic, dependency-light, and API-compatible with hosted/local
    provider implementations that can be added later.
    """

    dimensions: int = EMBEDDING_DIMENSIONS

    def embed_text(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        tokens = tokenize(text)
        if not tokens:
            return vector
        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=12).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            weight = 1.0 + (digest[5] / 255.0)
            vector[index] += sign * weight
        return normalize_vector(vector)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(text) for text in texts]


def get_embedding_provider(provider_name: str | None = None) -> EmbeddingProvider:
    # OpenAI-compatible, BGE-compatible, and sentence-transformers providers plug in here.
    return DeterministicLocalEmbeddingProvider()


def tokenize(text: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_RE.finditer(text)]


def sparse_terms(text: str) -> dict[str, int]:
    terms: dict[str, int] = {}
    for token in tokenize(text):
        terms[token] = terms.get(token, 0) + 1
    return terms


def normalize_vector(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return sum(a * b for a, b in zip(left, right, strict=True))
