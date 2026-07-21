from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from scripts.normalize_html import normalize_html_tree


class NormalizeHTMLTests(TestCase):
    def test_strips_trailing_whitespace_and_preserves_final_newline(self) -> None:
        with TemporaryDirectory() as directory:
            html_path = Path(directory) / "nested" / "index.html"
            html_path.parent.mkdir()
            html_path.write_text("<main>  \n  <p>Text</p>\t\n</main>", encoding="utf-8")

            changed = normalize_html_tree(Path(directory))

            self.assertEqual(changed, 1)
            self.assertEqual(
                html_path.read_text(encoding="utf-8"),
                "<main>\n  <p>Text</p>\n</main>\n",
            )

    def test_normalizes_generated_xml_feeds(self) -> None:
        with TemporaryDirectory() as directory:
            xml_path = Path(directory) / "feed.xml"
            xml_path.write_text("<feed>  \n</feed>\t\n", encoding="utf-8")

            changed = normalize_html_tree(Path(directory))

            self.assertEqual(changed, 1)
            self.assertEqual(xml_path.read_text(encoding="utf-8"), "<feed>\n</feed>\n")
