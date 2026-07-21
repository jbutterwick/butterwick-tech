import importlib.util
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch


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

    def test_chrome_timeout_terminates_before_reading_output(self):
        module = self.load_module()
        process = Mock(pid=12345)
        process.poll.return_value = None
        process.wait.return_value = 0

        with TemporaryDirectory() as directory:
            pdf_path = Path(directory) / "resume.pdf"
            profile_path = Path(directory) / "profile"
            with (
                patch.object(module, "PDF_PATH", pdf_path),
                patch.object(module.subprocess, "Popen", return_value=process) as popen,
                patch.object(module.time, "monotonic", side_effect=[0, 46]),
                patch.object(module.os, "killpg") as killpg,
            ):
                with self.assertRaisesRegex(RuntimeError, "did not produce"):
                    module.export_with_chrome("chrome", "http://127.0.0.1/resume/", profile_path)

        self.assertIsNot(popen.call_args.kwargs["stdout"], module.subprocess.PIPE)
        killpg.assert_called_once_with(process.pid, module.signal.SIGTERM)


if __name__ == "__main__":
    unittest.main()
