import tempfile
import unittest
from pathlib import Path

from scripts.verify_resume import verify_pdf_text, verify_phone, verify_text_order


class VerifyResumeTests(unittest.TestCase):
    def test_phone_validation_rejects_masked_href(self):
        errors = verify_phone(
            {
                "phone_display": "+1-(587)-830-5974",
                "phone_href": "+158****5974",
            }
        )

        self.assertIn("identity.phone_href must be a valid E.164 number", errors)

    def test_phone_validation_matches_displayed_digits(self):
        errors = verify_phone(
            {
                "phone_display": "+1-(587)-830-5974",
                "phone_href": "+15878305974",
            }
        )

        self.assertEqual(errors, [])

    def test_text_order_is_case_insensitive_for_printed_headings(self):
        errors = verify_text_order(
            "Jordan Butterwick PROFILE EXPERIENCE SKILLS EDUCATION",
            ("Jordan Butterwick", "Profile", "Experience", "Skills", "Education"),
            "PDF",
        )

        self.assertEqual(errors, [])

    def test_pdf_text_rejects_an_orphaned_education_heading(self):
        text = """Jordan Butterwick
Senior Software Engineer
jordan@butterwick.tech
PROFILE
EXPERIENCE
Tresco Consoles
Docupet
Statflo
Helcim
SKILLS
EDUCATION
\fSouthern Alberta Institute of Technology
"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "resume.txt"
            path.write_text(text, encoding="utf-8")

            errors = verify_pdf_text(path)

        self.assertIn(
            "Application PDF places the Education heading on a different page from its content",
            errors,
        )


if __name__ == "__main__":
    unittest.main()
