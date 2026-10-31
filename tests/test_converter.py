import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from converter import PdfPage, convert_pdf, safe_stem


class ConverterTests(unittest.TestCase):
    def test_conversion_creates_unique_markdown_without_overwriting(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "relatório.pdf"
            source.write_bytes(b"%PDF-example")
            folder = base / "saida"

            def fake_engine(stream):
                self.assertEqual(stream.read(5), b"%PDF-")
                return SimpleNamespace(markdown="# Relatório\n")

            first = convert_pdf(source, folder, fake_engine, ocr_mode="off")
            second = convert_pdf(source, folder, fake_engine, ocr_mode="off")
            self.assertIsNone(first.error)
            self.assertEqual(first.output.name, "relatório.md")
            self.assertEqual(second.output.name, "relatório-2.md")
            self.assertEqual(first.output.read_text(encoding="utf-8"), "# Relatório\n")

    def test_invalid_pdf_does_not_call_converter_or_create_folder(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "falso.pdf"
            source.write_bytes(b"not pdf")
            target = base / "saida"
            result = convert_pdf(source, target, lambda _: self.fail("converter should not run"), ocr_mode="off")
            self.assertIsNotNone(result.error)
            self.assertFalse(target.exists())

    def test_empty_extraction_has_warning(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "scan.pdf"
            source.write_bytes(b"%PDF-example")
            result = convert_pdf(source, base / "saida", lambda _: SimpleNamespace(markdown=""), ocr_mode="off")
            self.assertIsNotNone(result.warning)
            self.assertTrue(result.output.exists())

    def test_safe_stem(self):
        self.assertEqual(safe_stem("relatório final.pdf"), "relatório-final")
        self.assertEqual(safe_stem("CON.pdf"), "documento")

    def test_auto_ocr_only_scanned_pages_and_preserves_page_order(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "misto.pdf"
            source.write_bytes(b"%PDF-example")
            seen = []

            def fake_pages(_):
                yield PdfPage("Este é um parágrafo digital longo.", lambda: b"digital-page", lambda: self.fail("digital page rendered"))
                yield PdfPage("", lambda: self.fail("scanned page converted"), lambda: b"scanned-image")

            def fake_converter(stream):
                seen.append(stream.read())
                return SimpleNamespace(markdown="## Texto digital")

            def fake_ocr():
                return lambda image: ["Texto", "digitalizado"] if image == b"scanned-image" else []

            result = convert_pdf(source, base / "saida", fake_converter, pages=fake_pages, ocr_factory=fake_ocr)
            self.assertIsNone(result.error)
            self.assertEqual(result.ocr_pages, 1)
            self.assertEqual(seen, [b"digital-page"])
            self.assertLess(result.markdown.index("Texto digital"), result.markdown.index("Texto\ndigitalizado"))

    def test_force_ocr_all_pages(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "digital.pdf"
            source.write_bytes(b"%PDF-example")
            pages = lambda _: iter([PdfPage("Texto digital suficiente", lambda: self.fail("converter called"), lambda: b"image")])
            result = convert_pdf(source, base / "saida", lambda _: self.fail("converter called"), ocr_mode="force", pages=pages, ocr_factory=lambda: lambda _: ["Reconhecido"])
            self.assertEqual(result.ocr_pages, 1)
            self.assertIn("Reconhecido", result.markdown)


if __name__ == "__main__":
    unittest.main()

