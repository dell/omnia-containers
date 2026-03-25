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

# =============================================================================
# Omnia Automation – Environment Setup
# =============================================================================
#
# Prepares the local machine to run the Omnia Automation Framework.
#
# What it does:
#   1. Validates system prerequisites (Python 3, venv, sshpass)
#   2. Creates a Python virtual environment (.venv)
#   3. Installs all Python dependencies from requirements.txt
#   4. Makes helper scripts executable
#   5. Prints clear next-step instructions
#
# Usage:
#   bash setup_env.sh              # first-time setup (quiet install)
#   bash setup_env.sh --force      # recreate venv + reinstall everything
#   bash setup_env.sh --debug      # verbose output (shows every package)
#   bash setup_env.sh --force --debug
#
# =============================================================================

set -euo pipefail

# ── Constants ────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"
REQ_FILE="${SCRIPT_DIR}/requirements.txt"
USER_CONFIG="${SCRIPT_DIR}/user_config.yml"
PREREQ_SCRIPT="${SCRIPT_DIR}/run_prereq_check.py"
MOLECULE_SCRIPT="${SCRIPT_DIR}/run_molecule.sh"
MIN_PYTHON_MAJOR=3
MIN_PYTHON_MINOR=9
FORCE=false
DEBUG=false

# ── Colours (disabled when stdout is not a terminal) ─────────────────────────
if [ -t 1 ]; then
    C_RESET='\033[0m'; C_BOLD='\033[1m'; C_DIM='\033[2m'
    C_RED='\033[91m'; C_GREEN='\033[92m'; C_YELLOW='\033[93m'
    C_CYAN='\033[96m'; C_WHITE='\033[97m'
else
    C_RESET=''; C_BOLD=''; C_DIM=''
    C_RED=''; C_GREEN=''; C_YELLOW=''
    C_CYAN=''; C_WHITE=''
fi

# ── Helper functions ─────────────────────────────────────────────────────────
info()  { printf "${C_CYAN}[INFO]${C_RESET}  %s\n" "$*"; }
ok()    { printf "${C_GREEN}[  OK]${C_RESET}  %s\n" "$*"; }
warn()  { printf "${C_YELLOW}[WARN]${C_RESET}  %s\n" "$*"; }
fail()  { printf "${C_RED}[FAIL]${C_RESET}  %s\n" "$*"; exit 1; }
dbg()   { if [ "$DEBUG" = true ]; then printf "${C_DIM}[DBG ]  %s${C_RESET}\n" "$*"; fi; }

separator() {
    printf "${C_DIM}%0.s─${C_RESET}" $(seq 1 70); echo
}

pip_flags() {
    if [ "$DEBUG" = true ]; then echo ""; else echo "--quiet"; fi
}

# ── Parse arguments ──────────────────────────────────────────────────────────
for arg in "$@"; do
    case "$arg" in
        --force|-f)  FORCE=true ;;
        --debug|-d)  DEBUG=true ;;
        --help|-h)
            echo "Usage: bash setup_env.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --force, -f   Remove existing .venv and recreate from scratch"
            echo "  --debug, -d   Verbose output (show installed packages, versions)"
            echo "  --help,  -h   Show this help message"
            exit 0
            ;;
        *) warn "Unknown argument: $arg (ignored)" ;;
    esac
done

# ── Banner ───────────────────────────────────────────────────────────────────
echo ""
separator
printf "${C_BOLD}${C_WHITE}  Omnia Automation – Environment Setup${C_RESET}\n"
separator
echo ""

if [ "$DEBUG" = true ]; then
    info "Debug mode enabled – verbose output"
fi
if [ "$FORCE" = true ]; then
    info "Force mode enabled – will recreate virtual environment"
fi

# ═════════════════════════════════════════════════════════════════════════════
# PREREQUISITE VALIDATION
# ═════════════════════════════════════════════════════════════════════════════

# ── Python ───────────────────────────────────────────────────────────────────
info "Checking Python installation..."

if ! command -v python3 &>/dev/null; then
    fail "python3 is not installed. Install Python >= ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR} and retry."
fi

PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)

if [ "$PY_MAJOR" -lt "$MIN_PYTHON_MAJOR" ] || \
   { [ "$PY_MAJOR" -eq "$MIN_PYTHON_MAJOR" ] && [ "$PY_MINOR" -lt "$MIN_PYTHON_MINOR" ]; }; then
    fail "Python ${PY_VERSION} is too old. Minimum required: ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}"
fi
ok "Python ${PY_VERSION}"
dbg "Path: $(command -v python3)"

# ── venv module ──────────────────────────────────────────────────────────────
info "Checking Python venv module..."
if ! python3 -m venv --help &>/dev/null; then
    fail "Python venv module is missing. Install it with: dnf install -y python3-pip"
fi
ok "Python venv module available"

# ── sshpass (required for remote SSH in prereq checks) ───────────────────────
info "Checking sshpass..."
if ! command -v sshpass &>/dev/null; then
    info "sshpass not found – installing..."
    if command -v dnf &>/dev/null; then
        dbg "Using dnf to install sshpass"
        if dnf install -y sshpass $(pip_flags) 2>&1; then
            ok "sshpass installed successfully"
        else
            fail "Failed to install sshpass. Make sure your OS package repositories (dnf/yum) are configured correctly."
        fi
    elif command -v yum &>/dev/null; then
        dbg "Using yum to install sshpass"
        if yum install -y sshpass $(pip_flags) 2>&1; then
            ok "sshpass installed successfully"
        else
            fail "Failed to install sshpass. Make sure your OS package repositories (yum) are configured correctly."
        fi
    elif command -v apt-get &>/dev/null; then
        dbg "Using apt-get to install sshpass"
        if apt-get install -y sshpass $(pip_flags) 2>&1; then
            ok "sshpass installed successfully"
        else
            fail "Failed to install sshpass. Make sure your OS package repositories (apt) are configured correctly."
        fi
    else
        fail "No supported package manager found (dnf/yum/apt-get). Install sshpass manually and retry."
    fi
    # Verify installation succeeded
    if ! command -v sshpass &>/dev/null; then
        fail "sshpass installation failed. Make sure your OS package repositories are configured correctly."
    fi
fi
SSHPASS_VER=$(sshpass -V 2>&1 | head -1 || true)
ok "sshpass available (${SSHPASS_VER})"
dbg "Path: $(command -v sshpass)"

# ── requirements.txt ─────────────────────────────────────────────────────────
if [ ! -f "${REQ_FILE}" ]; then
    fail "requirements.txt not found at ${REQ_FILE}"
fi
dbg "requirements.txt: ${REQ_FILE}"

# ═════════════════════════════════════════════════════════════════════════════
# VIRTUAL ENVIRONMENT
# ═════════════════════════════════════════════════════════════════════════════

if [ -d "${VENV_DIR}" ]; then
    if [ "$FORCE" = true ]; then
        warn "Removing existing virtual environment (--force)..."
        rm -rf "${VENV_DIR}"
    else
        info "Virtual environment already exists at ${VENV_DIR}"
        info "Use --force to recreate from scratch."
    fi
fi

if [ ! -d "${VENV_DIR}" ]; then
    info "Creating virtual environment..."
    python3 -m venv "${VENV_DIR}"
    ok "Virtual environment created at ${VENV_DIR}"
fi

info "Activating virtual environment..."
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"
ok "Virtual environment activated"

# ═════════════════════════════════════════════════════════════════════════════
# DEPENDENCY INSTALLATION
# ═════════════════════════════════════════════════════════════════════════════

info "Upgrading pip..."
pip install --upgrade pip $(pip_flags)

info "Installing Python dependencies..."
pip install -r "${REQ_FILE}" $(pip_flags)
ok "All dependencies installed"

# ── Debug: show installed packages ───────────────────────────────────────────
if [ "$DEBUG" = true ]; then
    echo ""
    info "Installed packages:"
    pip list --format=columns 2>/dev/null | while IFS= read -r line; do
        dbg "  $line"
    done
    echo ""
    info "Key tool versions:"
    dbg "  python3     : $(python3 --version 2>&1)"
    dbg "  pip         : $(pip --version 2>&1)"
    dbg "  ansible     : $(ansible --version 2>&1 | head -1 || echo 'not found')"
    dbg "  molecule    : $(molecule --version 2>&1 | head -1 || echo 'not found')"
    dbg "  pytest      : $(pytest --version 2>&1 | head -1 || echo 'not found')"
fi

# ═════════════════════════════════════════════════════════════════════════════
# MAKE SCRIPTS EXECUTABLE
# ═════════════════════════════════════════════════════════════════════════════

if [ -f "${PREREQ_SCRIPT}" ]; then
    chmod +x "${PREREQ_SCRIPT}"
    dbg "Made executable: ${PREREQ_SCRIPT}"
fi
if [ -f "${MOLECULE_SCRIPT}" ]; then
    chmod +x "${MOLECULE_SCRIPT}"
    dbg "Made executable: ${MOLECULE_SCRIPT}"
fi

# ═════════════════════════════════════════════════════════════════════════════
# REGISTER ALIASES AND TAB-COMPLETION IN VENV ACTIVATE
# ═════════════════════════════════════════════════════════════════════════════
# Inject into .venv/bin/activate so that `source .venv/bin/activate` gives:
#   - run_molecule  command (no ./ needed)
#   - run_prereq    command (no ./ needed)
#   - Tab completion for run_molecule (scenarios + commands)

ACTIVATE_SCRIPT="${VENV_DIR}/bin/activate"
MARKER="# >>> omnia-automation >>>"
MARKER_END="# <<< omnia-automation <<<"

# Remove any previous omnia block (idempotent)
if grep -q "${MARKER}" "${ACTIVATE_SCRIPT}" 2>/dev/null; then
    sed -i "/${MARKER}/,/${MARKER_END}/d" "${ACTIVATE_SCRIPT}"
    dbg "Removed previous omnia block from activate script"
fi

cat >> "${ACTIVATE_SCRIPT}" << 'OMNIA_ACTIVATE_EOF'

# >>> omnia-automation >>>
# Added by setup_env.sh — shell functions and tab-completion for Omnia Automation

# Shell function so run_molecule works without ./
run_molecule() {
    "${VIRTUAL_ENV%/.venv}/run_molecule.sh" "$@"
}

# Tab-completion for run_molecule
_run_molecule_completions() {
    local cur prev
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    local mol_dir="${VIRTUAL_ENV%/.venv}/molecule"
    local scenarios=""
    if [ -d "${mol_dir}" ]; then
        for d in "${mol_dir}"/*/molecule.yml; do
            [ -f "$d" ] || continue
            scenarios="${scenarios} $(basename "$(dirname "$d")")"
        done
    fi
    local commands="test verify converge create prepare"
    local special="all list help"
    case "$COMP_CWORD" in
        1) COMPREPLY=( $(compgen -W "${scenarios} ${special}" -- "$cur") ) ;;
        2)
            case "$prev" in
                list|help|--help|-h) COMPREPLY=() ;;
                *) COMPREPLY=( $(compgen -W "${commands}" -- "$cur") ) ;;
            esac ;;
    esac
}
complete -F _run_molecule_completions run_molecule

# <<< omnia-automation <<<
OMNIA_ACTIVATE_EOF

ok "Registered run_molecule alias and tab-completion in venv activate"
dbg "Injected into: ${ACTIVATE_SCRIPT}"

# ═════════════════════════════════════════════════════════════════════════════
# NEXT STEPS
# ═════════════════════════════════════════════════════════════════════════════

echo ""
separator
printf "${C_BOLD}${C_GREEN}  Setup Complete${C_RESET}\n"
separator
echo ""
printf "  ${C_WHITE}${C_BOLD}Next Steps:${C_RESET}\n"
echo ""
printf "  ${C_CYAN}1.${C_RESET} Edit the user configuration file:\n"
printf "     ${C_DIM}vi ${USER_CONFIG}${C_RESET}\n"
echo ""
printf "  ${C_CYAN}2.${C_RESET} Fill the inputs in the project_default/ folder:\n"
printf "     ${C_DIM}ls project_default/${C_RESET}\n"
printf "     ${C_DIM}# Contains: software_config.json, telemetry_config.yml, provision_config.yml,${C_RESET}\n"
printf "     ${C_DIM}#           pxe_mapping_file.csv, omnia_config.yml, local_repo_config.yml, etc.${C_RESET}\n"
printf "     ${C_DIM}# For verify-only runs, filling inputs is not required.${C_RESET}\n"
echo ""
printf "  ${C_CYAN}3.${C_RESET} Activate the virtual environment (if not already):\n"
printf "     ${C_DIM}source .venv/bin/activate${C_RESET}\n"
echo ""
printf "  ${C_CYAN}4.${C_RESET} Run OIM prerequisite checks:\n"
printf "     ${C_DIM}oim-prereq-check                       ${C_RESET}${C_DIM}# run all checks${C_RESET}\n"
printf "     ${C_DIM}oim-prereq-check --debug                ${C_RESET}${C_DIM}# verbose output${C_RESET}\n"
printf "     ${C_DIM}oim-prereq-check --continue-on-failure  ${C_RESET}${C_DIM}# don't stop on first failure${C_RESET}\n"
echo ""
printf "  ${C_CYAN}5.${C_RESET} Run molecule tests:\n"
printf "     ${C_DIM}run_molecule all test                   ${C_RESET}${C_DIM}# run all modules (playbook + verify)${C_RESET}\n"
printf "     ${C_DIM}run_molecule all verify                 ${C_RESET}${C_DIM}# verify-only for all modules${C_RESET}\n"
printf "     ${C_DIM}run_molecule discovery verify           ${C_RESET}${C_DIM}# verify a specific module${C_RESET}\n"
printf "     ${C_DIM}run_molecule telemetry test             ${C_RESET}${C_DIM}# playbook + verify for a module${C_RESET}\n"
printf "     ${C_DIM}run_molecule list                       ${C_RESET}${C_DIM}# list available modules${C_RESET}\n"
echo ""

separator
echo ""
