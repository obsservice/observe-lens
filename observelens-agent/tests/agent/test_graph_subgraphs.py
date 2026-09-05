import pytest

from observelens_agent.agent.graph import build_agent_graph


@pytest.mark.asyncio
async def test_graph_routes_general_requests_to_qa_subgraph() -> None:
    graph = build_agent_graph(None, None, None).compile()

    state = await graph.ainvoke({"msg": "解释一下服务依赖关系"})

    assert state["intent_type"] == "qa"
    assert state["msg"] == "Hi, 解释一下服务依赖关系"
