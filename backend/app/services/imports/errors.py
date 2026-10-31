from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationIssue:
    field: str
    message: str


class ImportFileError(ValueError):
    def __init__(
        self,
        message: str,
        issues: tuple[ValidationIssue, ...] = (),
        status_code: int = 422,
    ) -> None:
        super().__init__(message)
        self.issues = issues
        self.status_code = status_code


class PendingRowNotFound(ValueError):
    pass


class PendingRowConflict(ValueError):
    pass


class PendingRowInvalid(ValueError):
    def __init__(self, issues: tuple[ValidationIssue, ...]) -> None:
        super().__init__("El pendiente todavía tiene errores de validación.")
        self.issues = issues
