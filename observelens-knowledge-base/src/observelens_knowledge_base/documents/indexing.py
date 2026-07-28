from dataclasses import dataclass

from observelens_knowledge_base.documents.schemas import ChunkConfig


@dataclass(frozen=True)
class ParsedChunk:
    chunk_index: int
    content: str
    title: str | None
    section_path: list[str]
    token_count: int


class SimpleDocumentChunker:
    def split(self, content: str, config: ChunkConfig) -> list[ParsedChunk]:
        sections = self._paragraphs(content)
        chunks: list[ParsedChunk] = []
        current: list[str] = []
        current_tokens = 0
        title: str | None = None
        section_path: list[str] = []

        for paragraph in sections:
            if paragraph.startswith("#"):
                heading = paragraph.lstrip("#").strip()
                if heading:
                    title = heading
                    section_path = [heading]
            tokens = self._count_tokens(paragraph)
            if current and current_tokens + tokens > config.max_tokens:
                chunks.append(self._build_chunk(len(chunks), current, title, section_path))
                overlap = current[-1:] if config.overlap_tokens > 0 else []
                current = overlap.copy()
                current_tokens = sum(self._count_tokens(item) for item in current)
            current.append(paragraph)
            current_tokens += tokens

        if current:
            chunks.append(self._build_chunk(len(chunks), current, title, section_path))
        return chunks

    def _paragraphs(self, content: str) -> list[str]:
        normalized = content.replace("\r\n", "\n").replace("\r", "\n")
        return [part.strip() for part in normalized.split("\n\n") if part.strip()]

    def _count_tokens(self, content: str) -> int:
        return max(1, len(content.split()))

    def _build_chunk(
        self, index: int, paragraphs: list[str], title: str | None, section_path: list[str]
    ) -> ParsedChunk:
        content = "\n\n".join(paragraphs)
        return ParsedChunk(
            chunk_index=index,
            content=content,
            title=title,
            section_path=section_path,
            token_count=self._count_tokens(content),
        )
