#!/bin/bash
# =============================================================================
# Molecule Test Runner for Omnia Automation Framework
# =============================================================================
#
# Usage:
#   ./run_molecule.sh [command] [scenario]
#
# Commands:
#   test      - Run tests (install + verify, NO cleanup) [DEFAULT]
#   full      - Run full cycle (install + verify + cleanup)
#   verify    - Run verification tests only (container must exist)
#   install   - Run omnia.sh --install only
#   cleanup   - Run omnia.sh --uninstall only
#   status    - Check container status on OIM server
#
# Scenarios:
#   omnia_sh  - Test omnia.sh script [DEFAULT]
#
# Examples:
#   ./run_molecule.sh                    # Default: test omnia_sh
#   ./run_molecule.sh test               # Install + verify (keeps container)
#   ./run_molecule.sh full               # Full cycle with cleanup
#   ./run_molecule.sh verify             # Verify only
#   ./run_molecule.sh cleanup            # Cleanup only
#   ./run_molecule.sh status             # Check container status
#
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
COMMAND="${1:-test}"
SCENARIO="${2:-omnia_sh}"

# Change to script directory
cd "$(dirname "$0")"

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Omnia Molecule Test Runner${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "  Command  : ${GREEN}${COMMAND}${NC}"
echo -e "  Scenario : ${GREEN}${SCENARIO}${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

case "$COMMAND" in
    test)
        echo -e "${YELLOW}➜ Running test (install + verify, NO cleanup)...${NC}"
        echo -e "${YELLOW}  Container will remain running after tests.${NC}"
        echo ""
        molecule test -s "$SCENARIO"
        echo ""
        echo -e "${GREEN}✔ Test completed. Container is still running.${NC}"
        echo -e "${YELLOW}  Run './run_molecule.sh cleanup' to remove container.${NC}"
        ;;
    
    full)
        echo -e "${YELLOW}➜ Running full cycle (install + verify + cleanup)...${NC}"
        echo ""
        molecule test -s "$SCENARIO"
        molecule cleanup -s "$SCENARIO"
        echo ""
        echo -e "${GREEN}✔ Full cycle completed. Container removed.${NC}"
        ;;
    
    verify)
        echo -e "${YELLOW}➜ Running verification tests only...${NC}"
        echo ""
        molecule verify -s "$SCENARIO"
        ;;
    
    install|converge)
        echo -e "${YELLOW}➜ Running omnia.sh --install...${NC}"
        echo ""
        molecule converge -s "$SCENARIO"
        echo ""
        echo -e "${GREEN}✔ Install completed.${NC}"
        ;;
    
    cleanup|destroy|uninstall)
        echo -e "${YELLOW}➜ Running omnia.sh --uninstall...${NC}"
        echo ""
        molecule cleanup -s "$SCENARIO"
        echo ""
        echo -e "${GREEN}✔ Cleanup completed. Container removed.${NC}"
        ;;
    
    status)
        echo -e "${YELLOW}➜ Checking container status on OIM server...${NC}"
        echo ""
        # Load config
        OIM_IP=$(grep "oim_server_ip:" user_config.yml | awk '{print $2}' | tr -d '"')
        OIM_PASS=$(grep "oim_ssh_password:" user_config.yml | awk '{print $2}' | tr -d '"')
        
        echo -e "  OIM Server: ${GREEN}${OIM_IP}${NC}"
        echo ""
        
        sshpass -p "$OIM_PASS" ssh -o StrictHostKeyChecking=no root@"$OIM_IP" \
            "echo '=== Container Status ===' && podman ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}' | grep -E 'NAMES|omnia' || echo 'No omnia containers found'"
        ;;
    
    create)
        echo -e "${YELLOW}➜ Creating inventory...${NC}"
        molecule create -s "$SCENARIO"
        ;;
    
    prepare)
        echo -e "${YELLOW}➜ Running prepare (prerequisites check)...${NC}"
        molecule prepare -s "$SCENARIO"
        ;;
    
    help|--help|-h)
        echo "Usage: $0 [command] [scenario]"
        echo ""
        echo "Commands:"
        echo "  test      - Run tests (install + verify, NO cleanup) [DEFAULT]"
        echo "  full      - Run full cycle (install + verify + cleanup)"
        echo "  verify    - Run verification tests only"
        echo "  install   - Run omnia.sh --install only"
        echo "  cleanup   - Run omnia.sh --uninstall only"
        echo "  status    - Check container status on OIM server"
        echo "  create    - Create inventory only"
        echo "  prepare   - Run prerequisites check"
        echo ""
        echo "Scenarios:"
        echo "  omnia_sh  - Test omnia.sh script [DEFAULT]"
        ;;
    
    *)
        echo -e "${RED}Unknown command: $COMMAND${NC}"
        echo "Run '$0 help' for usage."
        exit 1
        ;;
esac
