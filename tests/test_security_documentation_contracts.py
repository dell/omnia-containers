"""Keep the public security guidance aligned with implemented trust boundaries."""

from pathlib import Path
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "docs"
NETWORK_SECURITY = (
    DOCUMENTATION_ROOT / "SecurityConfigurationGuide" / "network_security.md"
)
PRODUCT_SECURITY = (
    DOCUMENTATION_ROOT
    / "SecurityConfigurationGuide"
    / "product_subsystem_security.md"
)
EXTERNAL_AUTHENTICATION = (
    DOCUMENTATION_ROOT
    / "SecurityConfigurationGuide"
    / "external_systems_authentication.md"
)

FORBIDDEN_ABSOLUTE_CLAIMS = {
    "omnia does not store data",
    "omnia does not have its own authentication mechanism",
}


def read(path):
    """Read a maintained documentation source file."""
    return path.read_text(encoding="utf-8-sig")


class SecurityDocumentationContractTests(unittest.TestCase):
    """Prevent the corrected persistence and authentication guidance drifting."""

    def test_false_absolute_claims_are_absent(self):
        occurrences = []
        for source in sorted(DOCUMENTATION_ROOT.rglob("*.md")):
            for line_number, line in enumerate(
                read(source).splitlines(), start=1
            ):
                normalized_line = line.casefold()
                for claim in FORBIDDEN_ABSOLUTE_CLAIMS:
                    if claim in normalized_line:
                        occurrences.append(
                            f"{source.relative_to(REPOSITORY_ROOT)}:"
                            f"{line_number}: {claim}"
                        )

        self.assertEqual(
            [],
            occurrences,
            "Remove false absolute security claims from: "
            + ", ".join(occurrences),
        )

    def test_data_inventory_covers_persisted_service_classes(self):
        network_security = read(NETWORK_SECURITY)
        normalized_network_security = " ".join(network_security.split())
        required_data_boundaries = {
            "Domain input, output, and runtime data",
            "Domain credentials and Vault material",
            "Pulp repositories and service state",
            "Image Build Manager objects and images",
            "BuildStreaM API state and artifacts",
            "Managed GitLab data",
            "Provisioning and OpenCHAMI state",
            "Telemetry state",
            "does not establish a universal data-retention, backup, or "
            "storage-encryption policy",
        }

        for boundary in required_data_boundaries:
            self.assertIn(boundary, normalized_network_security)

    def test_buildstream_matrix_retains_direction_and_security_controls(self):
        network_security = read(NETWORK_SECURITY)
        required_matrix_contracts = {
            "| Source | Destination | Direction |",
            "TCP 8010 by default (`build_stream_port`)",
            "TCP 443 by default (`gitlab_https_port`)",
            "| TCP 22 |",
            "| TCP 5432 |",
            "protected operations use JWT bearer tokens",
            "currently disable server-certificate verification",
            "Do not expose it outside the OIM",
        }

        for contract in required_matrix_contracts:
            self.assertIn(contract, network_security)

    def test_buildstream_authentication_contract_is_documented(self):
        product_security = read(PRODUCT_SECURITY)
        required_authentication_contracts = {
            "HTTP Basic authentication",
            "Argon2id",
            "RS256-signed JWT",
            "default access-token lifetime is 60 minutes",
            "required scope is absent",
            "The API root, health endpoint, OpenAPI document",
        }

        for contract in required_authentication_contracts:
            self.assertIn(contract, product_security)

    def test_external_trust_inventory_covers_supported_boundaries(self):
        external_authentication = read(EXTERNAL_AUTHENTICATION)
        required_systems = {
            "OpenManage Enterprise (OME)",
            "iDRAC/BMC",
            "Managed GitLab",
            "Container registries, including Docker Hub",
            "Pulp",
            "MinIO or external PowerScale S3",
            "PowerScale CSI",
            "UFM",
            "VAST",
            "LDAP/OpenLDAP",
            "Additional Telemetry sinks",
        }

        for system in required_systems:
            self.assertIn(f"| {system} |", external_authentication)

        self.assertIn(
            "Kubernetes Secret data is base64-encoded, not encrypted at rest",
            external_authentication,
        )
        self.assertIn(
            "does not define an authentication-secret contract",
            external_authentication,
        )


if __name__ == "__main__":
    unittest.main()
