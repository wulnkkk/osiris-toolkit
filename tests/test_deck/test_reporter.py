"""Tests for deck.reporter — IssueReport and Severity."""

from osiris_toolkit.deck.reporter import IssueReport, Severity, ValidationIssue


class TestSeverity:
    def test_enum_members_exist(self):
        assert Severity.ERROR is not None
        assert Severity.WARNING is not None
        assert Severity.INFO is not None

    def test_enum_is_enum(self):
        import enum
        assert isinstance(Severity.ERROR, enum.Enum)


class TestValidationIssue:
    def test_full_issue(self):
        issue = ValidationIssue(
            rule_id="V-TEST-001",
            severity=Severity.ERROR,
            message="Test error",
            section="simulation",
            line=5,
            suggestion="Fix it",
        )
        assert issue.rule_id == "V-TEST-001"
        assert issue.severity == Severity.ERROR
        assert issue.section == "simulation"
        assert issue.line == 5

    def test_format(self):
        issue = ValidationIssue(
            rule_id="V-TEST-001",
            severity=Severity.ERROR,
            message="Test error",
            section="simulation",
            line=5,
        )
        formatted = issue.format()
        assert "V-TEST-001" in formatted
        assert "Test error" in formatted

    def test_minimal_issue(self):
        issue = ValidationIssue(rule_id="X", severity=Severity.INFO, message="info")
        assert issue.section is None
        assert issue.line is None


class TestIssueReport:
    def test_empty_report(self):
        report = IssueReport()
        assert len(report.issues) == 0
        assert not report.has_errors()

    def test_add_error(self):
        report = IssueReport()
        report.add(ValidationIssue(rule_id="E1", severity=Severity.ERROR, message="err"))
        assert report.has_errors()
        assert len(report.errors()) == 1

    def test_add_warning(self):
        report = IssueReport()
        report.add(ValidationIssue(rule_id="W1", severity=Severity.WARNING, message="warn"))
        assert not report.has_errors()
        assert len(report.warnings()) == 1

    def test_add_info(self):
        report = IssueReport()
        report.add(ValidationIssue(rule_id="I1", severity=Severity.INFO, message="info"))
        assert len(report.infos()) == 1

    def test_errors_filter(self):
        report = IssueReport()
        report.add(ValidationIssue(rule_id="E1", severity=Severity.ERROR, message="e"))
        report.add(ValidationIssue(rule_id="W1", severity=Severity.WARNING, message="w"))
        assert len(report.errors()) == 1

    def test_summary_with_issues(self):
        report = IssueReport()
        report.add(ValidationIssue(rule_id="E1", severity=Severity.ERROR, message="e"))
        report.add(ValidationIssue(rule_id="W1", severity=Severity.WARNING, message="w"))
        s = report.summary()
        assert "1 error" in s.lower()
        assert "1 warning" in s.lower()

    def test_summary_no_issues(self):
        report = IssueReport()
        assert "no issue" in report.summary().lower()

    def test_format_all(self):
        report = IssueReport()
        report.add(ValidationIssue(rule_id="E1", severity=Severity.ERROR, message="err"))
        lines = report.format_all()
        assert len(lines) == 1
        assert "E1" in lines[0]
