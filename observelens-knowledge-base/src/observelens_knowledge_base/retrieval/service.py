from time import perf_counter

from observelens_knowledge_base.common.context import RequestContext
from observelens_knowledge_base.common.enums import DocumentType
from observelens_knowledge_base.common.schemas import EntityRef
from observelens_knowledge_base.database.models import (
    DocumentChunkModel,
    RetrievalFeedbackModel,
    RetrievalLogModel,
)
from observelens_knowledge_base.retrieval.repository import RetrievalRepository
from observelens_knowledge_base.retrieval.schemas import (
    Citation,
    InternalContextRetrieveRequest,
    InternalContextRetrieveResponse,
    KnowledgeContext,
    RetrievalFeedbackRequest,
    RetrievalFeedbackResponse,
    RetrievalFilters,
    RetrievalResult,
    RetrievalResultMetadata,
    RetrievalSearchRequest,
    RetrievalSearchResponse,
    RetrievalTrace,
)


class RetrievalService:
    def __init__(self, repository: RetrievalRepository) -> None:
        self.repository = repository

    async def search(
        self, ctx: RequestContext, request: RetrievalSearchRequest
    ) -> RetrievalSearchResponse:
        started = perf_counter()
        filters = request.filters or RetrievalFilters()
        keyword_candidates = await self.repository.search_chunks(
            ctx.tenant_id,
            request.query,
            request.knowledge_base_ids,
            filters.document_ids,
            max(request.top_k * 5, 30),
        )
        fallback_candidates = []
        if not keyword_candidates:
            fallback_candidates = await self.repository.list_ready_chunks(
                ctx.tenant_id,
                request.knowledge_base_ids,
                filters.document_ids,
                max(request.top_k * 5, 30),
            )
        candidates = keyword_candidates or fallback_candidates
        filtered = self._apply_metadata_filters(candidates, filters)
        ranked = sorted(
            filtered,
            key=lambda chunk: self._score(request.query, chunk),
            reverse=True,
        )[: request.top_k]
        results = [await self._build_result(ctx, request.query, chunk) for chunk in ranked]
        latency_ms = int((perf_counter() - started) * 1000)
        log = RetrievalLogModel(
            tenant_id=ctx.tenant_id,
            query=request.query,
            rewritten_query=None,
            filters=filters.model_dump(mode="json", exclude_none=True),
            result_chunk_ids=[str(result.chunk_id) for result in results],
            latency_ms=latency_ms,
            trace_id=ctx.request_id,
        )
        self.repository.add_log(log)
        await self.repository.session.flush()
        trace = None
        if request.include_trace:
            trace = RetrievalTrace(
                retrieval_id=log.id,
                rewritten_query=None,
                vector_candidates=len(candidates),
                keyword_candidates=len(keyword_candidates),
                reranked_candidates=len(ranked),
                latency_ms=latency_ms,
            )
        return RetrievalSearchResponse(query=request.query, results=results, trace=trace)

    async def submit_feedback(
        self, ctx: RequestContext, request: RetrievalFeedbackRequest
    ) -> RetrievalFeedbackResponse:
        feedback = RetrievalFeedbackModel(
            tenant_id=ctx.tenant_id,
            retrieval_log_id=request.retrieval_log_id,
            chunk_id=request.chunk_id,
            rating=request.rating,
            feedback_type=request.feedback_type,
            comment=request.comment,
            created_by=ctx.user_id,
        )
        self.repository.add_feedback(feedback)
        await self.repository.session.flush()
        return RetrievalFeedbackResponse.model_validate(feedback)

    async def retrieve_context(
        self, ctx: RequestContext, request: InternalContextRetrieveRequest
    ) -> InternalContextRetrieveResponse:
        filters = RetrievalFilters(
            document_types=request.document_types,
            tags=request.tags,
            entities=(
                [EntityRef(type=request.entity_type, name=request.entity_name)]
                if request.entity_type and request.entity_name
                else None
            ),
        )
        search_response = await self.search(
            ctx,
            RetrievalSearchRequest(
                query=request.query,
                knowledge_base_ids=request.knowledge_base_ids,
                filters=filters,
                top_k=request.top_k,
                rerank=True,
                include_trace=True,
            ),
        )
        trace = search_response.trace
        return InternalContextRetrieveResponse(
            retrieval_id=trace.retrieval_id if trace else search_response.results[0].chunk_id,
            query=search_response.query,
            contexts=[
                KnowledgeContext(
                    context_id=result.chunk_id,
                    content=result.content,
                    score=result.score,
                    citation=result.citation,
                    document_type=result.metadata.document_type,
                    tags=result.metadata.tags,
                )
                for result in search_response.results
            ],
            latency_ms=trace.latency_ms if trace else 0,
        )

    def _apply_metadata_filters(
        self, candidates: list[DocumentChunkModel], filters: RetrievalFilters
    ) -> list[DocumentChunkModel]:
        result = candidates
        if filters.document_types:
            allowed_types = {item.value for item in filters.document_types}
            result = [chunk for chunk in result if chunk.meta.get("document_type") in allowed_types]
        if filters.tags:
            requested = set(filters.tags)
            result = [
                chunk for chunk in result if requested.intersection(set(chunk.meta.get("tags", [])))
            ]
        if filters.entities:
            requested_entities = {(entity.type, entity.name) for entity in filters.entities}
            result = [
                chunk
                for chunk in result
                if requested_entities.intersection(
                    {
                        (item.get("type"), item.get("name"))
                        for item in chunk.meta.get("entities", [])
                    }
                )
            ]
        return result

    def _score(self, query: str, chunk: DocumentChunkModel) -> float:
        terms = {term.lower() for term in query.split() if term}
        content = chunk.content.lower()
        if not terms:
            return 0.1
        matched = sum(1 for term in terms if term in content)
        return min(1.0, 0.2 + (matched / len(terms)) * 0.8)

    async def _build_result(
        self, ctx: RequestContext, query: str, chunk: DocumentChunkModel
    ) -> RetrievalResult:
        document = await self.repository.get_document(ctx.tenant_id, chunk.document_id)
        version = await self.repository.get_version(ctx.tenant_id, chunk.document_version_id)
        document_type = None
        if chunk.meta.get("document_type"):
            document_type = DocumentType(chunk.meta["document_type"])
        score = self._score(query, chunk)
        return RetrievalResult(
            chunk_id=chunk.id,
            score=score,
            content=chunk.content,
            citation=Citation(
                document_id=chunk.document_id,
                document_name=document.name if document else "Unknown document",
                document_version=version.version if version else 1,
                section=chunk.title,
                page_number=chunk.page_number,
                source_url=f"/api/v1/documents/{chunk.document_id}/content",
                snippet=chunk.content[:300],
            ),
            metadata=RetrievalResultMetadata(
                knowledge_base_id=chunk.knowledge_base_id,
                document_type=document_type,
                tags=chunk.meta.get("tags", []),
                entities=chunk.meta.get("entities", []),
                section_path=chunk.section_path,
                chunk_index=chunk.chunk_index,
            ),
        )
