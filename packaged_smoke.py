"""End-to-end smoke check executed inside the packaged Windows executable."""

from __future__ import annotations

import tempfile
import traceback
from pathlib import Path

from converter import convert_pdf


def run(report_path: Path) -> int:
    try:
        import pymupdf

        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            source = base / "exemplo.pdf"

            image_document = pymupdf.open()
            image_page = image_document.new_page(width=595, height=842)
            image_page.insert_text((70, 150), "TEXTO OCR DE EXEMPLO", fontsize=28)
            image = image_page.get_pixmap(dpi=200).tobytes("png")
            image_document.close()

            document = pymupdf.open()
            digital = document.new_page(width=595, height=842)
            digital.insert_text((70, 150), "Texto digital selecionavel para teste", fontsize=18)
            scanned = document.new_page(width=595, height=842)
            scanned.insert_image(scanned.rect, stream=image)
            document.save(source)
            document.close()

            result = convert_pdf(source, base / "saida", ocr_mode="auto")
            if result.error or not result.output or result.ocr_pages != 1 or "OCR" not in result.markdown.upper():
                raise RuntimeError(result.error or "A conversão empacotada não produziu o resultado esperado.")

        report_path.write_text("OK: MarkItDown e OCR funcionaram dentro do executável.\n", encoding="utf-8")
        return 0
    except Exception:
        report_path.write_text(traceback.format_exc(), encoding="utf-8")
        return 1

