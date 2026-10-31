from app.main import app


def test_charts_route_is_documented_in_openapi():
    paths = app.openapi()["paths"]

    assert "get" in paths["/api/graficos/gastos-mensuales"]
