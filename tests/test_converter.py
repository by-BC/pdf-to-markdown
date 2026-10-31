import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from converter import convert_pdf, safe_stem


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

            first = convert_pdf(source, folder, fake_engine)
            second = convert_pdf(source, folder, fake_engine)
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
            result = convert_pdf(source, target, lambda _: self.fail("converter should not run"))
            self.assertIsNotNone(result.error)
            self.assertFalse(target.exists())

    def test_empty_extraction_has_warning(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "scan.pdf"
            source.write_bytes(b"%PDF-example")
            result = convert_pdf(source, base / "saida", lambda _: SimpleNamespace(markdown=""))
            self.assertIsNotNone(result.warning)
            self.assertTrue(result.output.exists())

    def test_safe_stem(self):
        self.assertEqual(safe_stem("relatório final.pdf"), "relatório-final")
        self.assertEqual(safe_stem("CON.pdf"), "documento")


if __name__ == "__main__":
    unittest.main()

