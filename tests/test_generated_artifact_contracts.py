"""Validate generated artifact names documented by the Omnia guides."""

from pathlib import Path
import re
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "docs"
FORBIDDEN_INVENTORY_NAME = "orchestrator_inventory.yaml"
GENERATED_INVENTORY_CONTRACT = {
    "bmc_group_data": "bmc_group_data.csv",
    "orchestrator_inventory": "orchestrator_inventory.yml",
}
GENERATED_INVENTORY_PATTERN = re.compile(
    r"\b(?:bmc_group_data|orchestrator_inventory)\.[A-Za-z0-9]+\b"
)


def markdown_sources():
    """Return all maintained Markdown documentation sources."""
    return sorted(DOCUMENTATION_ROOT.rglob("*.md"))


class GeneratedArtifactContractTests(unittest.TestCase):
    """Keep documented inventory names aligned with the producer contract."""

    def test_deprecated_orchestrator_inventory_name_is_absent(self):
        occurrences = []
        for source in markdown_sources():
            for line_number, line in enumerate(
                source.read_text(encoding="utf-8-sig").splitlines(), start=1
            ):
                if FORBIDDEN_INVENTORY_NAME in line:
                    occurrences.append(
                        f"{source.relative_to(REPOSITORY_ROOT)}:{line_number}"
                    )

        self.assertEqual(
            [],
            occurrences,
            f"Replace {FORBIDDEN_INVENTORY_NAME} with "
            f"{GENERATED_INVENTORY_CONTRACT['orchestrator_inventory']}: "
            + ", ".join(occurrences),
        )

    def test_generated_inventory_references_match_output_contract(self):
        expected_names = set(GENERATED_INVENTORY_CONTRACT.values())
        documented_names = set()

        for source in markdown_sources():
            documented_names.update(
                GENERATED_INVENTORY_PATTERN.findall(
                    source.read_text(encoding="utf-8-sig")
                )
            )

        unexpected_names = documented_names - expected_names
        missing_names = expected_names - documented_names
        self.assertEqual(
            set(),
            unexpected_names,
            "Documented generated inventories do not match the producer contract: "
            + ", ".join(sorted(unexpected_names)),
        )
        self.assertEqual(
            set(),
            missing_names,
            "Generated inventories missing from the documentation: "
            + ", ".join(sorted(missing_names)),
        )


if __name__ == "__main__":
    unittest.main()
