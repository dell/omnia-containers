"""Keep public aarch64 installation guidance aligned with the source contract."""

from pathlib import Path
import re
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "docs"
PREREQUISITES = DOCUMENTATION_ROOT / "GetStarted" / "prerequisites_checklist.md"
INSTALLATION_GUIDE = (
    DOCUMENTATION_ROOT / "HowTo" / "utils" / "install_os_unattended.md"
)
CONFIGURATION_REFERENCE = (
    DOCUMENTATION_ROOT / "Reference" / "Configuration" / "install_os_config.md"
)

# Mirrors target_architecture in
# src/utils/plugins/module_utils/input_validation/schema/install_os_config.json.
TARGET_ARCHITECTURES = {"x86_64", "aarch64"}
FORBIDDEN_EARLY_ACCESS_WORDING = (
    "For aarch64 architecture platforms, limited validation has been performed "
    "on early access systems."
)
FORBIDDEN_SEPARATE_PREREQUISITE = "#### Aarch64 Node Prerequisites"
FORBIDDEN_MANUAL_ONLY_WORDING = (
    "You must install the OS manually on aarch64 nodes."
)
VALIDATED_WORKFLOW_SCOPE = {
    "PowerEdge XE8712",
    "RHEL 10.0",
    "iDRAC 9",
    "`embedded`",
    "complete ISO build and deployment workflow",
    "iDRAC 10 is expected to work",
    "procedure-specific validation recorded here used iDRAC 9",
}


def read(path):
    """Read a maintained documentation source file."""
    return path.read_text(encoding="utf-8-sig")


class Aarch64DocumentationContractTests(unittest.TestCase):
    """Prevent the architecture contract and qualification text from drifting."""

    def test_manual_only_aarch64_instruction_is_absent(self):
        occurrences = []
        for source in sorted(DOCUMENTATION_ROOT.rglob("*.md")):
            for line_number, line in enumerate(
                read(source).splitlines(), start=1
            ):
                if FORBIDDEN_MANUAL_ONLY_WORDING in line:
                    occurrences.append(
                        f"{source.relative_to(REPOSITORY_ROOT)}:{line_number}"
                    )

        self.assertEqual(
            [],
            occurrences,
            "The source supports unattended aarch64 installation; remove the "
            "manual-only instruction from: " + ", ".join(occurrences),
        )

    def test_architecture_enum_matches_public_references(self):
        configuration = read(CONFIGURATION_REFERENCE)
        parameter_row = re.search(
            r"^\| `target_architecture` \|.*$", configuration, re.MULTILINE
        )
        self.assertIsNotNone(parameter_row)

        documented_architectures = {
            value
            for value in re.findall(r"`([^`]+)`", parameter_row.group(0))
            if value != "target_architecture"
        }
        self.assertEqual(TARGET_ARCHITECTURES, documented_architectures)

        expected_statement = "supports `x86_64` and `aarch64`"
        self.assertIn(expected_statement, configuration)
        self.assertIn(expected_statement, read(INSTALLATION_GUIDE))

    def test_obsolete_aarch64_qualification_is_absent(self):
        documentation = "\n".join(
            read(source) for source in sorted(DOCUMENTATION_ROOT.rglob("*.md"))
        )
        self.assertNotIn(FORBIDDEN_EARLY_ACCESS_WORDING, documentation)
        self.assertNotIn(FORBIDDEN_SEPARATE_PREREQUISITE, documentation)

    def test_validated_workflow_scope_is_documented(self):
        installation_guide = read(INSTALLATION_GUIDE)
        for expected_value in VALIDATED_WORKFLOW_SCOPE:
            self.assertIn(expected_value, installation_guide)

    def test_prerequisites_link_to_unattended_workflow(self):
        prerequisites = read(PREREQUISITES)
        self.assertIn(
            "[unattended OS installation workflow]"
            "(../HowTo/utils/install_os_unattended.md)",
            prerequisites,
        )
        self.assertIn("supports both `x86_64` and `aarch64`", prerequisites)


if __name__ == "__main__":
    unittest.main()
