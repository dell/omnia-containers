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
SERVER_MATRIX = (
    DOCUMENTATION_ROOT / "Reference" / "SupportMatrix" / "servers.md"
)

# Mirrors target_architecture in
# src/utils/plugins/module_utils/input_validation/schema/install_os_config.json.
TARGET_ARCHITECTURES = {"x86_64", "aarch64"}
LIMITED_VALIDATION_NOTICE = (
    "For aarch64 architecture platforms, limited validation has been performed "
    "on early access systems."
)
FORBIDDEN_MANUAL_ONLY_WORDING = (
    "You must install the OS manually on aarch64 nodes."
)


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

    def test_limited_validation_notice_is_consistent(self):
        for source in (
            PREREQUISITES,
            INSTALLATION_GUIDE,
            CONFIGURATION_REFERENCE,
            SERVER_MATRIX,
        ):
            self.assertIn(
                LIMITED_VALIDATION_NOTICE,
                read(source),
                f"Missing aarch64 qualification in "
                f"{source.relative_to(REPOSITORY_ROOT)}",
            )

    def test_prerequisites_link_to_unattended_workflow(self):
        prerequisites = read(PREREQUISITES)
        self.assertIn(
            "[unattended OS installation workflow]"
            "(../HowTo/utils/install_os_unattended.md)",
            prerequisites,
        )
        self.assertIn("supports `aarch64`", prerequisites)


if __name__ == "__main__":
    unittest.main()
