from app.main import app


def test_summary_route_is_documented_in_openapi():
    paths = app.openapi()["paths"]

    assert "/api/resumen" in paths
    assert "get" in paths["/api/resumen"]
