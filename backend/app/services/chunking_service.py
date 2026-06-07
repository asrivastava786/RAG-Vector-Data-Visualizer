from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.services.embedding_service import cosine_similarity, get_embedding_provider

WORD_RE = re.compile(r"\S+")
HEADING_RE = re.compile(r"^(#{1,6}\s+.+|[A-Z][A-Z0-9 .,&/-]{6,})$", re.MULTILINE)
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")


@dataclass(frozen=True)
class ChunkCandidate:
    text: str
    start_offset: int
    end_offset: int
    section_heading: str | None = None
    page_number: int | None = None
    warnings: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ChunkerConfig:
    splitter_type: str
    chunk_size: int
    overlap: int
    preserve_headings: bool = True
    preserve_tables: bool = True
    semantic_threshold: float | None = None
    config: dict = field(default_factory=dict)


class BaseChunker:
    def __init__(self, config: ChunkerConfig) -> None:
        self.config = config

    def chunk(self, text: str) -> list[ChunkCandidate]:
        raise NotImplementedError

    def _build_candidate(
        self,
        source: str,
        *,
        start: int,
        end: int,
        heading: str | None = None,
        metadata: dict | None = None,
    ) -> ChunkCandidate:
        raw_text = source[start:end]
        chunk_text = raw_text.strip()
        leading_trim = len(raw_text) - len(raw_text.lstrip())
        trailing_trim = len(raw_text) - len(raw_text.rstrip())
        adjusted_start = start + leading_trim
        adjusted_end = max(adjusted_start, end - trailing_trim)
        return ChunkCandidate(
            text=chunk_text,
            start_offset=adjusted_start,
            end_offset=adjusted_end,
            section_heading=heading,
            warnings=_warnings_for_text(chunk_text, self.config.chunk_size),
            metadata=metadata or {},
        )


class FixedSizeChunker(BaseChunker):
    def chunk(self, text: str) -> list[ChunkCandidate]:
        spans = [(match.start(), match.end()) for match in WORD_RE.finditer(text)]
        if not spans:
            return []
        size = max(1, self.config.chunk_size)
        overlap = min(max(0, self.config.overlap), max(0, size - 1))
        candidates: list[ChunkCandidate] = []
        word_index = 0
        while word_index < len(spans):
            end_word = min(len(spans), word_index + size)
            candidates.append(
                self._build_candidate(
                    text,
                    start=spans[word_index][0],
                    end=spans[end_word - 1][1],
                    metadata={"splitter": "fixed", "word_start": word_index, "word_end": end_word},
                )
            )
            if end_word == len(spans):
                break
            word_index = max(end_word - overlap, word_index + 1)
        return candidates


class RecursiveChunker(BaseChunker):
    def chunk(self, text: str) -> list[ChunkCandidate]:
        segments = (
            _section_segments(text)
            if self.config.preserve_headings
            else [(0, len(text), None)]
        )
        candidates: list[ChunkCandidate] = []
        fixed = FixedSizeChunker(self.config)
        for start, end, heading in segments:
            segment_text = text[start:end]
            if _estimated_tokens(segment_text) <= self.config.chunk_size:
                candidate = self._build_candidate(
                    text,
                    start=start,
                    end=end,
                    heading=heading,
                    metadata={"splitter": "recursive", "level": "section"},
                )
                if candidate.text:
                    candidates.append(candidate)
                continue
            candidates.extend(
                _split_oversized_segment(
                    segment_text,
                    base_offset=start,
                    heading=heading,
                    config=self.config,
                    source=text,
                    fallback=fixed,
                )
            )
        return [candidate for candidate in candidates if candidate.text]


class HeadingChunker(BaseChunker):
    def chunk(self, text: str) -> list[ChunkCandidate]:
        config = ChunkerConfig(
            splitter_type="recursive",
            chunk_size=self.config.chunk_size,
            overlap=self.config.overlap,
            preserve_headings=True,
            preserve_tables=self.config.preserve_tables,
        )
        return RecursiveChunker(config).chunk(text)


class SemanticChunker(BaseChunker):
    def chunk(self, text: str) -> list[ChunkCandidate]:
        paragraphs = _paragraph_spans(text)
        if not paragraphs:
            return []
        provider = get_embedding_provider(self.config.config.get("embedding_provider"))
        threshold = (
            self.config.semantic_threshold
            if self.config.semantic_threshold is not None
            else 0.72
        )
        candidates: list[ChunkCandidate] = []
        group_start, group_end = paragraphs[0]
        previous_embedding = provider.embed_text(text[group_start:group_end])
        for start, end in paragraphs[1:]:
            paragraph_embedding = provider.embed_text(text[start:end])
            merged_tokens = _estimated_tokens(text[group_start:end])
            similar = cosine_similarity(previous_embedding, paragraph_embedding) >= threshold
            if similar and merged_tokens <= self.config.chunk_size:
                group_end = end
            else:
                candidates.append(
                    self._build_candidate(
                        text,
                        start=group_start,
                        end=group_end,
                        metadata={"splitter": "semantic", "threshold": threshold},
                    )
                )
                group_start, group_end = start, end
            previous_embedding = paragraph_embedding
        candidates.append(
            self._build_candidate(
                text,
                start=group_start,
                end=group_end,
                metadata={"splitter": "semantic", "threshold": threshold},
            )
        )
        return _split_candidates_that_are_too_large(text, candidates, self.config)


class TableAwareChunker(BaseChunker):
    def chunk(self, text: str) -> list[ChunkCandidate]:
        candidates: list[ChunkCandidate] = []
        recursive = RecursiveChunker(self.config)
        for start, end, is_table in _table_aware_blocks(text):
            if is_table:
                candidates.append(
                    self._build_candidate(
                        text,
                        start=start,
                        end=end,
                        metadata={"splitter": "table_aware", "preserved_table": True},
                    )
                )
                continue
            for candidate in recursive.chunk(text[start:end]):
                adjusted = _offset_candidate(candidate, start)
                adjusted.metadata.setdefault("splitter", "table_aware")
                candidates.append(adjusted)
        return candidates


def build_chunker(config: ChunkerConfig) -> BaseChunker:
    chunkers = {
        "fixed": FixedSizeChunker,
        "recursive": RecursiveChunker,
        "heading": HeadingChunker,
        "semantic": SemanticChunker,
        "table_aware": TableAwareChunker,
    }
    chunker_cls = chunkers.get(config.splitter_type)
    if chunker_cls is None:
        raise ValueError(f"Unsupported splitter type '{config.splitter_type}'.")
    return chunker_cls(config)


def chunk_text(text: str, config: ChunkerConfig) -> list[ChunkCandidate]:
    return build_chunker(config).chunk(text)


def _estimated_tokens(text: str) -> int:
    return len(WORD_RE.findall(text))


def _warnings_for_text(text: str, chunk_size: int) -> list[str]:
    warnings: list[str] = []
    token_count = _estimated_tokens(text)
    if token_count > chunk_size * 1.15:
        warnings.append("too_long")
    if token_count < max(12, chunk_size // 8):
        warnings.append("too_short")
    if text and text[-1] not in ".!?;:|)" and token_count > 20:
        warnings.append("possible_split_sentence")
    if _looks_like_partial_table(text):
        warnings.append("table_split")
    return warnings


def _section_segments(text: str) -> list[tuple[int, int, str | None]]:
    matches = list(HEADING_RE.finditer(text))
    if not matches:
        return [(0, len(text), None)]
    segments: list[tuple[int, int, str | None]] = []
    if matches[0].start() > 0:
        segments.append((0, matches[0].start(), None))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        heading = match.group(0).lstrip("#").strip()
        segments.append((match.start(), end, heading[:300]))
    return segments


def _paragraph_spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    for match in re.finditer(r"\S(?:.*?\S)?(?=\n\s*\n|\Z)", text, flags=re.DOTALL):
        spans.append((match.start(), match.end()))
    return spans or ([(0, len(text))] if text.strip() else [])


def _split_oversized_segment(
    segment_text: str,
    *,
    base_offset: int,
    heading: str | None,
    config: ChunkerConfig,
    source: str,
    fallback: FixedSizeChunker,
) -> list[ChunkCandidate]:
    candidates: list[ChunkCandidate] = []
    for paragraph_start, paragraph_end in _paragraph_spans(segment_text):
        absolute_start = base_offset + paragraph_start
        absolute_end = base_offset + paragraph_end
        paragraph = source[absolute_start:absolute_end]
        if _estimated_tokens(paragraph) <= config.chunk_size:
            candidate = fallback._build_candidate(
                source,
                start=absolute_start,
                end=absolute_end,
                heading=heading,
                metadata={"splitter": "recursive", "level": "paragraph"},
            )
            if candidate.text:
                candidates.append(candidate)
            continue
        candidates.extend(
            _split_by_sentences(
                source,
                start=absolute_start,
                end=absolute_end,
                heading=heading,
                config=config,
            )
        )
    return candidates


def _split_by_sentences(
    source: str,
    *,
    start: int,
    end: int,
    heading: str | None,
    config: ChunkerConfig,
) -> list[ChunkCandidate]:
    text = source[start:end]
    pieces = SENTENCE_RE.split(text)
    if len(pieces) <= 1:
        return [
            _offset_candidate(candidate, start)
            for candidate in FixedSizeChunker(config).chunk(text)
        ]
    candidates: list[ChunkCandidate] = []
    cursor = start
    group_start = start
    group_end = start
    group_text = ""
    builder = BaseChunker(config)
    for piece in pieces:
        piece_start = source.find(piece, cursor, end)
        if piece_start < 0:
            continue
        piece_end = piece_start + len(piece)
        next_text = f"{group_text} {piece}".strip()
        if group_text and _estimated_tokens(next_text) > config.chunk_size:
            candidates.append(
                builder._build_candidate(
                    source,
                    start=group_start,
                    end=group_end,
                    heading=heading,
                    metadata={"splitter": "recursive", "level": "sentence"},
                )
            )
            group_start = piece_start
            group_text = piece
        else:
            group_text = next_text
        group_end = piece_end
        cursor = piece_end
    if group_text:
        candidates.append(
            builder._build_candidate(
                source,
                start=group_start,
                end=group_end,
                heading=heading,
                metadata={"splitter": "recursive", "level": "sentence"},
            )
        )
    return _split_candidates_that_are_too_large(source, candidates, config)


def _offset_candidate(candidate: ChunkCandidate, offset: int) -> ChunkCandidate:
    return ChunkCandidate(
        text=candidate.text,
        start_offset=candidate.start_offset + offset,
        end_offset=candidate.end_offset + offset,
        section_heading=candidate.section_heading,
        page_number=candidate.page_number,
        warnings=candidate.warnings,
        metadata=dict(candidate.metadata),
    )


def _split_candidates_that_are_too_large(
    source: str,
    candidates: list[ChunkCandidate],
    config: ChunkerConfig,
) -> list[ChunkCandidate]:
    output: list[ChunkCandidate] = []
    fixed = FixedSizeChunker(config)
    for candidate in candidates:
        if _estimated_tokens(candidate.text) <= config.chunk_size:
            output.append(candidate)
            continue
        for split in fixed.chunk(candidate.text):
            output.append(_offset_candidate(split, candidate.start_offset))
    return output


def _table_aware_blocks(text: str) -> list[tuple[int, int, bool]]:
    lines = text.splitlines(keepends=True)
    blocks: list[tuple[int, int, bool]] = []
    cursor = 0
    current_start = 0
    current_is_table: bool | None = None
    for line in lines:
        is_table = bool(TABLE_ROW_RE.match(line))
        if current_is_table is None:
            current_start = cursor
            current_is_table = is_table
        elif is_table != current_is_table:
            blocks.append((current_start, cursor, current_is_table))
            current_start = cursor
            current_is_table = is_table
        cursor += len(line)
    if current_is_table is not None:
        blocks.append((current_start, cursor, current_is_table))
    return blocks or [(0, len(text), False)]


def _looks_like_partial_table(text: str) -> bool:
    table_lines = [line for line in text.splitlines() if TABLE_ROW_RE.match(line)]
    return bool(table_lines) and len(table_lines) < 2
