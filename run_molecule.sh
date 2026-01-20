#!/bin/bash
# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
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
# Usage:
#   ./run_molecule.sh <scenario> <command>
#   ./run_molecule.sh all <command>              # Run install + prepare_oim
#
# Commands:
#   test      - Run full test (create + prepare + converge + verify)
#   verify    - Run verification tests only
#   converge  - Run converge only (install/cleanup action)
#   create    - Create inventory only
#   prepare   - Run prepare only
#   list      - List available scenarios
#
# Scenarios:
#   omnia_sh_install - Install omnia.sh and verify
#   omnia_sh_cleanup - Cleanup omnia.sh and verify
#   prepare_oim      - Prepare OIM and verify
#   build_image      - Build image playbook and verify
#   telemetry        - Run telemetry playbook and verify
#   all              - Run omnia_sh_install + prepare_oim + build_image (not cleanup)
#   (more scenarios can be added)
#
# Examples:
#   ./run_molecule.sh omnia_sh_install test      # Install + verify
#   ./run_molecule.sh omnia_sh_install verify    # Verify install only
#   ./run_molecule.sh omnia_sh_cleanup test      # Cleanup + verify
#   ./run_molecule.sh all test                   # Run ALL scenarios
#   ./run_molecule.sh list                       # List scenarios
#
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Change to script directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Parse arguments
SCENARIO="$1"
COMMAND="$2"

# Handle special commands that don't need scenario
case "$SCENARIO" in
    list|--list)
        echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
        echo -e "${BLUE}  Available Molecule Scenarios${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
        echo ""
        # Display in logical order
        ORDERED_SCENARIOS="omnia_sh_install prepare_oim local_repo build_image telemetry omnia_sh_cleanup"
        for name in $ORDERED_SCENARIOS; do
            if [[ -d "molecule/${name}" && -f "molecule/${name}/molecule.yml" ]]; then
                echo -e "  ${GREEN}${name}${NC}"
            fi
        done
        echo ""
        exit 0
        ;;
    
    help|--help|-h|"")
        echo "Usage: $0 <scenario> <command>"
        echo ""
        echo "Commands:"
        echo "  test      - Run full test (create + prepare + converge + verify)"
        echo "  verify    - Run verification tests only"
        echo "  converge  - Run converge only"
        echo "  create    - Create inventory only"
        echo "  prepare   - Run prepare only"
        echo ""
        echo "Scenarios:"
        echo "  <name>    - Run specific scenario"
        echo "  all       - Run omnia_sh_install + prepare_oim (not cleanup)"
        echo ""
        echo "Special Commands:"
        echo "  list      - List available scenarios"
        echo "  help      - Show this help"
        echo ""
        echo "Examples:"
        echo "  $0 omnia_sh_install test      # Install + verify"
        echo "  $0 omnia_sh_install verify    # Verify install only"
        echo "  $0 omnia_sh_cleanup test      # Cleanup + verify"
        echo "  $0 prepare_oim test           # Prepare OIM + verify"
        echo "  $0 build_image test           # Build image + verify"
        echo "  $0 telemetry test             # Telemetry + verify"
        echo "  $0 telemetry verify           # Verify telemetry only"
        echo "  $0 all test                   # Run ALL scenarios"
        echo "  $0 list                       # List scenarios"
        exit 0
        ;;
    
    all)
        # Run all scenarios with shared report ID
        # Order: install scenarios first, then cleanup scenarios
        COMMAND="${COMMAND:-test}"
        export OMNIA_REPORT_ID=$(cat /proc/sys/kernel/random/uuid | cut -c1-8)
        
        echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
        echo -e "${BLUE}  Omnia Molecule Test Runner - ALL SCENARIOS${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
        echo -e "  Command   : ${GREEN}${COMMAND}${NC}"
        echo -e "  Report ID : ${GREEN}${OMNIA_REPORT_ID}${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
        echo ""
        
        # Build ordered list: omnia_sh_install first, then prepare_oim
        # Note: cleanup scenarios are NOT included in "all" - run them explicitly
        SCENARIOS="omnia_sh_install prepare_oim local_repo build_image"
        
        FAILED=0
        for name in $SCENARIOS; do
            echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo -e "${YELLOW}➜ Running: ${name} ${COMMAND}${NC}"
            echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo ""
            
            # Create log file for this scenario
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
    echo "Run '$0 list' to see available scenarios."
    exit 1
fi

# Default command
COMMAND="${COMMAND:-test}"

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Omnia Molecule Test Runner${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "  Scenario : ${GREEN}${SCENARIO}${NC}"
echo -e "  Command  : ${GREEN}${COMMAND}${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

case "$COMMAND" in
    test)
        echo -e "${YELLOW}➜ Running full test...${NC}"
        echo ""
        LOG_FILE="/tmp/molecule_${SCENARIO}_${OMNIA_REPORT_ID:-$(date +%s)}.log"
        export MOLECULE_LOG_FILE="$LOG_FILE"
        export MOLECULE_COMMAND="test"
        molecule test -s "$SCENARIO" 2>&1 | tee "$LOG_FILE"
        echo ""
        echo -e "${GREEN}✔ Test completed.${NC}"
        ;;
    
    verify)
        echo -e "${YELLOW}➜ Running verification tests only...${NC}"
        echo ""
        LOG_FILE="/tmp/molecule_${SCENARIO}_${OMNIA_REPORT_ID:-$(date +%s)}.log"
        export MOLECULE_LOG_FILE="$LOG_FILE"
        export MOLECULE_COMMAND="verify"
        molecule verify -s "$SCENARIO" 2>&1 | tee "$LOG_FILE"
        echo ""
        echo -e "${GREEN}✔ Verify completed.${NC}"
        ;;
    
    converge)
        echo -e "${YELLOW}➜ Running converge...${NC}"
        echo ""
        LOG_FILE="/tmp/molecule_${SCENARIO}_${OMNIA_REPORT_ID:-$(date +%s)}.log"
        export MOLECULE_LOG_FILE="$LOG_FILE"
        export MOLECULE_COMMAND="converge"
        molecule converge -s "$SCENARIO" 2>&1 | tee "$LOG_FILE"
        echo ""
        echo -e "${GREEN}✔ Converge completed.${NC}"
        ;;
    
    create)
        echo -e "${YELLOW}➜ Creating inventory...${NC}"
        echo ""
        molecule create -s "$SCENARIO"
        echo ""
        echo -e "${GREEN}✔ Create completed.${NC}"
        ;;
    
    prepare)
        echo -e "${YELLOW}➜ Running prepare...${NC}"
        echo ""
        molecule prepare -s "$SCENARIO"
        echo ""
        echo -e "${GREEN}✔ Prepare completed.${NC}"
        ;;
    
    *)
        echo -e "${RED}Unknown command: $COMMAND${NC}"
        echo "Run '$0 help' for usage."
        exit 1
        ;;
esac
