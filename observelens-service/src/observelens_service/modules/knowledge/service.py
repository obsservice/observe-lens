from observelens_service.clients.knowledge_base import KnowledgeBaseClient
from observelens_service.modules.knowledge.schemas import (
    KnowledgeFilePage,
    KnowledgeFileResponse,
    KnowledgeFileStatusResponse,
)


class KnowledgeService:
    def __init__(self, client: KnowledgeBaseClient) -> None:
        self._client = client

    async def list_files(
        self, page: int, page_size: int, keyword: str | None, file_type: str | None
    ) -> KnowledgeFilePage:
        response = await self._client.list_files(
            {"page": page, "page_size": page_size, "keyword": keyword, "file_type": file_type}
        )
        return KnowledgeFilePage.model_validate(response)

    async def get_file(self, file_id: str) -> KnowledgeFileResponse:
        return KnowledgeFileResponse.model_validate(await self._client.get_file(file_id))

    async def upload(
        self, file_name: str, content_type: str, content: bytes
    ) -> KnowledgeFileResponse:
        return KnowledgeFileResponse.model_validate(
            await self._client.upload(file_name, content_type, content)
        )

    async def delete(self, file_id: str) -> None:
        await self._client.delete_file(file_id)

    async def status(self, file_id: str) -> KnowledgeFileStatusResponse:
        return KnowledgeFileStatusResponse.model_validate(await self._client.get_status(file_id))

    async def reindex(self, file_id: str) -> KnowledgeFileStatusResponse:
        return KnowledgeFileStatusResponse.model_validate(await self._client.reindex(file_id))

    async def file_types(self) -> list[dict[str, str]]:
        return await self._client.file_types()

    async def index_statuses(self) -> list[dict[str, str]]:
        return await self._client.index_statuses()
