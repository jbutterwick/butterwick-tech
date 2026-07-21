from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from scripts.verify_site import verify_site


class VerifySiteTests(TestCase):
    def _site(
        self,
        root: Path,
        *,
        canonical: str,
        stylesheet: str,
        og_image: str,
        extra_head: str = "",
    ) -> Path:
        public = root / "public"
        public.mkdir()
        (public / "site.css").write_text("body {}\n", encoding="utf-8")
        (public / "social.png").write_bytes(b"image")

        for route in ("projects", "resume"):
            target = public / route / "index.html"
            target.parent.mkdir()
            target.write_text(
                '<meta http-equiv="refresh" content="0; url=/">\n', encoding="utf-8"
            )

        (public / "index.html").write_text(
            f"""<!doctype html>
<html lang="en">
<head>
<title>Jordan Butterwick — Senior Software Engineer</title>
<meta name="description" content="Professional portfolio for Jordan Butterwick.">
<link rel="canonical" href="{canonical}">
<link rel="stylesheet" href="{stylesheet}">
{extra_head}
<meta property="og:title" content="Jordan Butterwick">
<meta property="og:type" content="website">
<meta property="og:url" content="https://butterwick.tech/">
<meta property="og:image" content="{og_image}">
<meta property="og:description" content="Senior Software Engineer">
</head>
<body>
<main><h1>Senior Software Engineer</h1>
<a href="/projects/">Projects</a>
<a href="/resume/">Résumé</a>
<a href="mailto:jordan@butterwick.tech">Contact</a>
</main>
</body>
</html>
""",
            encoding="utf-8",
        )
        return public

    def test_rejects_external_stylesheet(self) -> None:
        with TemporaryDirectory() as directory:
            public = self._site(
                Path(directory),
                canonical="https://butterwick.tech/",
                stylesheet="https://fonts.example/style.css",
                og_image="https://butterwick.tech/social.png",
            )

            errors = verify_site(public)

            self.assertTrue(any("external page resource" in error for error in errors))

    def test_rejects_canonical_that_does_not_match_page_url(self) -> None:
        with TemporaryDirectory() as directory:
            public = self._site(
                Path(directory),
                canonical="https://butterwick.tech/wrong/",
                stylesheet="/site.css",
                og_image="https://butterwick.tech/social.png",
            )

            errors = verify_site(public)

            self.assertTrue(any("canonical does not match page URL" in error for error in errors))

    def test_rejects_missing_open_graph_image(self) -> None:
        with TemporaryDirectory() as directory:
            public = self._site(
                Path(directory),
                canonical="https://butterwick.tech/",
                stylesheet="/site.css",
                og_image="https://butterwick.tech/missing.png",
            )

            errors = verify_site(public)

            self.assertTrue(any("og:image target does not exist" in error for error in errors))

    def test_rejects_external_script_source(self) -> None:
        with TemporaryDirectory() as directory:
            public = self._site(
                Path(directory),
                canonical="https://butterwick.tech/",
                stylesheet="/site.css",
                og_image="https://butterwick.tech/social.png",
                extra_head='<script src="https://scripts.example/app.js"></script>',
            )

            errors = verify_site(public)

            self.assertTrue(any("external page resource" in error for error in errors))

    def test_rejects_external_css_import(self) -> None:
        with TemporaryDirectory() as directory:
            public = self._site(
                Path(directory),
                canonical="https://butterwick.tech/",
                stylesheet="/site.css",
                og_image="https://butterwick.tech/social.png",
            )
            (public / "site.css").write_text(
                '@import url("https://fonts.example/font.css");\n', encoding="utf-8"
            )

            errors = verify_site(public)

            self.assertTrue(any("external CSS resource" in error for error in errors))

    def test_rejects_external_resource_on_noindex_page(self) -> None:
        with TemporaryDirectory() as directory:
            public = self._site(
                Path(directory),
                canonical="https://butterwick.tech/",
                stylesheet="/site.css",
                og_image="https://butterwick.tech/social.png",
            )
            private_page = public / "private" / "index.html"
            private_page.parent.mkdir()
            private_page.write_text(
                '<meta name="robots" content="noindex">\n'
                '<script src="https://scripts.example/private.js"></script>\n',
                encoding="utf-8",
            )

            errors = verify_site(public)

            self.assertTrue(any("private/index.html: external page resource" in error for error in errors))

    def test_rejects_base_element_that_changes_resource_resolution(self) -> None:
        with TemporaryDirectory() as directory:
            public = self._site(
                Path(directory),
                canonical="https://butterwick.tech/",
                stylesheet="/site.css",
                og_image="https://butterwick.tech/social.png",
                extra_head=(
                    '<base href="https://resources.example/">'
                    '<script src="local-decoy.js"></script>'
                ),
            )
            (public / "local-decoy.js").write_text("", encoding="utf-8")

            errors = verify_site(public)

            self.assertTrue(any("base element is not allowed" in error for error in errors))

    def test_rejects_iframe_srcdoc(self) -> None:
        with TemporaryDirectory() as directory:
            public = self._site(
                Path(directory),
                canonical="https://butterwick.tech/",
                stylesheet="/site.css",
                og_image="https://butterwick.tech/social.png",
                extra_head=(
                    '<iframe srcdoc="&lt;script src=\'https://scripts.example/app.js\'&gt;'
                    '&lt;/script&gt;"></iframe>'
                ),
            )

            errors = verify_site(public)

            self.assertTrue(any("iframe srcdoc is not allowed" in error for error in errors))

    def test_rejects_external_inline_svg_image(self) -> None:
        with TemporaryDirectory() as directory:
            public = self._site(
                Path(directory),
                canonical="https://butterwick.tech/",
                stylesheet="/site.css",
                og_image="https://butterwick.tech/social.png",
                extra_head='<svg><image href="https://images.example/photo.jpg"></image></svg>',
            )

            errors = verify_site(public)

            self.assertTrue(any("external page resource" in error for error in errors))

    def test_rejects_external_input_image(self) -> None:
        with TemporaryDirectory() as directory:
            public = self._site(
                Path(directory),
                canonical="https://butterwick.tech/",
                stylesheet="/site.css",
                og_image="https://butterwick.tech/social.png",
                extra_head='<input type="image" src="https://images.example/button.png">',
            )

            errors = verify_site(public)

            self.assertTrue(any("external page resource" in error for error in errors))

    def test_rejects_external_preload_imagesrcset(self) -> None:
        with TemporaryDirectory() as directory:
            public = self._site(
                Path(directory),
                canonical="https://butterwick.tech/",
                stylesheet="/site.css",
                og_image="https://butterwick.tech/social.png",
                extra_head=(
                    '<link rel="preload" as="image" '
                    'imagesrcset="https://images.example/photo.jpg 1x">'
                ),
            )

            errors = verify_site(public)

            self.assertTrue(any("external page resource" in error for error in errors))

    def test_rejects_escaped_css_resource_url(self) -> None:
        with TemporaryDirectory() as directory:
            public = self._site(
                Path(directory),
                canonical="https://butterwick.tech/",
                stylesheet="/site.css",
                og_image="https://butterwick.tech/social.png",
            )
            (public / "site.css").write_text(
                r'@import "\68ttps://fonts.example/font.css";' + "\n",
                encoding="utf-8",
            )

            errors = verify_site(public)

            self.assertTrue(any("escaped CSS resource" in error for error in errors))

    def test_rejects_data_first_srcset_with_external_candidate(self) -> None:
        with TemporaryDirectory() as directory:
            public = self._site(
                Path(directory),
                canonical="https://butterwick.tech/",
                stylesheet="/site.css",
                og_image="https://butterwick.tech/social.png",
                extra_head=(
                    '<img src="/social.png" '
                    'srcset="data:image/gif;base64,R0lGODlhAQABAIAAAAUEBA== 0.5x, '
                    'https://images.example/photo.jpg 1x" alt="Test">'
                ),
            )

            errors = verify_site(public)

            self.assertTrue(any("data URL in srcset is not allowed" in error for error in errors))
