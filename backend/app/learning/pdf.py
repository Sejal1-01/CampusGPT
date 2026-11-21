import io
import secrets

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.config import MAX_PDF_BYTES, MAX_PDF_TEXT_CHARS
from app.errors import AppError
from app.schemas import PdfUploadResponse
from app.sessions import Session

PDF_MAGIC = b"%PDF-"


def _reject(code: str, message: str) -> AppError:
    return AppError(code, message, 400)


def extract_text(data: bytes) -> tuple[str, int]:
    if len(data) > MAX_PDF_BYTES:
        raise _reject("pdf_too_large", "The PDF is larger than 10 MB.")
    if not data.startswith(PDF_MAGIC):
        raise _reject("not_pdf", "That file is not a PDF.")
    try:
        reader = PdfReader(io.BytesIO(data))
    except PdfReadError as error:
        raise _reject("not_pdf", "The PDF could not be read.") from error
    if reader.is_encrypted:
        raise _reject("pdf_encrypted", "The PDF is password-protected. Upload an unlocked copy.")
    text = "\n".join((page.extract_text() or "") for page in reader.pages).strip()
    if not text:
        raise _reject("pdf_no_text", "No text found in the PDF. Scanned PDFs are not supported.")
    return text[:MAX_PDF_TEXT_CHARS], len(reader.pages)


def store_pdf(session: Session, filename: str, data: bytes) -> PdfUploadResponse:
    text, pages = extract_text(data)
    file_id = f"p_{secrets.token_hex(4)}"
    session.pdf_texts[file_id] = (filename, text)
    return PdfUploadResponse(file_id=file_id, filename=filename, pages=pages, characters=len(text))


def pdf_text(session: Session, file_id: str) -> str | None:
    entry = session.pdf_texts.get(file_id)
    return entry[1] if entry else None
