#!/bin/bash
# Entrypoint script for omnia_build_stream container

# Configure Pulp CLI if environment variables are provided
/configure-pulp.sh

# Start the FastAPI application
exec python3 -m uvicorn api_server:app --host 0.0.0.0 --port 80
