"""PDF conversion and safe Markdown output paths."""

from __future__ import annotations

import re
import io
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator


@dataclass(frozen=True)
class ConversionResult:
    source: Path
    output: Path | None
    markdown: str = ""
    error: str | None = None
    warning: str | None = None
    ocr_pages: int = 0


@dataclass(frozen=True)
class PdfPage:
    text: str
    pdf_bytes: Callable[[], bytes]
    image_bytes: Callable[[], bytes]


def iter_pdf_pages(source: Path) -> Iterator[PdfPage]:
    """Yield one page at a time, keeping only the current page in memory."""
    import pymupdf

    document = pymupdf.open(source)
    try:
        for number in range(len(document)):
            page = document[number]

            def page_pdf(index=number):
                single = pymupdf.open()
                try:
                    single.insert_pdf(document, from_page=index, to_page=index)
                    return single.tobytes()
                finally:
                    single.close()

            def page_image(current=page):
                return current.get_pixmap(dpi=200, alpha=False).tobytes("png")

            yield PdfPage(page.get_text("text"), page_pdf, page_image)
    finally:
        document.close()


def make_ocr_reader() -> Callable[[bytes], list[str]]:
    from rapidocr import RapidOCR

    engine = RapidOCR(params={"Det.lang_type": "pt", "Rec.lang_type": "pt"})

    def recognize(image: bytes) -> list[str]:
        result = engine(image)
        return list(result.txts) if result.txts is not None else []

    return recognize


def extract_with_ocr(
    source: Path,
    convert_stream: Callable,
    mode: str,
    pages: Callable[[Path], Iterator[PdfPage]] = iter_pdf_pages,
    ocr_factory: Callable[[], Callable[[bytes], list[str]]] = make_ocr_reader,
) -> tuple[str, int, int]:
    """Keep page order while OCRing scanned pages and converting digital pages."""
    if mode not in {"auto", "force"}:
        raise ValueError("Modo de OCR inválido")
    chunks = []
    ocr_count = 0
    empty_count = 0
    recognize = None
    for number, page in enumerate(pages(source), start=1):
        use_ocr = mode == "force" or len(page.text.strip()) < 24
        if use_ocr:
            if recognize is None:
                recognize = ocr_factory()
            lines = recognize(page.image_bytes())
            content = "\n".join(str(line) for line in lines if str(line).strip()).strip()
            ocr_count += 1
            if not content:
                empty_count += 1
        else:
            content = convert_stream(io.BytesIO(page.pdf_bytes())).markdown or ""
        if content.strip():
            chunks.append(f"<!-- Página {number} -->\n\n{content.strip()}")
    return "\n\n".join(chunks) + ("\n" if chunks else ""), ocr_count, empty_count


def safe_stem(name: str) -> str:
    stem = Path(name).stem
    stem = re.sub(r"[^\w.-]+", "-", stem, flags=re.UNICODE).strip("._-")
    if not stem or stem.upper() in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}:
        stem = "documento"
    return stem[:100]


def convert_pdf(
    source: Path,
    output_dir: Path,
    make_converter: Callable | None = None,
    ocr_mode: str = "auto",
    pages: Callable[[Path], Iterator[PdfPage]] = iter_pdf_pages,
    ocr_factory: Callable[[], Callable[[bytes], list[str]]] = make_ocr_reader,
) -> ConversionResult:
    """Convert one user-chosen PDF and create a new .md without overwriting."""
    source = Path(source)
    output_dir = Path(output_dir)
    if source.suffix.lower() != ".pdf":
        return ConversionResult(source, None, error="O arquivo precisa ter extensão .pdf.")
    if ocr_mode not in {"off", "auto", "force"}:
        return ConversionResult(source, None, error="Modo de OCR inválido.")
    try:
        with source.open("rb") as pdf:
            if pdf.read(5) != b"%PDF-":
                return ConversionResult(source, None, error="O arquivo não parece ser um PDF válido.")
            pdf.seek(0)
            if make_converter is None:
                from markitdown import StreamInfo
                from markitdown.converters import PdfConverter

                # The input was already validated as PDF. Calling its converter
                # directly avoids Magika's format detection and bundled model.
                engine = PdfConverter()
                def convert(stream):
                    return engine.convert(stream, stream_info=StreamInfo(extension=".pdf", mimetype="application/pdf"))
            else:
                convert = make_converter
            if ocr_mode == "off":
                markdown = convert(pdf).markdown or ""
                ocr_count = 0
                empty_count = 0
            else:
                markdown, ocr_count, empty_count = extract_with_ocr(source, convert, ocr_mode, pages, ocr_factory)

        output_dir.mkdir(parents=True, exist_ok=True)
        stem = safe_stem(source.name)
        for index in range(1, 10001):
            name = f"{stem}.md" if index == 1 else f"{stem}-{index}.md"
            target = output_dir / name
            try:
                with target.open("x", encoding="utf-8", newline="\n") as handle:
                    handle.write(markdown)
                break
            except FileExistsError:
                continue
        else:
            return ConversionResult(source, None, error="Não há nome livre para salvar o Markdown.")

        return ConversionResult(
            source,
            target,
            markdown,
            warning=(
                f"OCR não encontrou texto em {empty_count} página(s)." if empty_count
                else "Nenhum texto foi extraído. Tente forçar OCR em todas as páginas." if not markdown.strip()
                else None
            ),
            ocr_pages=ocr_count,
        )
    except Exception as exc:
        detail = str(exc).strip()
        message = f"Falha na conversão: {type(exc).__name__}"
        if detail:
            message += f": {detail[:300]}"
        return ConversionResult(source, None, error=message)

