from app.main import app


def test_api_version_is_1_2_0():
    assert app.version == "1.2.0"
