from app.main import app


def test_income_routes_are_documented_in_openapi():
    paths = app.openapi()["paths"]

    assert "/api/ingresos" in paths
    assert "/api/ingresos/{income_id}" in paths
    assert "post" in paths["/api/ingresos"]
    assert "get" in paths["/api/ingresos"]
    assert "get" in paths["/api/ingresos/{income_id}"]
    assert "put" in paths["/api/ingresos/{income_id}"]
    assert "delete" in paths["/api/ingresos/{income_id}"]
