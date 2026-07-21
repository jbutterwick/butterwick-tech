import importlib.util
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("export_resume_pdf.py")


class ExportResumePDFTests(unittest.TestCase):
    def load_module(self):
        spec = importlib.util.spec_from_file_location("export_resume_pdf", SCRIPT_PATH)
        assert spec is not None
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module

    def test_parse_page_count_reads_pdfinfo_output(self):
        module = self.load_module()
        pdfinfo = "Title: Application Resume\nPages:           2\nPage size: A4\n"

        self.assertEqual(module.parse_page_count(pdfinfo), 2)

    def test_parse_page_count_rejects_missing_pages_field(self):
        module = self.load_module()

        with self.assertRaisesRegex(ValueError, "Pages"):
            module.parse_page_count("Page size: A4\n")


if __name__ == "__main__":
    unittest.main()
