from collections.abc import AsyncIterator

import httpx


class AgentClient:
    def __init__(self, base_url: str, timeout_seconds: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = httpx.Timeout(timeout_seconds, connect=min(timeout_seconds, 5.0))

    async def stream_run(
        self, conversation_id: int, run_id: int, content: str
    ) -> AsyncIterator[str]:
        payload = {
            "conversation_id": str(conversation_id),
            "run_id": str(run_id),
            "content": content,
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            async with client.stream(
                "POST", f"{self._base_url}/runs:stream", json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        yield f"{line}\n"
                    else:
                        yield "\n"
