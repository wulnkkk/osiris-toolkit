"""Issue reporter: collects, filters, and formats validation issues."""

from dataclasses import dataclass, field
from enum import Enum


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    rule_id: str
    severity: Severity
    message: str
    section: str | None = None
    line: int | None = None
    suggestion: str | None = None

    def format(self) -> str:
        loc = ""
        if self.section:
            loc += f" [{self.section}]"
        if self.line:
            loc += f" line {self.line}"
        msg = f"{self.severity.value}: [{self.rule_id}]{loc} {self.message}"
        if self.suggestion:
            msg += f" ({self.suggestion})"
        return msg


@dataclass
class IssueReport:
    issues: list[ValidationIssue] = field(default_factory=list)

    def add(self, issue: ValidationIssue):
        self.issues.append(issue)

    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.ERROR]

    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.WARNING]

    def infos(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == Severity.INFO]

    def has_errors(self) -> bool:
        return any(i.severity == Severity.ERROR for i in self.issues)

    def format_all(self) -> list[str]:
        return [i.format() for i in self.issues]

    def summary(self) -> str:
        n_err = len(self.errors())
        n_warn = len(self.warnings())
        n_info = len(self.infos())
        parts = []
        if n_err:
            parts.append(f"{n_err} error(s)")
        if n_warn:
            parts.append(f"{n_warn} warning(s)")
        if n_info:
            parts.append(f"{n_info} info(s)")
        if not parts:
            return "No issues found."
        return ", ".join(parts)
