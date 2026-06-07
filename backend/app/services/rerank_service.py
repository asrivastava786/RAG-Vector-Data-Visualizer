from __future__ import annotations

from typing import Protocol, TypeVar

T = TypeVar("T")


class Reranker(Protocol):
    def rerank(self, query: str, candidates: list[T]) -> list[T]:
        ...


class NoopReranker:
    def rerank(self, query: str, candidates: list[T]) -> list[T]:
        return candidates


def get_reranker(enabled: bool = False) -> Reranker:
    # Hosted and local cross-encoder rerankers plug in here.
    return NoopReranker()
