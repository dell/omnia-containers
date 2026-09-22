"""Validate the public Main and omnia-cli command references."""

from pathlib import Path
import re
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MAIN_REFERENCE = REPOSITORY_ROOT / "docs" / "HowTo" / "main" / "index.md"
CATALOG_GUIDE = REPOSITORY_ROOT / "docs" / "HowTo" / "main" / "update_catalog.md"
CLI_GUIDE = REPOSITORY_ROOT / "docs" / "HowTo" / "main" / "omnia_cli.md"
PLAYBOOK_REFERENCE = (
    REPOSITORY_ROOT / "docs" / "Reference" / "Playbooks" / "playbook_reference.md"
)
MKDOCS_CONFIG = REPOSITORY_ROOT / "mkdocs.yml"

CATALOG_COMMANDS = {"--list-catalogs", "--select-catalog"}
CLI_COMMANDS = {
    "status [--project <name>]",
    "check [--project <name>]",
    "edit <domain> [file] [--project <name>]",
    "output <domain> [file] [--project <name>]",
    "logs <domain> [--project <name>] [--limit <n>]",
    "repo_manager [--project <name>]",
    "image_build_manager [--project <name>]",
    "orchestrator [--project <name>]",
    "discovery [--project <name>]",
    "telemetry [--project <name>]",
    "build_stream [--project <name>]",
    "utils [--project <name>]",
    "version",
    "help [<domain>]",
}
SLURM_UTILS_OPERATIONS = {
    "slurm_config_backup",
    "slurm_config_cleanup",
    "slurm_config_rollback",
    "cleanup_slurm_config_backups",
}


def read(path):
    """Read a maintained documentation source file."""
    return path.read_text(encoding="utf-8-sig")


def code_spans(value):
    """Return the Markdown code spans in a string."""
    return set(re.findall(r"`([^`]+)`", value))


def section(document, start, end):
    """Return the text between two unique Markdown headings."""
    return document.split(start, 1)[1].split(end, 1)[0]


class CommandReferenceContractTests(unittest.TestCase):
    """Keep public command tables complete and internally consistent."""

    def test_catalog_commands_are_in_main_reference_and_primary_guide(self):
        main_reference = read(MAIN_REFERENCE)
        catalog_guide = read(CATALOG_GUIDE)

        for command in CATALOG_COMMANDS:
            self.assertIn(f"`{command}", main_reference)
            self.assertIn(command, catalog_guide)

        fallback_position = catalog_guide.index(
            "## Controlled fallback for a custom catalog"
        )
        self.assertLess(
            catalog_guide.index("./omnia.sh --select-catalog"), fallback_position
        )
        self.assertNotIn("\n    cp ", catalog_guide[:fallback_position])

    def test_cli_reference_documents_every_supported_command(self):
        cli_reference = section(
            read(CLI_GUIDE), "## Command reference", "### Options"
        )
        documented_commands = {
            match.group(1)
            for match in re.finditer(r"^\| `([^`]+)` \|", cli_reference, re.MULTILINE)
        }
        self.assertEqual(CLI_COMMANDS, documented_commands)

    def test_main_utils_operations_cover_playbook_reference(self):
        main_reference = read(MAIN_REFERENCE)
        playbook_reference = read(PLAYBOOK_REFERENCE)

        main_match = re.search(
            r"^\| `utils` \| (?P<tags>.*?) \|$", main_reference, re.MULTILINE
        )
        playbook_match = re.search(
            r"^\| Utils \| `src/utils/playbooks/utils\.yml` \| "
            r"(?P<tags>.*?) \| \[How-to guide\]",
            playbook_reference,
            re.MULTILINE,
        )
        self.assertIsNotNone(main_match)
        self.assertIsNotNone(playbook_match)

        main_tags = code_spans(main_match.group("tags"))
        implemented_tags = code_spans(playbook_match.group("tags"))
        self.assertTrue(SLURM_UTILS_OPERATIONS <= main_tags)
        self.assertTrue(implemented_tags <= main_tags)

    def test_cli_guide_is_in_main_navigation(self):
        navigation = read(MKDOCS_CONFIG)
        self.assertIn("Diagnostics CLI: HowTo/main/omnia_cli.md", navigation)


if __name__ == "__main__":
    unittest.main()
