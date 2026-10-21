from app.main import app


def test_expense_routes_are_documented_in_openapi():
    paths = app.openapi()["paths"]

    assert "/api/gastos" in paths
    assert "/api/gastos/{expense_id}" in paths
    assert "post" in paths["/api/gastos"]
    assert "get" in paths["/api/gastos"]
    assert "get" in paths["/api/gastos/{expense_id}"]
    assert "put" in paths["/api/gastos/{expense_id}"]
    assert "delete" in paths["/api/gastos/{expense_id}"]
