from app.services.chunking_service import ChunkerConfig, chunk_text
from app.services.embedding_service import cosine_similarity, get_embedding_provider, sparse_terms


def test_fixed_chunker_preserves_overlap_offsets() -> None:
    text = " ".join(f"token{i}" for i in range(10))
    chunks = chunk_text(text, ChunkerConfig(splitter_type="fixed", chunk_size=4, overlap=2))

    assert [chunk.text for chunk in chunks] == [
        "token0 token1 token2 token3",
        "token2 token3 token4 token5",
        "token4 token5 token6 token7",
        "token6 token7 token8 token9",
    ]
    assert chunks[1].start_offset == text.index("token2")
    assert chunks[-1].end_offset == len(text)


def test_heading_chunker_keeps_section_metadata() -> None:
    text = "# Eligibility\nEmployees may request leave.\n\n# Approval\nManagers approve leave."
    chunks = chunk_text(text, ChunkerConfig(splitter_type="heading", chunk_size=20, overlap=0))

    assert len(chunks) == 2
    assert chunks[0].section_heading == "Eligibility"
    assert chunks[1].section_heading == "Approval"


def test_table_aware_chunker_preserves_markdown_table() -> None:
    text = (
        "Intro paragraph.\n| Name | Role |\n| Ada | Admin |\n"
        "| Lin | Viewer |\nClosing paragraph."
    )
    chunks = chunk_text(text, ChunkerConfig(splitter_type="table_aware", chunk_size=8, overlap=0))

    table_chunks = [chunk for chunk in chunks if chunk.metadata.get("preserved_table")]
    assert len(table_chunks) == 1
    assert "| Ada | Admin |" in table_chunks[0].text
    assert "table_split" not in table_chunks[0].warnings


def test_semantic_chunker_uses_deterministic_embeddings() -> None:
    text = "Leave policy eligibility for employees.\n\nLeave policy approval for employees."
    chunks = chunk_text(
        text,
        ChunkerConfig(splitter_type="semantic", chunk_size=30, overlap=0, semantic_threshold=0.1),
    )

    assert len(chunks) == 1
    assert chunks[0].metadata["splitter"] == "semantic"


def test_embedding_provider_is_stable_and_sparse_terms_count_tokens() -> None:
    provider = get_embedding_provider()
    left = provider.embed_text("policy policy approval")
    right = provider.embed_text("policy policy approval")

    assert left == right
    assert cosine_similarity(left, right) > 0.99
    assert sparse_terms("Policy policy approval") == {"policy": 2, "approval": 1}
