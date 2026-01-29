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

# Entrypoint script for omnia_build_stream container

# Configure Pulp CLI if environment variables are provided
/configure-pulp.sh

# Read omnia_share_path from oim_metadata.yml
# First try default location, then use the extracted path
DEFAULT_PATH="/opt/omnia"
OIM_METADATA_FILE="$DEFAULT_PATH/.data/oim_metadata.yml"

if [ -f "$OIM_METADATA_FILE" ]; then
    OMNIA_SHARE_PATH=$(grep -E '^oim_shared_path:' "$OIM_METADATA_FILE" | awk '{print $2}' | tr -d '"')
    echo "Using omnia_share_path from metadata: $OMNIA_SHARE_PATH"
    
    # If the extracted path is different from default, update the metadata file location
    if [ "$OMNIA_SHARE_PATH" != "$DEFAULT_PATH" ]; then
        OIM_METADATA_FILE="$OMNIA_SHARE_PATH/.data/oim_metadata.yml"
        echo "Metadata file location: $OIM_METADATA_FILE"
    fi
else
    OMNIA_SHARE_PATH="$DEFAULT_PATH"
    echo "WARNING: oim_metadata.yml not found at default location, using: $OMNIA_SHARE_PATH"
fi

# Start the FastAPI application
cd "$OMNIA_SHARE_PATH/build_stream"

if [ -f "/etc/ssl/omnia/cert.pem" ] && [ -f "/etc/ssl/omnia/key.pem" ]; then
    echo "Starting FastAPI with HTTPS on port ${PORT:-443}..."
    exec python3 -m uvicorn main:app --host ${HOST:-0.0.0.0} --port ${PORT:-443} \
        --ssl-keyfile=/etc/ssl/omnia/key.pem \
        --ssl-certfile=/etc/ssl/omnia/cert.pem
else
    echo "WARNING: SSL certificates not found, starting with HTTP on port ${PORT:-443}..."
    exec python3 -m uvicorn main:app --host ${HOST:-0.0.0.0} --port ${PORT:-443}
fi
