#!/usr/bin/env python3
"""Verify résumé source data, rendered HTML, routes, and PDF text order."""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from html.parser import HTMLParser
from pathlib import Path

EXPECTED_COMPANIES = (
    "Tresco Consoles",
    "Docupet",
    "Statflo",
    "Helcim",
)
EXPECTED_ROLE_COUNT = 4
EXPECTED_BULLET_COUNT = 12
MAX_FEATURED_SKILLS = 16


class ResumeHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: list[tuple[str, dict[str, str | None]]] = []
        self.text_parts: list[str] = []
        self.h1_count = 0
        self.main_count = 0
        self.hrefs: list[str] = []
        self.external_scripts: list[str] = []
        self.forbidden: list[str] = []
        self.role_count = 0

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        attributes = dict(attrs)
        self.tags.append((tag, attributes))
        if tag == "h1":
            self.h1_count += 1
        elif tag == "main":
            self.main_count += 1
        elif tag == "a" and attributes.get("href"):
            self.hrefs.append(attributes["href"] or "")
        elif tag == "script" and attributes.get("src"):
            source = attributes["src"] or ""
            if source.startswith(("http://", "https://", "//")):
                self.external_scripts.append(source)

        classes = set((attributes.get("class") or "").split())
        if tag in {"table", "i"}:
            self.forbidden.append(f"<{tag}>")
        if "grid" in classes or any(name.startswith("grid-") for name in classes):
            self.forbidden.append(f"grid class on <{tag}>")
        if "resume-role" in classes:
            self.role_count += 1

    def handle_data(self, data: str) -> None:
        stripped = " ".join(data.split())
        if stripped:
            self.text_parts.append(stripped)

    @property
    def text(self) -> str:
        return " ".join(self.text_parts)


def parse_html(path: Path) -> ResumeHTMLParser:
    parser = ResumeHTMLParser()
    parser.feed(path.read_text(encoding="utf-8"))
    return parser


def load_resume_data(path: Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def verify_phone(identity: dict) -> list[str]:
    errors: list[str] = []
    display = str(identity.get("phone_display", ""))
    href = str(identity.get("phone_href", ""))
    if re.fullmatch(r"\+[1-9][0-9]{7,14}", href) is None:
        errors.append("identity.phone_href must be a valid E.164 number")
        return errors

    display_digits = "".join(character for character in display if character.isdigit())
    if href[1:] != display_digits:
        errors.append("identity.phone_href must match the digits in identity.phone_display")
    return errors


def verify_data(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"Missing résumé data: {path}"]

    data = load_resume_data(path)
    identity = data.get("identity", {})
    profile = data.get("profile", {})
    experience = data.get("experience", [])
    skills = data.get("skills", [])
    education = data.get("education", [])

    for field in (
        "name",
        "professional_title",
        "email",
        "phone_display",
        "phone_href",
        "location",
        "website",
        "github",
        "linkedin",
    ):
        if not identity.get(field):
            errors.append(f"identity.{field} is required")
    errors.extend(verify_phone(identity))

    if profile.get("summary_status") != "needs-copy-review":
        errors.append("profile.summary_status must remain needs-copy-review")
    if len(profile.get("summary_seed", [])) != 2:
        errors.append("profile.summary_seed must preserve two existing statements")
    if len(profile.get("logistics", [])) != 2:
        errors.append("profile.logistics must preserve two existing statements")

    if len(experience) != EXPECTED_ROLE_COUNT:
        errors.append(
            f"Expected {EXPECTED_ROLE_COUNT} experience roles, found {len(experience)}"
        )
    companies = tuple(role.get("company") for role in experience)
    if companies != EXPECTED_COMPANIES:
        errors.append(
            f"Experience companies/order changed: expected {EXPECTED_COMPANIES}, found {companies}"
        )
    bullet_count = sum(len(role.get("bullets", [])) for role in experience)
    if bullet_count != EXPECTED_BULLET_COUNT:
        errors.append(
            f"Expected {EXPECTED_BULLET_COUNT} experience bullets, found {bullet_count}"
        )
    for role in experience:
        for field in ("company", "title", "start", "end", "location", "bullets"):
            if field not in role or role[field] in (None, "", []):
                errors.append(f"Experience role is missing {field}: {role.get('company')}")

    featured = [skill for skill in skills if skill.get("featured")]
    if not featured:
        errors.append("At least one skill must be featured")
    if len(featured) > MAX_FEATURED_SKILLS:
        errors.append(
            f"Featured skill inventory is too large: {len(featured)} > {MAX_FEATURED_SKILLS}"
        )
    for skill in skills:
        if not skill.get("name") or not skill.get("category"):
            errors.append(f"Skill is missing name/category: {skill}")
        if "featured" not in skill:
            errors.append(f"Skill is missing featured flag: {skill.get('name')}")

    if len(education) != 1:
        errors.append(f"Expected one education entry, found {len(education)}")
    elif education[0].get("credential_status") != "needs-confirmation":
        errors.append("Education credential_status must remain needs-confirmation")

    return errors


def verify_rendered(root: Path) -> list[str]:
    errors: list[str] = []
    web_path = root / "resume" / "index.html"
    application_path = root / "resume" / "application" / "index.html"
    alias_path = root / "resume.html"

    for label, path in (("web", web_path), ("application", application_path)):
        if not path.exists():
            errors.append(f"Missing {label} résumé page: {path}")
    if not alias_path.exists():
        errors.append(f"Missing legacy résumé alias: {alias_path}")
    if errors:
        return errors

    web = parse_html(web_path)
    application = parse_html(application_path)

    for label, parser in (("web", web), ("application", application)):
        if parser.h1_count != 1:
            errors.append(f"{label} résumé must have one h1, found {parser.h1_count}")
        if parser.main_count != 1:
            errors.append(f"{label} résumé must have one main, found {parser.main_count}")
        if parser.role_count != EXPECTED_ROLE_COUNT:
            errors.append(
                f"{label} résumé must render {EXPECTED_ROLE_COUNT} roles, found {parser.role_count}"
            )
        for company in EXPECTED_COMPANIES:
            if parser.text.count(company) != 1:
                errors.append(
                    f"{label} résumé must render {company} once, found {parser.text.count(company)}"
                )

    if application.forbidden:
        errors.append(
            "Application résumé contains ATS-hostile markup: "
            + ", ".join(application.forbidden)
        )
    if application.external_scripts:
        errors.append(
            "Application résumé loads external scripts: "
            + ", ".join(application.external_scripts)
        )
    if "tel:+15878305974" not in application.hrefs:
        errors.append("Application résumé has an invalid or missing normalized tel link")

    order = (
        "Jordan Butterwick",
        "Senior Software Engineer",
        "jordan@butterwick.tech",
        "Profile",
        "Experience",
        "Tresco Consoles",
        "Docupet",
        "Statflo",
        "Helcim",
        "Skills",
        "Education",
    )
    errors.extend(verify_text_order(application.text, order, "Application HTML"))

    return errors


def verify_text_order(text: str, ordered_terms: tuple[str, ...], label: str) -> list[str]:
    errors: list[str] = []
    searchable_text = text.casefold()
    previous_index = -1
    for term in ordered_terms:
        index = searchable_text.find(term.casefold())
        if index == -1:
            errors.append(f"{label} is missing expected text: {term}")
        elif index <= previous_index:
            errors.append(f"{label} has incorrect reading order near: {term}")
        previous_index = max(previous_index, index)
    return errors


def verify_pdf_text(path: Path) -> list[str]:
    if not path.exists():
        return [f"Missing PDF text extraction: {path}"]
    raw_text = path.read_text(encoding="utf-8", errors="replace")
    text = " ".join(raw_text.split())
    order = (
        "Jordan Butterwick",
        "Senior Software Engineer",
        "jordan@butterwick.tech",
        "Profile",
        "Experience",
        "Tresco Consoles",
        "Docupet",
        "Statflo",
        "Helcim",
        "Skills",
        "Education",
    )
    errors = verify_text_order(text, order, "Application PDF")
    for page in raw_text.split("\f"):
        folded_page = page.casefold()
        if "education" in folded_page:
            if "southern alberta institute of technology" not in folded_page:
                errors.append(
                    "Application PDF places the Education heading on a different page from its content"
                )
            break
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path("public"))
    parser.add_argument("--data-only", type=Path)
    parser.add_argument("--data", type=Path, default=Path("data/resume.toml"))
    parser.add_argument("--pdf-text", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    errors = verify_data(args.data_only or args.data)
    if not args.data_only:
        errors.extend(verify_rendered(args.root))
        if args.pdf_text:
            errors.extend(verify_pdf_text(args.pdf_text))

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1

    scope = "résumé data" if args.data_only else "résumé data and rendered output"
    print(f"PASS: verified {scope}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
