#!/bin/bash
# Entrypoint script for omnia_build_stream container

# Configure Pulp CLI if environment variables are provided
/configure-pulp.sh

# TODO: Uncomment when api_server.py is available in /opt/omnia/build_stream
# Start the FastAPI application with SSL if certificates exist
# cd /opt/omnia/build_stream
# if [ -f "/etc/ssl/omnia/cert.pem" ] && [ -f "/etc/ssl/omnia/key.pem" ]; then
#     echo "Starting FastAPI with HTTPS on port 443..."
#     exec python3 -m uvicorn api_server:app --host 0.0.0.0 --port 443 \
#         --ssl-keyfile=/etc/ssl/omnia/key.pem \
#         --ssl-certfile=/etc/ssl/omnia/cert.pem
# else
#     echo "WARNING: SSL certificates not found, starting with HTTP on port 443..."
#     exec python3 -m uvicorn api_server:app --host 0.0.0.0 --port 443
# fi

echo "Container started successfully. API server is disabled (api_server.py not implemented yet)."
echo "Keeping container alive..."
exec tail -f /dev/null
