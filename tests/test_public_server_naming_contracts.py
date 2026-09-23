"""Keep public server documentation free of internal model names."""

from pathlib import Path
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "docs"
INSTALLATION_GUIDE = (
    DOCUMENTATION_ROOT / "HowTo" / "utils" / "install_os_unattended.md"
)
CONFIGURATION_REFERENCE = (
    DOCUMENTATION_ROOT / "Reference" / "Configuration" / "install_os_config.md"
)
INTERNAL_MODEL_NAME = "Belton"
PUBLIC_MODEL_NAME = "PowerEdge XE8712"


def read(path):
    """Read a maintained documentation source file."""
    return path.read_text(encoding="utf-8-sig")


class PublicServerNamingContractTests(unittest.TestCase):
    """Require the SME-confirmed public model name in maintained docs."""

    def test_internal_model_name_is_absent(self):
        occurrences = []
        for source in sorted(DOCUMENTATION_ROOT.rglob("*.md")):
            for line_number, line in enumerate(
                read(source).splitlines(), start=1
            ):
                if INTERNAL_MODEL_NAME in line:
                    occurrences.append(
                        f"{source.relative_to(REPOSITORY_ROOT)}:{line_number}"
                    )

        self.assertEqual(
            [],
            occurrences,
            f"Replace {INTERNAL_MODEL_NAME} with {PUBLIC_MODEL_NAME}: "
            + ", ".join(occurrences),
        )

    def test_public_model_name_is_used_in_installation_references(self):
        self.assertIn(PUBLIC_MODEL_NAME, read(INSTALLATION_GUIDE))
        self.assertIn(PUBLIC_MODEL_NAME, read(CONFIGURATION_REFERENCE))


if __name__ == "__main__":
    unittest.main()
