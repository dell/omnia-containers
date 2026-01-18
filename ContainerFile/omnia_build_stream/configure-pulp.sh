#!/bin/bash
# Configure pulp-cli to connect to Pulp server

PULP_CONFIG_DIR="/root/.config/pulp"
PULP_CONFIG_FILE="${PULP_CONFIG_DIR}/cli.toml"

# Set defaults if environment variables are not provided
PULP_BASE_URL="${PULP_BASE_URL:-https://localhost}"
PULP_USERNAME="${PULP_USERNAME:-admin}"
PULP_VERIFY_SSL="${PULP_VERIFY_SSL:-true}"

# Create config directory if it doesn't exist
mkdir -p "$PULP_CONFIG_DIR"

# Create Pulp CLI configuration
# Note: SSL verification uses REQUESTS_CA_BUNDLE and SSL_CERT_FILE environment variables
# which point directly to the Pulp certificate mounted at /etc/pulp/certs/pulp_webserver.crt
cat > "$PULP_CONFIG_FILE" <<EOF
[cli]
base_url = "${PULP_BASE_URL}"
username = "${PULP_USERNAME}"
verify_ssl = ${PULP_VERIFY_SSL}
EOF

# Add password if provided
if [ -n "$PULP_PASSWORD" ]; then
    echo "password = \"${PULP_PASSWORD}\"" >> "$PULP_CONFIG_FILE"
fi

# Set proper permissions
chmod 600 "$PULP_CONFIG_FILE"

echo "Pulp CLI configuration created at ${PULP_CONFIG_FILE}"
