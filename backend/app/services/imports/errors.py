from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationIssue:
    field: str
    message: str


class ImportFileError(ValueError):
    def __init__(self, message: str, issues: tuple[ValidationIssue, ...] = ()) -> None:
        super().__init__(message)
        self.issues = issues
