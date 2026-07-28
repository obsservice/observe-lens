from observelens_knowledge_base.documents.indexing import SimpleDocumentChunker
from observelens_knowledge_base.documents.schemas import ChunkConfig


def test_chunker_preserves_heading_metadata() -> None:
    content = "# Direct Memory\n\nBroker OOM troubleshooting steps.\n\nCheck cache metrics."

    chunks = SimpleDocumentChunker().split(content, ChunkConfig(max_tokens=100))

    assert len(chunks) == 1
    assert chunks[0].title == "Direct Memory"
    assert chunks[0].section_path == ["Direct Memory"]
    assert "Broker OOM" in chunks[0].content


def test_chunker_splits_by_token_limit() -> None:
    content = "one two three\n\nfour five six\n\nseven eight nine"

    chunks = SimpleDocumentChunker().split(content, ChunkConfig(max_tokens=4, overlap_tokens=0))

    assert [chunk.chunk_index for chunk in chunks] == [0, 1, 2]
    assert all(chunk.content for chunk in chunks)
