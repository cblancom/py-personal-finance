from app.main import app


def test_import_routes_are_documented_in_openapi():
    paths = app.openapi()["paths"]

    assert "post" in paths["/api/importaciones"]
    assert "get" in paths["/api/importaciones/pendientes"]
    assert "get" in paths["/api/importaciones/pendientes/count"]
    assert "delete" in paths["/api/importaciones/pendientes"]
    assert "put" in paths["/api/importaciones/pendientes/{pending_id}"]
    assert "delete" in paths["/api/importaciones/pendientes/{pending_id}"]
    assert "post" in paths["/api/importaciones/pendientes/{pending_id}/contabilizar"]
