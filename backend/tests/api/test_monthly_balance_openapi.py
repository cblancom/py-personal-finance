from app.main import app


def test_monthly_balance_routes_are_documented_in_openapi():
    paths = app.openapi()["paths"]

    assert "get" in paths["/api/balance-mensual"]
    assert "get" in paths["/api/balance-mensual/periodos"]
    assert "put" in paths["/api/balance-mensual/asignaciones/{anio}/{mes}"]
