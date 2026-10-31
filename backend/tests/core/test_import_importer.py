from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session

from app.services.imports import importer
from app.services.imports.errors import ImportFileError
from app.services.imports.importer import import_file


def test_import_file_rejects_content_over_the_limit(monkeypatch):
    monkeypatch.setattr(importer, "MAX_IMPORT_BYTES", 10)
    db = Mock(spec=Session)

    with pytest.raises(ImportFileError) as caught:
        import_file(
            db,
            filename="movimientos.csv",
            content_type="text/csv",
            content=b"x" * 11,
            movement_type="INGRESO",
        )

    assert caught.value.status_code == 413
