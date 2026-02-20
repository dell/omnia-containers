#!/bin/bash
set -euo pipefail

METADATA_FILE="/opt/omnia/.data/oim_metadata.yml"
HASH_KEY="omnia_build_stream_hashed_passwd"

# Configure root password from hashed value in metadata (paasword is same as omnia core container)
if [[ -f "${METADATA_FILE}" ]]; then
    hashed_passwd=$(grep "${HASH_KEY}" "${METADATA_FILE}" | awk -F: '{print $2}' | tr -d ' ' || true)
    if [[ -n "${hashed_passwd}" ]]; then
        echo "root:${hashed_passwd}" | chpasswd -e
    else
        echo "[WARN] ${HASH_KEY} not found in ${METADATA_FILE}; retaining existing root password" >&2
    fi
else
    echo "[WARN] Metadata file ${METADATA_FILE} not found; retaining existing root password" >&2
fi

# Start SSH daemon in the background
/usr/sbin/sshd -D &
SSHD_PID=$!

# Launch FastAPI service (expects HOST/PORT/SSL vars to be provided via env)
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8010}
python3 -m uvicorn main:app --host "${HOST}" --port "${PORT}" --ssl-keyfile="${SSL_KEYFILE}" --ssl-certfile="${SSL_CERTFILE}"

# Ensure background sshd exits when uvicorn stops
wait ${SSHD_PID}
