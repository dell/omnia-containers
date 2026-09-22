"""Keep RHEL point-release guidance aligned with the documented RC1 status."""

from pathlib import Path
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "docs"
SUPPORT_MATRIX = (
    DOCUMENTATION_ROOT / "Reference" / "SupportMatrix" / "operating_systems.md"
)
PREREQUISITES = DOCUMENTATION_ROOT / "GetStarted" / "prerequisites_checklist.md"
CATALOG_GUIDE = DOCUMENTATION_ROOT / "HowTo" / "main" / "update_catalog.md"
RELEASE_NOTES = DOCUMENTATION_ROOT / "Overview" / "release_notes.md"
QUICK_STARTS = (
    DOCUMENTATION_ROOT / "GetStarted" / "k8s_telemetry_only.md",
    DOCUMENTATION_ROOT / "GetStarted" / "slurm_quickstart.md",
    DOCUMENTATION_ROOT / "GetStarted" / "full_deployment.md",
)
RHEL_10_2_MARKERS = ("RHEL 10.2", "rhel_10_2", "catalogs/10.2")
RHEL_10_2_STATUS_PAGES = {SUPPORT_MATRIX, CATALOG_GUIDE, RELEASE_NOTES}


def read(path):
    """Read a maintained documentation source file."""
    return path.read_text(encoding="utf-8-sig")


def normalized(path):
    """Return documentation text with prose line wrapping removed."""
    return " ".join(read(path).split())


class OperatingSystemSupportDocumentationContractTests(unittest.TestCase):
    """Prevent shipped catalogs from being presented as support evidence."""

    def test_support_matrix_separates_oim_and_cluster_node_axes(self):
        matrix = read(SUPPORT_MATRIX)
        matrix_prose = normalized(SUPPORT_MATRIX)

        self.assertIn("| OIM OS | Cluster-node OS |", matrix)
        self.assertIn("| RHEL 10.0 | RHEL 10.0 | Validated |", matrix)
        self.assertIn(
            "catalog selects the operating system used to build cluster-node",
            matrix_prose,
        )
        self.assertIn(
            "No RHEL 10.2 combination has a published product classification",
            matrix_prose,
        )

    def test_normal_quick_starts_do_not_recommend_rhel_10_2(self):
        occurrences = []
        for source in QUICK_STARTS:
            content = read(source)
            for marker in RHEL_10_2_MARKERS:
                if marker in content:
                    occurrences.append(
                        f"{source.relative_to(REPOSITORY_ROOT)}: {marker}"
                    )

        self.assertEqual(
            [],
            occurrences,
            "Normal quick starts must use the documented validated RHEL 10.0 "
            "path until Engineering classifies RHEL 10.2: "
            + ", ".join(occurrences),
        )

    def test_rhel_10_2_mentions_are_limited_to_status_context(self):
        unexpected = []
        for source in sorted(DOCUMENTATION_ROOT.rglob("*.md")):
            if source in RHEL_10_2_STATUS_PAGES:
                continue
            content = read(source)
            for marker in RHEL_10_2_MARKERS:
                if marker in content:
                    unexpected.append(
                        f"{source.relative_to(REPOSITORY_ROOT)}: {marker}"
                    )

        self.assertEqual(
            [],
            unexpected,
            "RHEL 10.2 must not be promoted outside the status pages until "
            "Engineering publishes its classification: "
            + ", ".join(unexpected),
        )

    def test_catalog_guide_qualifies_bundled_10_2_artifacts(self):
        catalog_guide = read(CATALOG_GUIDE)
        catalog_prose = normalized(CATALOG_GUIDE)

        self.assertIn(
            "Bundled catalog availability is not a product-support statement",
            catalog_prose,
        )
        for classification in (
            "Supported",
            "Validated",
            "Technology preview",
            "Not supported",
        ):
            self.assertIn(classification, catalog_guide)
        self.assertIn(
            "Use a `10.0` selector for the documented validated RC1 baseline",
            catalog_prose,
        )

    def test_release_pin_is_scoped_to_the_oim(self):
        prerequisites = read(PREREQUISITES)

        self.assertIn("OIM RHEL release pinned to 10.0", prerequisites)
        self.assertIn(
            "The cluster-node version is selected separately by the catalog",
            prerequisites,
        )
        self.assertNotIn("Omnia requires RHEL 10.0", prerequisites)

    def test_release_notes_do_not_treat_catalog_presence_as_support(self):
        release_notes = read(RELEASE_NOTES)
        release_prose = normalized(RELEASE_NOTES)

        self.assertIn(
            "validated with RHEL 10.0 on the Omnia Infrastructure Manager "
            "(OIM) and cluster nodes",
            release_prose,
        )
        self.assertIn(
            "presence does not declare RHEL 10.2 supported, validated, or a "
            "technology preview",
            release_prose,
        )


if __name__ == "__main__":
    unittest.main()
