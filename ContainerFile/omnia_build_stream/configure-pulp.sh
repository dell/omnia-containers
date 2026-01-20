#!/bin/bash
# Copyright 2026 Dell Inc. or its subsidiaries. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
