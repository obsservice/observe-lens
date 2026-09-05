import pytest

from observelens_agent.agent.graph import build_agent_graph
from observelens_agent.agent.nodes.answer_node import create_answer_node
from observelens_agent.agent.nodes.rag_node import create_rag_node
from observelens_agent.agent.state.state import AgentState


class FakeKnowledgeClient:
    def __init__(self) -> None:
        self.requests: list[tuple[str, str | None, str | None]] = []

    async def retrieve_architecture(
        self, query: str, entity_type: str | None, entity_name: str | None
    ) -> list[dict[str, object]]:
        self.requests.append((query, entity_type, entity_name))
        return [
            {
                "content": "orders-api depends on orders-db.",
                "citation": {"document_name": "orders architecture"},
            }
        ]


class FakeAnswerLLM:
    def __init__(self) -> None:
        self.requests: list[tuple[str, list[dict[str, object]]]] = []

    async def answer(self, question: str, contexts: list[dict[str, object]]) -> str:
        self.requests.append((question, contexts))
        return "orders-api 依赖 orders-db。"


@pytest.mark.asyncio
async def test_graph_routes_general_requests_to_qa_subgraph() -> None:
    knowledge = FakeKnowledgeClient()
    graph = build_agent_graph(knowledge, None, None).compile()

    state = await graph.ainvoke({"msg": "解释一下服务依赖关系"})

    assert state["intent_type"] == "qa"
    assert knowledge.requests == [("解释一下服务依赖关系", None, None)]
    assert state["rag_contexts"]
    assert state["msg"] == "暂时无法生成回答，请检查 LLM 配置或稍后重试。"


@pytest.mark.asyncio
async def test_rag_and_answer_nodes_can_be_composed_by_any_graph() -> None:
    knowledge = FakeKnowledgeClient()
    answer_llm = FakeAnswerLLM()
    state = AgentState(
        msg="orders-api 的依赖是什么？",
        entity="service:orders-api",
    )

    state = await create_rag_node(knowledge)(state)
    state = await create_answer_node(answer_llm)(state)

    assert knowledge.requests == [("orders-api 的依赖是什么？", "service", "orders-api")]
    assert answer_llm.requests == [
        (
            "orders-api 的依赖是什么？",
            [
                {
                    "content": "orders-api depends on orders-db.",
                    "citation": {"document_name": "orders architecture"},
                }
            ],
        )
    ]
    assert state.msg == "orders-api 依赖 orders-db。"
