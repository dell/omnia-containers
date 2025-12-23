#!/bin/bash
# Setup virtual environment for Omnia Automation

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"

echo "Creating virtual environment..."
python3 -m venv "${VENV_DIR}"

echo "Activating virtual environment..."
source "${VENV_DIR}/bin/activate"

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r "${SCRIPT_DIR}/requirements.txt"

echo ""
echo "============================================"
echo "  Setup complete!"
echo "============================================"
echo ""
echo "To activate the environment:"
echo "  source .venv/bin/activate"
echo ""
echo "To run tests:"
echo "  ./run_molecule.sh all test"
echo ""
