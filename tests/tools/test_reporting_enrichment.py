from strix.telemetry.tracer import Tracer


def test_report_includes_cvss_and_refs() -> None:
    tracer = Tracer("test-run")
    tracer.add_vulnerability_report(
        title="Test vuln",
        content="Issue details",
        severity="high",
        cvss_score=7.5,
        references=["CWE-79", "OWASP-A01"],
        fix_recommendation="Sanitize inputs",
        cwe=["CWE-79"],
    )

    report = tracer.vulnerability_reports[0]
    assert report["cvss_score"] == 7.5
    assert "CWE-79" in report["references"]
