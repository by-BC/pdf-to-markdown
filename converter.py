"""PDF conversion and safe Markdown output paths."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class ConversionResult:
    source: Path
    output: Path | None
    markdown: str = ""
    error: str | None = None
    warning: str | None = None


def safe_stem(name: str) -> str:
    stem = Path(name).stem
    stem = re.sub(r"[^\w.-]+", "-", stem, flags=re.UNICODE).strip("._-")
    if not stem or stem.upper() in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}:
        stem = "documento"
    return stem[:100]


def convert_pdf(source: Path, output_dir: Path, make_converter: Callable | None = None) -> ConversionResult:
    """Convert one user-chosen PDF and create a new .md without overwriting."""
    source = Path(source)
    output_dir = Path(output_dir)
    if source.suffix.lower() != ".pdf":
        return ConversionResult(source, None, error="O arquivo precisa ter extensão .pdf.")
    try:
        with source.open("rb") as pdf:
            if pdf.read(5) != b"%PDF-":
                return ConversionResult(source, None, error="O arquivo não parece ser um PDF válido.")
            pdf.seek(0)
            if make_converter is None:
                from markitdown import MarkItDown, StreamInfo

                engine = MarkItDown(enable_plugins=False)
                result = engine.convert_stream(pdf, stream_info=StreamInfo(extension=".pdf", mimetype="application/pdf"))
            else:
                result = make_converter(pdf)
            markdown = result.markdown or ""

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
            warning="Nenhum texto foi extraído. Este PDF pode precisar de OCR." if not markdown.strip() else None,
        )
    except Exception as exc:
        return ConversionResult(source, None, error=f"Falha na conversão: {type(exc).__name__}. Verifique se o PDF está íntegro e sem senha.")

