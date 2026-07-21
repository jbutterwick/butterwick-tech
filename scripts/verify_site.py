#!/usr/bin/env python3
"""Verify built-site semantics, metadata, links, and required assets."""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

SITE_URL = "https://butterwick.tech/"
SITE_HOST = urlsplit(SITE_URL).netloc
SKIP_OG_BODY_CLASSES = {"resume-web-body", "application-resume-body"}
STALE_PHRASES = ("looking for work", "seeking permanent role")
CSS_IMPORT_RE = re.compile(
    r"@import\s+(?:url\(\s*)?[\"']?([^\"'\s);]+)", re.IGNORECASE
)
CSS_URL_RE = re.compile(r"url\(\s*[\"']?([^\"')]+)", re.IGNORECASE)


@dataclass
class Link:
    href: str
    text: list[str] = field(default_factory=list)

    @property
    def accessible_name(self) -> str:
        return " ".join("".join(self.text).split())


class DocumentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.in_title = False
        self.h1_parts: list[list[str]] = []
        self.h1_depth = 0
        self.lang = ""
        self.body_classes: set[str] = set()
        self.meta_names: dict[str, list[str]] = {}
        self.meta_properties: dict[str, list[str]] = {}
        self.canonicals: list[str] = []
        self.links: list[Link] = []
        self.link_stack: list[Link] = []
        self.resource_urls: list[str] = []
        self.resource_errors: list[str] = []
        self.inline_css: list[str] = []
        self.style_depth = 0
        self.nested_anchors = 0
        self.has_refresh = False

    @property
    def title(self) -> str:
        return " ".join("".join(self.title_parts).split())

    @property
    def h1_texts(self) -> list[str]:
        return [" ".join("".join(parts).split()) for parts in self.h1_parts]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if values.get("style", "").strip():
            self.inline_css.append(values["style"])
        if tag == "base":
            self.resource_errors.append("base element is not allowed")
        elif tag == "html":
            self.lang = values.get("lang", "").strip()
        elif tag == "body":
            self.body_classes = set(values.get("class", "").split())
        elif tag == "title":
            self.in_title = True
        elif tag == "h1":
            self.h1_parts.append([])
            self.h1_depth += 1
        elif tag == "meta":
            content = values.get("content", "").strip()
            name = values.get("name", "").strip().lower()
            prop = values.get("property", "").strip().lower()
            if name:
                self.meta_names.setdefault(name, []).append(content)
            if prop:
                self.meta_properties.setdefault(prop, []).append(content)
            if values.get("http-equiv", "").lower() == "refresh":
                self.has_refresh = True
        elif tag == "link":
            href = values.get("href", "").strip()
            rels = set(values.get("rel", "").lower().split())
            if "canonical" in rels:
                self.canonicals.append(href)
            if rels.intersection(
                {
                    "stylesheet",
                    "icon",
                    "manifest",
                    "apple-touch-icon",
                    "preload",
                    "modulepreload",
                    "prefetch",
                    "preconnect",
                    "dns-prefetch",
                }
            ):
                self.resource_urls.append(href)
            self._append_srcset(values.get("imagesrcset", ""))
        elif tag == "img":
            src = values.get("src", "").strip()
            if src:
                self.resource_urls.append(src)
            if self.link_stack:
                self.link_stack[-1].text.append(values.get("alt", ""))
            self._append_srcset(values.get("srcset", ""))
        elif tag == "style":
            self.style_depth += 1
        elif tag in {"script", "iframe", "embed", "audio", "video", "source", "track"}:
            src = values.get("src", "").strip()
            if src:
                self.resource_urls.append(src)
            href = values.get("href", "").strip()
            if href:
                self.resource_urls.append(href)
            if tag == "iframe" and values.get("srcdoc", "").strip():
                self.resource_errors.append("iframe srcdoc is not allowed")
            if tag == "video" and values.get("poster", "").strip():
                self.resource_urls.append(values["poster"].strip())
            self._append_srcset(values.get("srcset", ""))
        elif tag == "object":
            data = values.get("data", "").strip()
            if data:
                self.resource_urls.append(data)
        elif tag in {"image", "use", "feimage"}:
            href = values.get("href", values.get("xlink:href", "")).strip()
            if href:
                self.resource_urls.append(href)
        elif tag == "input" and values.get("type", "").lower() == "image":
            src = values.get("src", "").strip()
            if src:
                self.resource_urls.append(src)
        elif tag == "a":
            if self.link_stack:
                self.nested_anchors += 1
            link = Link(values.get("href", "").strip())
            self.links.append(link)
            self.link_stack.append(link)

    def _append_srcset(self, srcset: str) -> None:
        if not srcset.strip():
            return
        if "data:" in srcset.casefold():
            self.resource_errors.append("data URL in srcset is not allowed")
            return
        for candidate in srcset.split(","):
            url = candidate.strip().split(maxsplit=1)[0] if candidate.strip() else ""
            if url:
                self.resource_urls.append(url)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False
        elif tag == "h1" and self.h1_depth:
            self.h1_depth -= 1
        elif tag == "style" and self.style_depth:
            self.style_depth -= 1
        elif tag == "a" and self.link_stack:
            self.link_stack.pop()

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)
        if self.h1_depth and self.h1_parts:
            self.h1_parts[-1].append(data)
        if self.style_depth:
            self.inline_css.append(data)
        for link in self.link_stack:
            link.text.append(data)


def html_url(path: Path, public_dir: Path) -> str:
    relative = path.relative_to(public_dir).as_posix()
    if relative == "index.html":
        return SITE_URL
    if relative.endswith("/index.html"):
        return urljoin(SITE_URL, relative[: -len("index.html")])
    return urljoin(SITE_URL, relative)


def resolve_local_target(url: str, source_url: str, public_dir: Path) -> Path | None:
    if not url or url.startswith(("mailto:", "tel:", "data:", "javascript:")):
        return None
    parsed = urlsplit(urljoin(source_url, url))
    if parsed.scheme not in ("", "http", "https"):
        return None
    if parsed.netloc and parsed.netloc != SITE_HOST:
        return None
    path = unquote(parsed.path)
    if not path or path == "/":
        return public_dir / "index.html"
    candidate = public_dir / path.lstrip("/")
    if path.endswith("/"):
        return candidate / "index.html"
    if candidate.is_dir():
        return candidate / "index.html"
    return candidate


def parse_document(path: Path) -> DocumentParser:
    parser = DocumentParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


def css_resource_urls(css: str) -> set[str]:
    without_comments = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
    return {
        url.strip()
        for pattern in (CSS_IMPORT_RE, CSS_URL_RE)
        for url in pattern.findall(without_comments)
        if url.strip()
    }


def external_resource(url: str, source_url: str) -> bool:
    parsed = urlsplit(urljoin(source_url, url))
    return parsed.scheme in ("http", "https") and parsed.netloc != SITE_HOST


def verify_site(public_dir: Path) -> list[str]:
    errors: list[str] = []
    documents: dict[Path, DocumentParser] = {}
    indexable: dict[Path, DocumentParser] = {}

    for path in sorted(public_dir.rglob("*.html")):
        document = parse_document(path)
        documents[path] = document
        robots = " ".join(document.meta_names.get("robots", [])).lower()
        if path.name == "404.html" or document.has_refresh or "noindex" in robots:
            continue
        indexable[path] = document

    for path, document in documents.items():
        source_url = html_url(path, public_dir)
        label = path.relative_to(public_dir).as_posix()

        for resource_error in document.resource_errors:
            errors.append(f"{label}: {resource_error}")

        for resource_url in document.resource_urls:
            if external_resource(resource_url, source_url):
                errors.append(f"{label}: external page resource is not allowed: {resource_url}")
                continue
            target = resolve_local_target(resource_url, source_url, public_dir)
            if target is not None and not target.exists():
                errors.append(f"{label}: resource target does not exist: {resource_url}")

        for css in document.inline_css:
            for resource_url in css_resource_urls(css):
                if "\\" in resource_url:
                    errors.append(
                        f"{label}: escaped CSS resource URL is not allowed: {resource_url}"
                    )
                elif external_resource(resource_url, source_url):
                    errors.append(
                        f"{label}: external inline CSS resource is not allowed: {resource_url}"
                    )

    if not indexable:
        errors.append("No indexable HTML pages found")
        return errors

    for path, document in indexable.items():
        relative = path.relative_to(public_dir)
        source_url = html_url(path, public_dir)
        label = relative.as_posix()

        if not document.lang:
            errors.append(f"{label}: missing html lang")
        if not document.title:
            errors.append(f"{label}: missing title")
        descriptions = document.meta_names.get("description", [])
        if len(descriptions) != 1 or not descriptions[0].strip():
            errors.append(f"{label}: expected one nonempty meta description")
        if len(document.canonicals) != 1:
            errors.append(f"{label}: expected exactly one canonical link")
        elif document.canonicals[0] != source_url:
            errors.append(
                f"{label}: canonical does not match page URL: {document.canonicals[0]!r}"
            )
        if len(document.h1_texts) != 1 or not document.h1_texts[0]:
            errors.append(f"{label}: expected exactly one nonempty h1, found {document.h1_texts!r}")
        if document.nested_anchors:
            errors.append(f"{label}: contains {document.nested_anchors} nested anchor(s)")

        for link in document.links:
            if not link.href:
                errors.append(f"{label}: link is missing href")
            if not link.accessible_name:
                errors.append(f"{label}: link {link.href!r} has no accessible name")
            target = resolve_local_target(link.href, source_url, public_dir)
            if target is not None and not target.exists():
                errors.append(f"{label}: internal link target does not exist: {link.href}")

        if not document.body_classes.intersection(SKIP_OG_BODY_CLASSES):
            for prop in ("og:title", "og:type", "og:url", "og:image", "og:description"):
                values = document.meta_properties.get(prop, [])
                if len(values) != 1 or not values[0].strip():
                    errors.append(f"{label}: expected one nonempty {prop}")
            og_images = document.meta_properties.get("og:image", [])
            if len(og_images) == 1 and og_images[0].strip():
                parsed_image = urlsplit(urljoin(source_url, og_images[0]))
                if parsed_image.netloc != SITE_HOST:
                    errors.append(f"{label}: external og:image is not allowed: {og_images[0]}")
                else:
                    image_target = resolve_local_target(og_images[0], source_url, public_dir)
                    if image_target is not None and not image_target.exists():
                        errors.append(f"{label}: og:image target does not exist: {og_images[0]}")

        if "/about/me.jpg" in path.read_text(encoding="utf-8"):
            errors.append(f"{label}: references missing /about/me.jpg")

    title_counts = Counter(document.title for document in indexable.values() if document.title)
    for title, count in title_counts.items():
        if count > 1:
            errors.append(f"Duplicate page title used {count} times: {title!r}")

    description_counts = Counter(
        document.meta_names.get("description", [""])[0]
        for document in indexable.values()
        if document.meta_names.get("description")
    )
    for description, count in description_counts.items():
        if description and count > 1:
            errors.append(f"Duplicate meta description used {count} times: {description!r}")

    for css_path in sorted(public_dir.rglob("*.css")):
        css_url = html_url(css_path, public_dir)
        css_label = css_path.relative_to(public_dir).as_posix()
        for resource_url in css_resource_urls(css_path.read_text(encoding="utf-8")):
            if "\\" in resource_url:
                errors.append(
                    f"{css_label}: escaped CSS resource URL is not allowed: {resource_url}"
                )
            elif external_resource(resource_url, css_url):
                errors.append(
                    f"{css_label}: external CSS resource is not allowed: {resource_url}"
                )

    home_path = public_dir / "index.html"
    if home_path not in documents:
        errors.append("Homepage output is missing")
    else:
        home_text = home_path.read_text(encoding="utf-8").casefold()
        if "senior software engineer" not in home_text:
            errors.append("Homepage does not identify the professional role")
        home_links = {urlsplit(link.href).path for link in documents[home_path].links}
        for required_path in ("/projects/", "/resume/"):
            if required_path not in home_links:
                errors.append(f"Homepage is missing primary action {required_path}")
        if not any(link.href.startswith("mailto:") for link in documents[home_path].links):
            errors.append("Homepage is missing a contact email action")

    for relative in (Path("about/index.html"), Path("now/index.html")):
        path = public_dir / relative
        if path.exists():
            text = path.read_text(encoding="utf-8").casefold()
            for phrase in STALE_PHRASES:
                if phrase in text:
                    errors.append(f"{relative.as_posix()}: contains stale phrase {phrase!r}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("public_dir", nargs="?", type=Path, default=Path("public"))
    args = parser.parse_args()

    errors = verify_site(args.public_dir.resolve())
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        print(f"FAIL: site verification found {len(errors)} error(s)", file=sys.stderr)
        return 1

    print("PASS: verified site semantics, metadata, links, and assets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
