"""Validate canonical URLs and internal links in the generated documentation."""

from html.parser import HTMLParser
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_BASE_URL = "https://omnia.readthedocs.io/en/contract-test/"


class PageParser(HTMLParser):
    """Collect canonical URLs, anchors, and links from an HTML page."""

    def __init__(self):
        super().__init__()
        self.anchors = set()
        self.canonical_urls = []
        self.links = []

    def handle_starttag(self, tag, attributes):
        values = dict(attributes)
        if values.get("id"):
            self.anchors.add(values["id"])
        if tag == "a" and values.get("name"):
            self.anchors.add(values["name"])
        if tag == "a" and values.get("href"):
            self.links.append(values["href"])
        if tag == "link" and values.get("rel") == "canonical":
            self.canonical_urls.append(values.get("href"))


class SiteIntegrityContractTests(unittest.TestCase):
    """Keep publication metadata and generated internal links valid."""

    @classmethod
    def setUpClass(cls):
        cls.temporary_directory = tempfile.TemporaryDirectory()
        cls.site_root = Path(cls.temporary_directory.name)
        environment = os.environ.copy()
        environment["READTHEDOCS_CANONICAL_URL"] = CANONICAL_BASE_URL
        subprocess.run(
            [
                sys.executable,
                "-m",
                "mkdocs",
                "build",
                "--clean",
                "--strict",
                "--site-dir",
                str(cls.site_root),
            ],
            cwd=REPOSITORY_ROOT,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )

        sitemap = ElementTree.parse(cls.site_root / "sitemap.xml")
        cls.sitemap_urls = [
            element.text
            for element in sitemap.iter()
            if element.tag.endswith("loc")
        ]
        cls.invalid_sitemap_urls = [
            url
            for url in cls.sitemap_urls
            if not url.startswith(CANONICAL_BASE_URL)
        ]
        cls.missing_sitemap_pages = []
        cls.pages = {}
        for url in cls.sitemap_urls:
            if not url.startswith(CANONICAL_BASE_URL):
                continue
            page_path = cls.site_root / unquote(
                url.removeprefix(CANONICAL_BASE_URL)
            )
            if not page_path.is_file():
                cls.missing_sitemap_pages.append(page_path)
                continue
            parser = PageParser()
            parser.feed(page_path.read_text(encoding="utf-8"))
            cls.pages[page_path.resolve()] = parser

    @classmethod
    def tearDownClass(cls):
        cls.temporary_directory.cleanup()

    def test_sitemap_and_canonical_urls_use_versioned_public_base(self):
        self.assertTrue(self.sitemap_urls)
        self.assertEqual([], self.invalid_sitemap_urls)
        self.assertEqual([], self.missing_sitemap_pages)

        expected_urls = {
            CANONICAL_BASE_URL
            + page.relative_to(self.site_root).as_posix()
            for page in self.pages
        }
        self.assertEqual(expected_urls, set(self.sitemap_urls))

        canonical_urls = []
        for page, parser in self.pages.items():
            expected_url = (
                CANONICAL_BASE_URL
                + page.relative_to(self.site_root).as_posix()
            )
            self.assertEqual([expected_url], parser.canonical_urls)
            canonical_urls.extend(parser.canonical_urls)

        self.assertNotIn("100.10.0.84", "\n".join(canonical_urls))

    def test_internal_link_targets_and_fragments_exist(self):
        failures = []
        canonical = urlsplit(CANONICAL_BASE_URL)

        for source_page, parser in self.pages.items():
            for href in parser.links:
                parsed = urlsplit(href)
                if parsed.scheme in {"mailto", "tel", "javascript", "data"}:
                    continue
                if parsed.netloc and parsed.netloc != canonical.netloc:
                    continue

                if parsed.netloc:
                    if not parsed.path.startswith(canonical.path):
                        continue
                    relative_path = parsed.path.removeprefix(canonical.path)
                    target = self.site_root / unquote(relative_path)
                elif parsed.path.startswith("/"):
                    if not parsed.path.startswith(canonical.path):
                        continue
                    relative_path = parsed.path.removeprefix(canonical.path)
                    target = self.site_root / unquote(relative_path)
                elif parsed.path:
                    target = source_page.parent / unquote(parsed.path)
                else:
                    target = source_page

                if str(target).endswith("/") or target.is_dir():
                    target /= "index.html"
                target = target.resolve()

                if not target.exists():
                    failures.append(
                        f"{source_page.relative_to(self.site_root)} -> "
                        f"{href} (missing target)"
                    )
                    continue

                if parsed.fragment and target.suffix == ".html":
                    target_parser = self.pages.get(target)
                    fragment = unquote(parsed.fragment)
                    if target_parser is None or fragment not in target_parser.anchors:
                        failures.append(
                            f"{source_page.relative_to(self.site_root)} -> "
                            f"{href} (missing fragment)"
                        )

        self.assertEqual([], failures, "\n".join(failures))


if __name__ == "__main__":
    unittest.main()
