#!/bin/bash
# Configure pulp-cli to connect to Pulp server

PULP_CONFIG_DIR="/root/.config/pulp"
PULP_CONFIG_FILE="${PULP_CONFIG_DIR}/cli.toml"
OMNIA_METADATA_FILE="/opt/omnia/.data/oim_metadata.yml"
LOG_DIR="/opt/omnia/log/build_stream"
LOG_FILE="${LOG_DIR}/pulp_config.log"

# Log to both stdout (systemd journal) and file
echo "$(date): Starting Pulp CLI configuration..." | tee -a "$LOG_FILE"

# Check if required environment variables are set
if [ -z "$PULP_BASE_URL" ]; then
    echo "$(date): WARNING - PULP_BASE_URL not set, using default: https://localhost" | tee -a "$LOG_FILE"
    PULP_BASE_URL="https://localhost"
fi

if [ -z "$PULP_USERNAME" ]; then
    echo "$(date): WARNING - PULP_USERNAME not set, using default: admin" | tee -a "$LOG_FILE"
    PULP_USERNAME="admin"
fi

# Try to read password from Omnia metadata file if not set via environment
if [ -z "$PULP_PASSWORD" ]; then
    echo "$(date): PULP_PASSWORD not set via environment, checking Omnia metadata file..." | tee -a "$LOG_FILE"
    
    if [ -f "$OMNIA_METADATA_FILE" ]; then
        echo "$(date): Found Omnia metadata file at ${OMNIA_METADATA_FILE}" | tee -a "$LOG_FILE"
        
        # Extract pulp_password from YAML file using grep and awk
        PULP_PASSWORD=$(grep -E '^pulp_password:' "$OMNIA_METADATA_FILE" | awk '{print $2}' | tr -d '"' | tr -d "'")
        
        if [ -n "$PULP_PASSWORD" ]; then
            echo "$(date): Successfully read Pulp password from metadata file" | tee -a "$LOG_FILE"
        else
            echo "$(date): WARNING - Could not extract pulp_password from metadata file" | tee -a "$LOG_FILE"
        fi
    else
        echo "$(date): WARNING - Omnia metadata file not found at ${OMNIA_METADATA_FILE}" | tee -a "$LOG_FILE"
    fi
fi

if [ -z "$PULP_PASSWORD" ]; then
    echo "$(date): WARNING - PULP_PASSWORD not available from any source" | tee -a "$LOG_FILE"
fi

# Set verify_ssl based on environment variable (default: true for secure connections)
PULP_VERIFY_SSL="${PULP_VERIFY_SSL:-true}"

# Create pulp CLI configuration
echo "$(date): Creating Pulp CLI configuration at ${PULP_CONFIG_FILE}" | tee -a "$LOG_FILE"

cat > "$PULP_CONFIG_FILE" <<EOF
[cli]
base_url = "${PULP_BASE_URL}"
username = "${PULP_USERNAME}"
verify_ssl = ${PULP_VERIFY_SSL}
EOF

# Add password if provided
if [ -n "$PULP_PASSWORD" ]; then
    echo "password = \"${PULP_PASSWORD}\"" >> "$PULP_CONFIG_FILE"
    echo "$(date): Pulp CLI configured with password" | tee -a "$LOG_FILE"
else
    echo "$(date): Pulp CLI configured without password (will use interactive auth)" | tee -a "$LOG_FILE"
fi

# Set proper permissions
chmod 600 "$PULP_CONFIG_FILE"

echo "$(date): Pulp CLI configuration completed" | tee -a "$LOG_FILE"
echo "$(date): Configuration details:" | tee -a "$LOG_FILE"
echo "  - Base URL: ${PULP_BASE_URL}" | tee -a "$LOG_FILE"
echo "  - Username: ${PULP_USERNAME}" | tee -a "$LOG_FILE"
echo "  - Verify SSL: ${PULP_VERIFY_SSL}" | tee -a "$LOG_FILE"

# Test connection if pulp command is available
if command -v pulp &> /dev/null; then
    echo "$(date): Testing Pulp connection..." | tee -a "$LOG_FILE"
    if pulp status >> "$LOG_FILE" 2>&1; then
        echo "$(date): Successfully connected to Pulp server" | tee -a "$LOG_FILE"
    else
        echo "$(date): WARNING - Could not connect to Pulp server. Check configuration and network." | tee -a "$LOG_FILE"
    fi
fi

echo "$(date): Pulp configuration script completed" | tee -a "$LOG_FILE"
