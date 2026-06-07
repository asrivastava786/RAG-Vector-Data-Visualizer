from app.services.extraction_service import extract_text, validate_document_type


def test_extract_markdown_detects_heading_and_table() -> None:
    payload = b"# Policy\n\nEmployees can request leave.\n\n| Role | Access |\n| --- | --- |\n"

    extracted = extract_text("policy.md", "text/markdown", payload)

    assert "Employees can request leave" in extracted.text
    assert extracted.structure["kind"] == "markdown"
    assert extracted.structure["headings"] == [{"line": 1, "text": "Policy"}]
    assert extracted.structure["tables"] == [{"start_line": 5, "end_line": 6}]


def test_validate_document_type_accepts_pdf() -> None:
    validate_document_type("source.pdf", "application/pdf")
