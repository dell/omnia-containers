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
# Molecule Test Runner for Omnia Automation Framework
# =============================================================================
#
# Tab completion is enabled automatically after: source .venv/bin/activate
#   run_molecule <TAB>              # Shows scenarios
#   run_molecule discovery <TAB>    # Shows commands
#
# Usage:
#   ./run_molecule.sh <scenario> <command> [options]
#   ./run_molecule.sh --config                         # Run from test_run_config.yml
#   ./run_molecule.sh all <command>              # Run install + prepare_oim
#   ./run_molecule.sh all verify --flow build_stream  # Run full build_stream flow
#
# Commands:
#   test      - Run full test (create + prepare + converge + verify)
#   verify    - Run verification tests only
#   converge  - Run converge only (install/cleanup action)
#   create    - Create inventory only
#   prepare   - Run prepare only
#   list      - List available scenarios
#
# Options:
#   --suite <name>    Run specific test suite (sanity, negative, regression, smoke)
#   --marker <expr>   Run tests matching pytest marker expression
#   --flow <name>     Run a predefined scenario flow (e.g. build_stream)
#
# Test Suites:
#   sanity      - Basic functionality tests (quick validation)
#   negative    - Error handling and edge cases
#   regression  - Full test coverage
#   smoke       - Critical path only (fastest)
#
# Scenarios (in execution order):
#   omnia_sh_install    - Install omnia.sh and verify
#   prepare_oim         - Prepare OIM and verify
#   gitlab_install      - Run GitLab playbook and verify
#   local_repo          - Verify local repo
#   build_image_x86_64  - Build x86_64 images and verify
#   build_image_aarch64 - Build aarch64 images and verify
#   discovery           - Run discovery playbook and verify
#   telemetry           - Run telemetry playbook and verify
#   one_shot_log_extraction - Run one-shot log extraction and verify
#   gitlab_cleanup      - Run GitLab cleanup and verify
#   oim_cleanup         - Run OIM cleanup and verify
#   omnia_sh_uninstall  - Uninstall omnia.sh and verify
#   all                 - Run all scenarios in order (not cleanup)
#   build_stream        - Run Build Stream CI/CD pipeline tests
#
# Flows (use with 'all --flow <name>'):
#   build_stream        - omnia_sh_install → prepare_oim → gitlab_install → build_stream verify
#
# Examples:
#   ./run_molecule.sh omnia_sh_install test      # Install + verify
#   ./run_molecule.sh omnia_sh_install verify    # Verify install only
#   ./run_molecule.sh omnia_sh_uninstall test    # Cleanup + verify
#   ./run_molecule.sh all test                          # Run ALL scenarios
#   ./run_molecule.sh all verify --flow build_stream  # Run build_stream flow
#   ./run_molecule.sh build_stream verify --suite build_auto   # Run build_auto suite
#   ./run_molecule.sh list                                # List scenarios
#   ./run_molecule.sh prepare_oim verify --suite sanity    # Run sanity tests only
#   ./run_molecule.sh gitlab_install verify --suite sanity # Run GitLab install sanity tests
#   ./run_molecule.sh gitlab_cleanup verify --suite sanity # Run GitLab cleanup sanity tests
#   ./run_molecule.sh telemetry verify --suite negative    # Run negative tests only
#   ./run_molecule.sh discovery verify --marker smoke      # Run smoke tests
#
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# Supported Values (used for validation and tab-completion)
# =============================================================================
# Add new scenarios, commands, or suites here when extending the framework.

# Supported scenario names (must match directories under molecule/)
SUPPORTED_SCENARIOS="omnia_sh_install prepare_oim gitlab_install local_repo build_image_x86_64 build_image_aarch64 discovery provision telemetry apptainer kubernetes slurm dcgm hpc_benchmarks vast_storage build_stream one_shot_log_extraction gitlab_cleanup oim_cleanup omnia_sh_uninstall"

# Supported molecule commands
SUPPORTED_COMMANDS="test verify converge create prepare"

# Supported run values (boolean)
SUPPORTED_RUN_VALUES="true false"

# Supported test suites (must match directories under molecule/<scenario>/tests/)
SUPPORTED_SUITES="sanity negative regression smoke stress performance build_auto deploy_auto build_manual deploy_manual cleanup_manual"

# Execution order for --config mode and 'all' command
SCENARIO_EXECUTION_ORDER="omnia_sh_install prepare_oim gitlab_install local_repo build_image_x86_64 build_image_aarch64 discovery provision telemetry apptainer kubernetes slurm dcgm hpc_benchmarks vast_storage build_stream one_shot_log_extraction gitlab_cleanup oim_cleanup omnia_sh_uninstall"

# Change to script directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Parse arguments
SCENARIO="$1"
COMMAND="$2"
SUITE=""
MARKER=""
FLOW=""

# Parse optional arguments (--suite, --marker, --flow) only if we have more than 2 args
if [[ $# -gt 2 ]]; then
    shift 2
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --suite)
                SUITE="$2"
                shift 2
                ;;
            --marker)
                MARKER="$2"
                shift 2
                ;;
            --flow)
                FLOW="$2"
                shift 2
                ;;
            *)
                echo -e "${RED}Unknown option: $1${NC}"
                echo "Run '$0 help' for usage."
                exit 1
                ;;
        esac
    done
fi

# Build pytest marker arguments based on --suite or --marker
build_pytest_args() {
    local pytest_args=""
    if [[ -n "$SUITE" ]]; then
        # Convert suite to pytest marker expression
        # sanity -> -m sanity
        # sanity,negative -> -m "sanity or negative"
        if [[ "$SUITE" == *","* ]]; then
            local markers
            markers=$(echo "$SUITE" | sed 's/,/ or /g')
            pytest_args="-m \"$markers\""
        else
            pytest_args="-m $SUITE"
        fi
    fi
    if [[ -n "$MARKER" ]]; then
        pytest_args="-m $MARKER"
    fi
    echo "$pytest_args"
}

# =============================================================================
# Validate test_run_config.yml before execution
# =============================================================================
validate_test_run_config() {
    local config_file="$1"
    echo -e "${BLUE}Validating ${config_file}...${NC}"

    VALIDATION_RESULT=$(python3 << PYEOF
import yaml, sys

SUPPORTED_SCENARIOS = set("${SUPPORTED_SCENARIOS}".split())
SUPPORTED_COMMANDS = set("${SUPPORTED_COMMANDS}".split())
SUPPORTED_RUN_VALUES = {True, False}  # YAML booleans
SUPPORTED_SUITES = set("${SUPPORTED_SUITES}".split()) | {''}  # empty string = all

errors = []
try:
    with open("${config_file}") as f:
        cfg = yaml.safe_load(f) or {}
except Exception as e:
    print(f"ERROR: Failed to parse YAML: {e}")
    sys.exit(1)

for key, value in cfg.items():
    # Skip non-scenario keys (e.g. oim_cleanup_extra_vars)
    if not isinstance(value, dict):
        continue
    if 'run' not in value:
        continue

    # Validate scenario name
    if key not in SUPPORTED_SCENARIOS:
        errors.append(f"  [{key}] Invalid scenario name. Supported: {', '.join(sorted(SUPPORTED_SCENARIOS))}")
        continue

    # Validate 'run' value
    run_val = value.get('run')
    if run_val not in SUPPORTED_RUN_VALUES:
        errors.append(f"  [{key}].run = '{run_val}' is invalid. Must be: true or false")

    # Validate 'command' value
    cmd_val = value.get('command', 'verify')
    if cmd_val not in SUPPORTED_COMMANDS:
        errors.append(f"  [{key}].command = '{cmd_val}' is invalid. Supported: {', '.join(sorted(SUPPORTED_COMMANDS))}")

    # Validate 'suite' value
    suite_val = str(value.get('suite', '') or '')
    # Support comma-separated suites
    for s in suite_val.split(','):
        s = s.strip()
        if s and s not in SUPPORTED_SUITES:
            errors.append(f"  [{key}].suite = '{s}' is invalid. Supported: {', '.join(sorted(SUPPORTED_SUITES - {''}))}")

if errors:
    print("VALIDATION_FAILED")
    for e in errors:
        print(e)
else:
    print("VALIDATION_OK")
PYEOF
)

    # Check result
    if echo "$VALIDATION_RESULT" | head -1 | grep -q "VALIDATION_FAILED"; then
        echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
        echo -e "${RED}  test_run_config.yml VALIDATION FAILED${NC}"
        echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
        echo "$VALIDATION_RESULT" | tail -n +2
        echo ""
        echo -e "${YELLOW}Supported scenarios:${NC}  ${SUPPORTED_SCENARIOS}"
        echo -e "${YELLOW}Supported commands:${NC}   ${SUPPORTED_COMMANDS}"
        echo -e "${YELLOW}Supported run values:${NC} true, false"
        echo -e "${YELLOW}Supported suites:${NC}     ${SUPPORTED_SUITES}"
        echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
        exit 1
    fi
    echo -e "${GREEN}✔ Config validation passed${NC}"
    echo ""
}

# =============================================================================
# --config mode: Read test_run_config.yml and run enabled scenarios
# =============================================================================
if [[ "$SCENARIO" == "--config" || "$SCENARIO" == "config" ]]; then
    CONFIG_FILE="$(dirname "$0")/test_run_config.yml"
    if [[ ! -f "$CONFIG_FILE" ]]; then
        echo -e "${RED}Error: Config file not found: ${CONFIG_FILE}${NC}"
        echo "Create test_run_config.yml and set scenarios to run: true"
        exit 1
    fi

    # Validate config before execution
    validate_test_run_config "$CONFIG_FILE"
    PARSED=$(python3 -c "
import yaml, sys
with open('$CONFIG_FILE') as f:
    cfg = yaml.safe_load(f) or {}
order = '$SCENARIO_EXECUTION_ORDER'.split()
for name in order:
    s = cfg.get(name, {})
    if isinstance(s, dict) and s.get('run', False):
        cmd = s.get('command', 'verify')
        suite = s.get('suite', '') or ''
        print(f'{name}:{cmd}:{suite}')
")

    if [[ -z "$PARSED" ]]; then
        echo -e "${RED}No scenarios enabled in ${CONFIG_FILE}${NC}"
        echo "Edit the file and set scenarios to 'run: true' to enable them."
        exit 1
    fi

    # Export oim_cleanup extra-vars as env vars for converge.yml
    eval "$(python3 -c "
import yaml
with open('$CONFIG_FILE') as f:
    cfg = yaml.safe_load(f) or {}
ev = cfg.get('oim_cleanup_extra_vars', {}) or {}
for k, v in [('slurm_cleanup', 'OIM_CLEANUP_SLURM'),
             ('k8s_cleanup', 'OIM_CLEANUP_K8S'),
             ('postgres_backup', 'OIM_CLEANUP_POSTGRES_BACKUP')]:
    val = str(ev.get(k, '') or '')
    if val:
        print(f'export {v}=\"{val}\"')
st = str(cfg.get('oim_cleanup_skip_tags', '') or '')
if st:
    print(f'export OIM_CLEANUP_SKIP_TAGS=\"{st}\"')
")"

    export OMNIA_REPORT_ID=$(cat /proc/sys/kernel/random/uuid | cut -c1-8)

    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  Omnia Molecule Test Runner - CONFIG MODE${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "  Config    : ${GREEN}${CONFIG_FILE}${NC}"
    echo -e "  Report ID : ${GREEN}${OMNIA_REPORT_ID}${NC}"
    echo -e "${BLUE}───────────────────────────────────────────────────────────────${NC}"
    while IFS=: read -r s_name s_cmd s_suite; do
        printf "  %-30s  %-8s  %s\n" "${s_name}" "${s_cmd}" "${s_suite:-all}"
    done <<< "$PARSED"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""

    FAILED=0
    PASSED_LIST=""
    FAILED_LIST=""

    while IFS=: read -r s_name s_cmd s_suite; do
        echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${YELLOW}➜ ${s_name}  command=${s_cmd}  suite=${s_suite:-all}${NC}"
        echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""

        LOG_FILE="/tmp/molecule_${s_name}_${OMNIA_REPORT_ID}.log"
        export MOLECULE_LOG_FILE="$LOG_FILE"
        export MOLECULE_COMMAND="${s_cmd}"

        # build_stream always uses verify
        run_cmd="$s_cmd"
        if [[ "$s_name" == "build_stream" && "$run_cmd" == "test" ]]; then
            run_cmd="verify"
        fi

        # Set pytest marker for suite with verbose options
        unset PYTEST_ADDOPTS
        local verbose_opts="-v --tb=short -s"
        if [[ -n "$s_suite" ]]; then
            export PYTEST_ADDOPTS="$verbose_opts -m $s_suite"
        else
            export PYTEST_ADDOPTS="$verbose_opts"
        fi

        if molecule "${run_cmd}" -s "${s_name}" 2>&1 | tee "$LOG_FILE"; then
            echo -e "${GREEN}✔ ${s_name} completed${NC}"
            PASSED_LIST="$PASSED_LIST $s_name"
        else
            echo -e "${RED}✘ ${s_name} failed${NC}"
            FAILED=1
            FAILED_LIST="$FAILED_LIST $s_name"
        fi
        echo ""
    done <<< "$PARSED"

    # Summary
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  CONFIG MODE - EXECUTION SUMMARY  (Report: ${OMNIA_REPORT_ID})${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    if [[ -n "$PASSED_LIST" ]]; then
        echo -e "  ${GREEN}✔ Passed:${NC}$PASSED_LIST"
    fi
    if [[ -n "$FAILED_LIST" ]]; then
        echo -e "  ${RED}✘ Failed:${NC}$FAILED_LIST"
    fi
    echo -e "  Logs: /tmp/molecule_*_${OMNIA_REPORT_ID}.log"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

    if [[ $FAILED -eq 0 ]]; then
        echo -e "${GREEN}  ✔ ALL SCENARIOS COMPLETED SUCCESSFULLY${NC}"
    else
        echo -e "${RED}  ✘ SOME SCENARIOS FAILED${NC}"
        exit 1
    fi
    exit 0
fi

# Handle special commands that don't need scenario
case "$SCENARIO" in
    list|--list)
        echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
        echo -e "${BLUE}  Available Molecule Scenarios${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
        echo ""
        # Display in logical order
        ORDERED_SCENARIOS="omnia_sh_install prepare_oim discovery gitlab_install local_repo build_image_x86_64 build_image_aarch64 provision telemetry apptainer build_stream gitlab_cleanup oim_cleanup omnia_sh_uninstall"
        for name in $ORDERED_SCENARIOS; do
            if [[ -d "molecule/${name}" && -f "molecule/${name}/molecule.yml" ]]; then
                echo -e "  ${GREEN}${name}${NC}"
            fi
        done
        echo ""
        exit 0
        ;;
    
    help|--help|-h|"")
        echo "Usage: $0 <scenario> <command> [options]"
        echo "       $0 --config"
        echo ""
        echo "Commands:"
        echo "  test      - Run full test (create + prepare + converge + verify)"
        echo "  verify    - Run verification tests only"
        echo "  converge  - Run converge only"
        echo "  create    - Create inventory only"
        echo "  prepare   - Run prepare only"
        echo ""
        echo "Options:"
        echo "  --suite <name>    Run specific test suite (sanity, negative, regression, smoke)"
        echo "  --marker <expr>   Run tests matching pytest marker expression"
        echo "  --config          Run scenarios from test_run_config.sh"
        echo ""
        echo "Test Suites:"
        echo "  sanity      - Basic functionality tests (quick)"
        echo "  negative    - Error handling and edge cases"
        echo "  regression  - Full test coverage"
        echo "  smoke       - Critical path only (fastest)"
        echo ""
        echo "Scenarios:"
        echo "  <name>    - Run specific scenario"
        echo "  all       - Run all scenarios in order (not cleanup)"
        echo ""
        echo "Special Commands:"
        echo "  list      - List available scenarios"
        echo "  help      - Show this help"
        echo ""
        echo "Config Mode:"
        echo "  Edit test_run_config.yml to enable scenarios, set command & suite."
        echo "  Then run: $0 --config"
        echo ""
        echo "Examples:"
        echo "  $0 omnia_sh_install test       # Install + verify"
        echo "  $0 omnia_sh_install verify     # Verify install only"
        echo "  $0 omnia_sh_uninstall test     # Uninstall + verify"
        echo "  $0 prepare_oim verify --suite sanity     # Run sanity tests only"
        echo "  $0 gitlab_install verify --suite sanity  # Run GitLab install sanity tests"
        echo "  $0 telemetry verify --suite negative     # Run negative tests only"
        echo "  $0 discovery verify --marker smoke       # Run smoke tests"
        echo "  $0 all test                    # Run ALL scenarios"
        echo "  $0 --config                    # Run from test_run_config.yml"
        echo "  $0 list                        # List scenarios"
        exit 0
        ;;
    
    all)
        COMMAND="${COMMAND:-test}"
        export OMNIA_REPORT_ID=$(cat /proc/sys/kernel/random/uuid | cut -c1-8)

        # --flow build_stream: omnia_sh_install -> prepare_oim -> gitlab_install -> build_stream verify
        if [[ "$FLOW" == "build_stream" ]]; then
            echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
            echo -e "${BLUE}  Omnia Molecule Test Runner - BUILD STREAM FLOW${NC}"
            echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
            echo -e "  Flow      : ${GREEN}build_stream${NC}"
            echo -e "  Command   : ${GREEN}${COMMAND}${NC}"
            if [[ -n "$SUITE" ]]; then
                echo -e "  Suite     : ${GREEN}${SUITE}${NC}"
            fi
            echo -e "  Report ID : ${GREEN}${OMNIA_REPORT_ID}${NC}"
            echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
            echo ""
            echo -e "  Flow: omnia_sh_install → prepare_oim → gitlab_install → build_stream verify"
            echo ""

            FAILED=0
            PREREQ_SCENARIOS="omnia_sh_install prepare_oim gitlab_install"

            for name in $PREREQ_SCENARIOS; do
                echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
                echo -e "${YELLOW}➜ Running: ${name} test${NC}"
                echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
                echo ""
                LOG_FILE="/tmp/molecule_${name}_${OMNIA_REPORT_ID}.log"
                export MOLECULE_LOG_FILE="$LOG_FILE"
                export MOLECULE_COMMAND="test"
                if molecule test -s "${name}" 2>&1 | tee "$LOG_FILE"; then
                    echo -e "${GREEN}✔ ${name} completed${NC}"
                else
                    echo -e "${RED}✘ ${name} failed — aborting build_stream flow${NC}"
                    exit 1
                fi
                echo ""
            done

            # Run build_stream verify with optional suite/marker
            echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo -e "${YELLOW}➜ Running: build_stream verify${NC}"
            echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo ""
            LOG_FILE="/tmp/molecule_build_stream_${OMNIA_REPORT_ID}.log"
            export MOLECULE_LOG_FILE="$LOG_FILE"
            export MOLECULE_COMMAND="verify"
            PYTEST_ARGS=$(build_pytest_args)
            if [[ -n "$PYTEST_ARGS" ]]; then
                export PYTEST_ADDOPTS="$PYTEST_ARGS"
                echo -e "  Suite/Marker: ${GREEN}${PYTEST_ARGS}${NC}"
                echo ""
            fi
            if molecule verify -s build_stream 2>&1 | tee "$LOG_FILE"; then
                echo -e "${GREEN}✔ build_stream verify completed${NC}"
            else
                echo -e "${RED}✘ build_stream verify failed${NC}"
                FAILED=1
            fi
            echo ""

            if [[ $FAILED -eq 0 ]]; then
                echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
                echo -e "${GREEN}  ✔ BUILD STREAM FLOW COMPLETED SUCCESSFULLY${NC}"
                echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
            else
                echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
                echo -e "${RED}  ✘ BUILD STREAM FLOW FAILED${NC}"
                echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
                exit 1
            fi
            exit 0
        fi

        # Normal 'all' flow (build_stream excluded — use --flow build_stream)
        echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
        echo -e "${BLUE}  Omnia Molecule Test Runner - ALL SCENARIOS${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
        echo -e "  Command   : ${GREEN}${COMMAND}${NC}"
        echo -e "  Report ID : ${GREEN}${OMNIA_REPORT_ID}${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
        echo ""

        # Note: build_stream is NOT in this list — use: ./run_molecule.sh all verify --flow build_stream
        SCENARIOS="omnia_sh_install prepare_oim discovery local_repo build_image_x86_64 build_image_aarch64 provision telemetry apptainer"

        FAILED=0
        for name in $SCENARIOS; do
            echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo -e "${YELLOW}➜ Running: ${name} ${COMMAND}${NC}"
            echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo ""

            LOG_FILE="/tmp/molecule_${name}_${OMNIA_REPORT_ID:-$(date +%s)}.log"
            export MOLECULE_LOG_FILE="$LOG_FILE"
            export MOLECULE_COMMAND="${COMMAND}"

            if molecule "${COMMAND}" -s "${name}" 2>&1 | tee "$LOG_FILE"; then
                echo -e "${GREEN}✔ ${name} completed${NC}"
            else
                echo -e "${RED}✘ ${name} failed${NC}"
                FAILED=1
            fi
            echo ""
        done

        if [[ $FAILED -eq 0 ]]; then
            echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
            echo -e "${GREEN}  ✔ ALL SCENARIOS COMPLETED SUCCESSFULLY${NC}"
            echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
        else
            echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
            echo -e "${RED}  ✘ SOME SCENARIOS FAILED${NC}"
            echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
            exit 1
        fi
        exit 0
        ;;
esac

# Validate scenario exists
if [[ ! -d "molecule/${SCENARIO}" ]]; then
    echo -e "${RED}Error: Scenario '${SCENARIO}' not found${NC}"
    echo -e "${YELLOW}Supported scenarios:${NC} ${SUPPORTED_SCENARIOS}"
    echo "Run '$0 list' to see available scenarios."
    exit 1
fi

# Default command
COMMAND="${COMMAND:-test}"

# Validate command
if ! echo " ${SUPPORTED_COMMANDS} " | grep -q " ${COMMAND} "; then
    echo -e "${RED}Error: Invalid command '${COMMAND}'${NC}"
    echo -e "${YELLOW}Supported commands:${NC} ${SUPPORTED_COMMANDS}"
    exit 1
fi

# Validate suite if provided
if [[ -n "$SUITE" ]]; then
    for _s in $(echo "$SUITE" | tr ',' ' '); do
        if ! echo " ${SUPPORTED_SUITES} " | grep -q " ${_s} "; then
            echo -e "${RED}Error: Invalid suite '${_s}'${NC}"
            echo -e "${YELLOW}Supported suites:${NC} ${SUPPORTED_SUITES}"
            exit 1
        fi
    done
fi

# For build_stream scenario: always use verify (tests only, no converge needed)
if [[ "$SCENARIO" == "build_stream" && "$COMMAND" == "test" ]]; then
    echo -e "${YELLOW}Note: build_stream uses 'verify' instead of 'test' (no converge step needed)${NC}"
    COMMAND="verify"
fi

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Omnia Molecule Test Runner${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "  Scenario : ${GREEN}${SCENARIO}${NC}"
echo -e "  Command  : ${GREEN}${COMMAND}${NC}"
if [[ -n "$SUITE" ]]; then
    echo -e "  Suite    : ${GREEN}${SUITE}${NC}"
fi
if [[ -n "$MARKER" ]]; then
    echo -e "  Marker   : ${GREEN}${MARKER}${NC}"
fi
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Run molecule command with logging
run_molecule() {
    local cmd="$1"
    local scenario="$2"
    local label="$3"

    echo -e "${YELLOW}➜ ${label}...${NC}"
    echo ""

    LOG_FILE="/tmp/molecule_${scenario}_${OMNIA_REPORT_ID:-$(date +%s)}.log"
    export MOLECULE_LOG_FILE="$LOG_FILE"
    export MOLECULE_COMMAND="${cmd}"

    # Build pytest args for test suite filtering
    local pytest_args
    pytest_args=$(build_pytest_args)
    # Always include verbose pytest options
    local verbose_opts="-v --tb=short -s"
    if [[ -n "$pytest_args" ]]; then
        export PYTEST_ADDOPTS="$verbose_opts $pytest_args"
        echo -e "  Suite/Marker: ${GREEN}${pytest_args}${NC}"
    else
        export PYTEST_ADDOPTS="$verbose_opts"
    fi
    echo ""

    molecule "${cmd}" -s "${scenario}" 2>&1 | tee "$LOG_FILE"
    echo ""
    echo -e "${GREEN}✔ ${label} completed.${NC}"
}

case "$COMMAND" in
    test)     run_molecule test     "$SCENARIO" "Running full test" ;;
    verify)   run_molecule verify   "$SCENARIO" "Running verification tests only" ;;
    converge) run_molecule converge "$SCENARIO" "Running converge" ;;
    create)   run_molecule create   "$SCENARIO" "Creating inventory" ;;
    prepare)  run_molecule prepare  "$SCENARIO" "Running prepare" ;;
    *)
        echo -e "${RED}Unknown command: $COMMAND${NC}"
        echo "Run '$0 help' for usage."
        exit 1
        ;;
esac

# =============================================================================
# Bash Tab Completion
# To enable: source <(./run_molecule.sh --completion)
# Or add to ~/.bashrc: source /root/balaji/omnia-artifactory/.run_molecule_completion.bash
# =============================================================================
if [[ "$1" == "--completion" ]]; then
    cat <<'COMPLETION_SCRIPT'
_run_molecule_completions() {
    local cur prev
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    local scenarios="omnia_sh_install prepare_oim discovery gitlab_install local_repo build_image_x86_64 build_image_aarch64 provision telemetry apptainer build_stream gitlab_cleanup oim_cleanup omnia_sh_uninstall all list help"
    local commands="test verify converge create prepare"
    local suites="sanity negative regression smoke stress build_auto deploy_auto cleanup_manual build_manual deploy_manual"
    local flows="build_stream"

    case "${COMP_CWORD}" in
        1)
            COMPREPLY=($(compgen -W "$scenarios" -- "$cur"))
            ;;
        2)
            COMPREPLY=($(compgen -W "$commands" -- "$cur"))
            ;;
        *)
            case "$prev" in
                --suite) COMPREPLY=($(compgen -W "$suites" -- "$cur")) ;;
                --flow)  COMPREPLY=($(compgen -W "$flows" -- "$cur")) ;;
                *)       COMPREPLY=($(compgen -W "--suite --marker --flow" -- "$cur")) ;;
            esac
            ;;
    esac
}
complete -F _run_molecule_completions run_molecule.sh
complete -F _run_molecule_completions ./run_molecule.sh
COMPLETION_SCRIPT
    exit 0
fi
