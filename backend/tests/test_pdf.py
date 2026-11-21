import io

import pytest
from pypdf import PdfWriter

from app.config import MAX_PDF_BYTES
from app.errors import AppError
from app.learning.pdf import extract_text, store_pdf


def blank_pdf(password: str | None = None) -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    if password:
        writer.encrypt(password)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def test_rejects_large_file() -> None:
    with pytest.raises(AppError, match="10 MB"):
        extract_text(b"%PDF-" + b"0" * MAX_PDF_BYTES)


def test_rejects_non_pdf() -> None:
    with pytest.raises(AppError, match="not a PDF"):
        extract_text(b"hello world")


def test_rejects_encrypted_pdf() -> None:
    with pytest.raises(AppError, match="password"):
        extract_text(blank_pdf(password="secret"))


def test_rejects_pdf_without_text() -> None:
    with pytest.raises(AppError, match="No text"):
        extract_text(blank_pdf())


def test_stores_extracted_text(session, monkeypatch) -> None:
    monkeypatch.setattr("app.learning.pdf.extract_text", lambda data: ("Deadlock notes", 2))
    response = store_pdf(session, "notes.pdf", b"%PDF-")
    assert response.pages == 2
    assert session.pdf_texts[response.file_id] == ("notes.pdf", "Deadlock notes")
