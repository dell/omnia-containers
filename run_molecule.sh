#!/bin/bash
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
#   all              - Run omnia_sh_install + prepare_oim (not cleanup)
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
        # List top-level scenarios
        for dir in molecule/*/; do
            if [[ -f "${dir}molecule.yml" ]]; then
                name=$(basename "$dir")
                echo -e "  ${GREEN}${name}${NC}"
            fi
            # Check for nested scenarios (e.g., slurm/pam_slurm_adopt)
            for subdir in "${dir}"*/; do
                if [[ -f "${subdir}molecule.yml" ]]; then
                    parent=$(basename "$dir")
                    child=$(basename "$subdir")
                    echo -e "  ${GREEN}${parent}/${child}${NC}"
                fi
            done
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
        SCENARIOS="omnia_sh_install prepare_oim"
        
        FAILED=0
        for name in $SCENARIOS; do
            echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo -e "${YELLOW}➜ Running: ${name} ${COMMAND}${NC}"
            echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo ""
            
            if molecule "${COMMAND}" -s "${name}"; then
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

# Check if this is a nested scenario (e.g., slurm/pam_slurm_adopt)
# Molecule requires the scenario name to be the leaf directory name
# and we need to set the base config path
if [[ "$SCENARIO" == */* ]]; then
    # Nested scenario - extract parent and child
    PARENT_DIR=$(dirname "$SCENARIO")
    SCENARIO_NAME=$(basename "$SCENARIO")
    export MOLECULE_BASE_CONFIG="molecule/${PARENT_DIR}/molecule.yml"
    MOLECULE_SCENARIO_DIR="molecule/${SCENARIO}"
else
    SCENARIO_NAME="$SCENARIO"
    MOLECULE_SCENARIO_DIR="molecule/${SCENARIO}"
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

# Function to run molecule with proper path handling
run_molecule() {
    local cmd="$1"
    if [[ "$SCENARIO" == */* ]]; then
        # For nested scenarios, we need to temporarily symlink or use MOLECULE_GLOB
        # Molecule expects scenarios directly under molecule/ directory
        # Solution: Create a temporary symlink
        local LINK_NAME="${SCENARIO_NAME}"
        local LINK_PATH="molecule/${LINK_NAME}"
        local TARGET_PATH="${SCENARIO}"
        
        # Remove existing symlink if it exists
        [[ -L "$LINK_PATH" ]] && rm "$LINK_PATH"
        
        # Create symlink from molecule/<scenario_name> -> <parent>/<scenario_name>
        ln -sf "${TARGET_PATH#molecule/}" "$LINK_PATH" 2>/dev/null || ln -sf "../molecule/${TARGET_PATH}" "$LINK_PATH"
        
        # Run molecule
        molecule "$cmd" -s "$SCENARIO_NAME"
        local result=$?
        
        # Cleanup symlink
        [[ -L "$LINK_PATH" ]] && rm "$LINK_PATH"
        
        return $result
    else
        molecule "$cmd" -s "$SCENARIO_NAME"
    fi
}

case "$COMMAND" in
    test)
        echo -e "${YELLOW}➜ Running full test...${NC}"
        echo ""
        run_molecule test
        echo ""
        echo -e "${GREEN}✔ Test completed.${NC}"
        ;;
    
    verify)
        echo -e "${YELLOW}➜ Running verification tests only...${NC}"
        echo ""
        run_molecule verify
        echo ""
        echo -e "${GREEN}✔ Verify completed.${NC}"
        ;;
    
    converge)
        echo -e "${YELLOW}➜ Running converge...${NC}"
        echo ""
        run_molecule converge
        echo ""
        echo -e "${GREEN}✔ Converge completed.${NC}"
        ;;
    
    create)
        echo -e "${YELLOW}➜ Creating inventory...${NC}"
        echo ""
        run_molecule create
        echo ""
        echo -e "${GREEN}✔ Create completed.${NC}"
        ;;
    
    prepare)
        echo -e "${YELLOW}➜ Running prepare...${NC}"
        echo ""
        run_molecule prepare
        echo ""
        echo -e "${GREEN}✔ Prepare completed.${NC}"
        ;;
    
    *)
        echo -e "${RED}Unknown command: $COMMAND${NC}"
        echo "Run '$0 help' for usage."
        exit 1
        ;;
esac
