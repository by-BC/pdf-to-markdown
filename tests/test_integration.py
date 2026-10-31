"""Real conversion smoke test, skipped when optional packages are unavailable."""

import importlib.util
import tempfile
import unittest
from pathlib import Path

from converter import convert_pdf


@unittest.skipUnless(
    all(importlib.util.find_spec(name) for name in ("pymupdf", "rapidocr", "onnxruntime", "markitdown")),
    "OCR dependencies are not installed",
)
class RealOcrTests(unittest.TestCase):
    def test_mixed_pdf_uses_local_ocr(self):
        import pymupdf

        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "misto.pdf"

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
            self.assertIsNone(result.error, result.error)
            self.assertEqual(result.ocr_pages, 1)
            self.assertTrue(result.output.is_file())
            self.assertIn("Texto digital selecionavel", result.markdown)
            self.assertIn("OCR", result.markdown.upper())


if __name__ == "__main__":
    unittest.main()

