#!/usr/bin/env python3
"""Build, export, and validate the one-column application résumé PDF."""

from __future__ import annotations

import functools
import http.server
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIR = ROOT / "public"
PDF_PATH = ROOT / "static" / "downloads" / "Jordan-Butterwick-Resume.pdf"
PUBLIC_PDF_PATH = PUBLIC_DIR / "downloads" / PDF_PATH.name
MAX_PDF_BYTES = 2_500_000


class QuietRequestHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass


def parse_page_count(pdfinfo_output: str) -> int:
    for line in pdfinfo_output.splitlines():
        key, separator, value = line.partition(":")
        if separator and key.strip() == "Pages":
            return int(value.strip())
    raise ValueError("pdfinfo output did not contain a Pages field")


def find_chrome() -> str:
    configured = os.environ.get("CHROME_BIN")
    candidates = [
        configured,
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        shutil.which("google-chrome"),
        shutil.which("google-chrome-stable"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return candidate
    raise RuntimeError("Could not locate Chrome or Chromium; set CHROME_BIN")


def run_checked(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def export_with_chrome(chrome: str, url: str, profile_dir: Path) -> None:
    PDF_PATH.parent.mkdir(parents=True, exist_ok=True)
    PDF_PATH.unlink(missing_ok=True)
    command = [
        chrome,
        "--headless=new",
        "--disable-background-networking",
        "--disable-component-update",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--disable-sync",
        "--metrics-recording-only",
        "--no-sandbox",
        "--no-first-run",
        "--no-pdf-header-footer",
        f"--user-data-dir={profile_dir}",
        f"--print-to-pdf={PDF_PATH}",
        url,
    ]
    with tempfile.TemporaryFile(mode="w+t", encoding="utf-8") as chrome_log:
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            start_new_session=True,
            stdout=chrome_log,
            stderr=subprocess.STDOUT,
            text=True,
        )
        deadline = time.monotonic() + 45
        try:
            while time.monotonic() < deadline:
                if PDF_PATH.exists() and PDF_PATH.stat().st_size > 0:
                    time.sleep(0.5)
                    return
                if process.poll() is not None:
                    break
                time.sleep(0.25)
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=5)

        chrome_log.seek(0)
        raise RuntimeError(
            f"Chrome did not produce the résumé PDF.\n{chrome_log.read()}"
        )


def main() -> int:
    for command in ("npm", "zola", "pdfinfo", "pdftotext"):
        if shutil.which(command) is None:
            raise RuntimeError(f"Required command is not installed: {command}")

    build = run_checked(["npm", "run", "build:site"])
    print(build.stdout, end="")

    handler = functools.partial(QuietRequestHandler, directory=str(PUBLIC_DIR))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        port = server.server_address[1]
        with tempfile.TemporaryDirectory(prefix="resume-chrome-") as profile:
            export_with_chrome(
                find_chrome(),
                f"http://127.0.0.1:{port}/resume/application/",
                Path(profile),
            )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    with tempfile.TemporaryDirectory(prefix="resume-pdf-check-") as check_dir:
        extracted_text = Path(check_dir) / "resume.txt"
        run_checked(["pdftotext", "-layout", str(PDF_PATH), str(extracted_text)])
        pdfinfo = run_checked(["pdfinfo", str(PDF_PATH)]).stdout
        pages = parse_page_count(pdfinfo)
        if pages not in (1, 2):
            raise RuntimeError(f"Application résumé must be one or two pages, found {pages}")
        size = PDF_PATH.stat().st_size
        if size > MAX_PDF_BYTES:
            raise RuntimeError(
                f"Application résumé PDF is {size} bytes; limit is {MAX_PDF_BYTES}"
            )
        verification = run_checked(
            [
                sys.executable,
                "scripts/verify_resume.py",
                "public",
                "--pdf-text",
                str(extracted_text),
            ]
        )
        print(verification.stdout, end="")

    rebuild = run_checked(["npm", "run", "build:site"])
    print(rebuild.stdout, end="")
    if not PUBLIC_PDF_PATH.is_file():
        raise RuntimeError(f"Generated site is missing downloadable PDF: {PUBLIC_PDF_PATH}")

    print(
        f"PASS: exported {PDF_PATH.relative_to(ROOT)} "
        f"({pages} page{'s' if pages != 1 else ''}, {size} bytes)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
