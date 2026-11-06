# Copyright 2026 Dell Inc. or its subsidiaries. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""Keep RHEL support statements consistent across documentation pages."""

from pathlib import Path
import re
import unittest


DOCS = Path(__file__).resolve().parents[1] / "docs"
MATRIX = DOCS / "Reference" / "SupportMatrix" / "operating_systems.md"
PREREQUISITES = DOCS / "GetStarted" / "prerequisites_checklist.md"
BASELINE_PAGES = [
    DOCS / "GetStarted" / "k8s_telemetry_only.md",
    DOCS / "GetStarted" / "full_deployment.md",
    DOCS / "GetStarted" / "buildstream_deployment.md",
    DOCS / "HowTo" / "build_stream" / "index.md",
    DOCS / "HowTo" / "image_build_manager" / "build_images.md",
]


def read(path):
    return path.read_text(encoding="utf-8")


class OsSupportDocumentationContracts(unittest.TestCase):
    def test_matrix_is_per_architecture(self):
        text = read(MATRIX)
        self.assertIn("| x86_64 | Validated | Validated |", text)
        self.assertIn("| aarch64 | Validated | Not supported |", text)

    def test_matrix_status_column_names_current_release(self):
        text = read(MATRIX)
        self.assertIn("2.3.0.0-rc3 status", text)
        self.assertNotIn("rc2 status", text)

    def test_prerequisites_allow_both_oim_versions(self):
        text = read(PREREQUISITES)
        self.assertNotIn("release --set=10.2`", text)
        self.assertNotIn("release --set=10.0`", text)
        self.assertIn("release --set=<10.0 or 10.2>", text)
        self.assertNotIn("10.2 is the documented validated OIM baseline", text)

    def test_baseline_statements_do_not_pin_a_single_minor_version(self):
        pattern = re.compile(
            r"validated (RC1 )?baseline[^.]*RHEL 10\.[02]\b(?! or)"
            r"|validated RHEL 10\.[02] baseline",
            re.IGNORECASE,
        )
        for page in BASELINE_PAGES:
            text = " ".join(read(page).split())
            self.assertIsNone(pattern.search(text), page)

    def test_catalog_paths_use_rhel_directory(self):
        for page in DOCS.rglob("*.md"):
            self.assertNotRegex(
                read(page), r"samples/catalogs/10\.[02]", str(page)
            )

    def test_repository_keys_are_not_hard_coded_to_one_version(self):
        self.assertNotIn('repositories."10.2"', read(PREREQUISITES))


if __name__ == "__main__":
    unittest.main()
