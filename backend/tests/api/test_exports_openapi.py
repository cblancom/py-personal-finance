from app.main import app


def test_export_routes_are_documented_in_openapi():
    paths = app.openapi()["paths"]

    for path in ("/api/exportaciones/ingresos", "/api/exportaciones/gastos"):
        assert "get" in paths[path]
        parameters = paths[path]["get"]["parameters"]
        formato = next(parameter for parameter in parameters if parameter["name"] == "formato")
        assert formato["in"] == "query"
        assert formato["required"] is True
        assert formato["schema"]["enum"] == ["csv", "xlsx"]
