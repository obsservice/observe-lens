from observelens_knowledge_base.main import create_app


def test_app_openapi_contains_knowledge_base_paths() -> None:
    app = create_app()
    schema = app.openapi()

    assert schema["info"]["title"] == "ObserveLens Knowledge Base"
    assert "/api/v1/knowledge/knowledge-bases" in schema["paths"]
    assert "/api/v1/knowledge/retrieval/search" in schema["paths"]
    assert "/api/v1/knowledge/internal/v1/context/retrieve" in schema["paths"]
