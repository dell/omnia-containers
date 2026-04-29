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

set -euo pipefail

S3CFG_FILE="${S3CFG_FILE:-/root/.s3cfg}"
MINIO_ACCESS_KEY="${MINIO_ACCESS_KEY:-admin}"
MINIO_SECRET_KEY="${MINIO_SECRET_KEY:-}"
MINIO_HOST="${MINIO_HOST:-localhost:9000}"
MINIO_USE_HTTPS="${MINIO_USE_HTTPS:-False}"

if [ -z "$MINIO_SECRET_KEY" ]; then
    echo "WARNING: MINIO_SECRET_KEY not set. s3cmd will not work without valid credentials."
    echo "Please set MINIO_SECRET_KEY environment variable or mount a valid .s3cfg file."
    exit 0
fi

cat > "$S3CFG_FILE" <<EOF
[default]
access_key = ${MINIO_ACCESS_KEY}
secret_key = ${MINIO_SECRET_KEY}
host_base = ${MINIO_HOST}
host_bucket = ${MINIO_HOST}
use_https = ${MINIO_USE_HTTPS}
signature_v2 = False
check_ssl_certificate = False
check_ssl_hostname = False
EOF

chmod 600 "$S3CFG_FILE"
echo "s3cmd configuration initialized at $S3CFG_FILE"
