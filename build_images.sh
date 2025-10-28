#!/bin/bash

# Define color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[34m'
YELLOW='\033[1;33m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Arrays to store build status
SUCCESSFUL_BUILDS=()
FAILED_BUILDS=()

# Function to build omnia_core image
build_omnia_core() {
    echo "Building omnia_core image..."
    echo -e "Using Omnia branch: ${YELLOW}${OMNIA_VERSION}${NC}"
    echo -e "Using Build Tool: ${YELLOW}${BUILD_TOOL}${NC}"
    echo -e "${RED}---------------------------------${NC}"
    cd "$OMNIA_CORE_DIR" || exit
    if [ "$BUILD_TOOL" = "podman" ]; then
        podman build --build-arg OMNIA_VERSION="$OMNIA_VERSION" -t omnia_core:latest -f Dockerfile
    elif [ "$BUILD_TOOL" = "docker" ]; then
	if [ "$BUILD_ACTION" = "load" ]; then
	    docker buildx build --no-cache --build-arg OMNIA_VERSION="$OMNIA_VERSION" -t omnia_core:latest --file Dockerfile --platform linux/amd64 --load .
	elif [ "$BUILD_ACTION" = "push" ]; then
	    docker buildx build   --build-arg OMNIA_VERSION="pub/ochami" -t docker.io/dellhpcomniaaisolution/omnia_core:latest --file Dockerfile --platform linux/amd64 --provenance=true --sbom=true  --push .
	else
            echo -e "${RED}Invalid BUILD_ACTION. Please enter 'load' or 'push'.${NC}"
            exit 1
        fi
    else
        echo -e "${RED}Invalid BUILD_TOOL. Please enter 'podman' or 'docker'.${NC}"
        exit 1
    fi
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}omnia_core image built successfully.${NC}"
        SUCCESSFUL_BUILDS+=("omnia_core")
    else
        echo -e "${RED}omnia_core image build failed.${NC}"
        FAILED_BUILDS+=("omnia_core")
    fi
    cd - || exit
}

# Function to build omnia_provision image
build_omnia_provision() {
    echo "Building omnia_provision image..."
    cd "$PROVISION_DIR" || exit
    podman build --build-arg xcat_version="$XCAT_VERSION" --cap-add=ALL -t omnia_provision:latest -f Dockerfile
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}omnia_provision image built successfully.${NC}"
        SUCCESSFUL_BUILDS+=("omnia_provision")
    else
        echo -e "${RED}omnia_provision image build failed.${NC}"
        FAILED_BUILDS+=("omnia_provision")
    fi
    cd - || exit
}

# Function to build omnia_pcs image
build_omnia_pcs() {
    echo "Building omnia_pcs image..."
    cd "$PCS_CONTAINER_DIR" || exit
    podman build -t omnia_pcs:latest -f Dockerfile
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}omnia_pcs image built successfully.${NC}"
        SUCCESSFUL_BUILDS+=("omnia_pcs")
    else
        echo -e "${RED}omnia_pcs image build failed.${NC}"
        FAILED_BUILDS+=("omnia_pcs")
    fi
    cd - || exit
}

# Function to build omnia_kubespray image
build_omnia_kubespray() {
    echo "Building omnia_kubespray image..."
    # Check if the argument is provided in the format kubespray_version=v2.27.0
    echo -e "Using Kubespray version: ${YELLOW}${KUBESPRAY_VERSION}${NC}"
    echo -e "${RED}---------------------------------${NC}"
    cd "$KUBESPRAY_DIR" || exit
    if [ "$BUILD_TOOL" = "podman" ]; then
        podman build --build-arg KUBESPRAY_VERSION="$KUBESPRAY_VERSION" --build-arg SSH_PORT="$SSH_PORT" -t "omnia_kubespray:$KUBESPRAY_VERSION" -f Dockerfile
    elif [ "$BUILD_TOOL" = "docker" ]; then
        if [ "$BUILD_ACTION" = "load" ]; then
            docker buildx build --no-cache --build-arg  KUBESPRAY_VERSION="$KUBESPRAY_VERSION" --build-arg SSH_PORT="$SSH_PORT" -t "omnia_kubespray:$KUBESPRAY_VERSION" --file Dockerfile --platform linux/amd64 --load .
        elif [ "$BUILD_ACTION" = "push" ]; then
            docker buildx build --no-cache --build-arg  KUBESPRAY_VERSION="$KUBESPRAY_VERSION" --build-arg SSH_PORT="$SSH_PORT" -t "omnia_kubespray:$KUBESPRAY_VERSION" --file Dockerfile --platform linux/amd64  --provenance=true --sbom=true --push .
        else
            echo -e "${RED}Invalid BUILD_ACTION. Please enter 'load' or 'push'.${NC}"
            exit 1
        fi
    else
        echo -e "${RED}Invalid BUILD_TOOL. Please enter 'podman' or 'docker'.${NC}"
        exit 1
    fi

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}omnia_kubespray image built successfully.${NC}"
        SUCCESSFUL_BUILDS+=("omnia_kubespray")
    else
        echo -e "${RED}omnia_kubespray image build failed.${NC}"
        FAILED_BUILDS+=("omnia_kubespray")
    fi
    cd - || exit
}

build_omnia_auth() {
    echo "Building omnia_auth image..."
    cd "$AUTH_DIR" || exit
    if [ "$BUILD_TOOL" = "podman" ]; then
        podman build -t omnia_auth:latest -f Dockerfile
    elif [ "$BUILD_TOOL" = "docker" ]; then
        if [ "$BUILD_ACTION" = "load" ]; then
            docker buildx build -t docker.io/dellhpcomniaaisolution/omnia_auth:latest --file Dockerfile --platform linux/amd64 --load .
        elif [ "$BUILD_ACTION" = "push" ]; then
            docker buildx build -t docker.io/dellhpcomniaaisolution/omnia_auth:latest --file Dockerfile --platform linux/amd64 --provenance=true --sbom=true  --push .
        else
            echo -e "${RED}Invalid BUILD_ACTION. Please enter 'load' or 'push'.${NC}"
            exit 1
        fi
    else
        echo -e "${RED}Invalid BUILD_TOOL. Please enter 'podman' or 'docker'.${NC}"
        exit 1
    fi

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}omnia_auth image built successfully.${NC}"
        SUCCESSFUL_BUILDS+=("omnia_auth")
    else
        echo -e "${RED}omnia_auth image build failed.${NC}"
        FAILED_BUILDS+=("omnia_auth")
    fi
    cd - || exit
}

# Default parameterized values
OMNIA_VERSION="pub/ochami"
KUBESPRAY_VERSION='v2.28.0'
BUILD_TOOL="podman"
BUILD_ACTION="load"
DOCKER_REGISTERY="docker.io/dellhpcomniaaisolution/"

# Parse command line arguments
for arg in "$@"; do
    if [[ "$arg" =~ ^omnia_branch=.*$ ]]; then
        OMNIA_VERSION="${arg#omnia_branch=}"
    elif [[ "$arg" =~ ^kubespray_version=.*$ ]]; then
        KUBESPRAY_VERSION="${arg#kubespray_version=}"
    elif [[ "$arg" =~ ^build_tool=.*$ ]]; then
        BUILD_TOOL="${arg#build_tool=}"
    elif [[ "$arg" =~ ^build_action=.*$ ]]; then
        BUILD_ACTION="${arg#build_action=}"

    fi
done

# Set SSH_PORT based on KUBESPRAY_VERSION
case "$KUBESPRAY_VERSION" in
  v2.26.0)
    SSH_PORT="2226"
    ;;
  v2.27.0)
    SSH_PORT="2227"
    ;;
  v2.28.0)
    SSH_PORT="2228"
    ;;
  *)
    echo "Error: Unknown or unsupported KUBESPRAY_VERSION: $KUBESPRAY_VERSION. Supported versions are v2.26.0, v2.27.0, v2.28.0"
    exit 1
    ;;
esac

# Omnia core container variables
OMNIA_CORE_DIR="ContainerFile/omnia_core"

# PCS container variables
PCS_CONTAINER_DIR="ContainerFile/pcs_container"

# Kubespray container variables
KUBESPRAY_DIR="ContainerFile/kubespray"

# Provision container variables
PROVISION_DIR="ContainerFile/provision/files"
XCAT_VERSION="2.17"
PROVISION_IMAGE_FILE="omnia_provision"
PROVISION_IMAGE_NAME="omnia_provision"

# Auth container variables
AUTH_DIR="ContainerFile/auth"

# Parse command line arguments
if [[ $# -eq 0 || "$1" == "all" ]]; then
    # Build all containers
    build_omnia_core
    build_omnia_auth
    build_omnia_kubespray
else
    # Loop through each container specified in the arguments and build
    IFS=',' read -r -a containers <<< "$1"
    for container in "${containers[@]}"; do
        case "$container" in
            provision)
                build_omnia_provision
                ;;
            core)
                build_omnia_core
                ;;
            pcs)
                build_omnia_pcs
                ;;
            kubespray)
                build_omnia_kubespray
                ;;
            auth)
                build_omnia_auth
                ;;
            pipeline)
                build_omnia_core
                build_omnia_kubespray
                build_omnia_auth
                ;;
            *)
                echo -e "${RED}Invalid container: $container. Available options: provision, core, pcs, kubespray.${NC}"
                exit 1
                ;;
        esac
    done
fi

# Summary of builds
echo -e "\n${BLUE}Build Summary:${NC}"
if [ ${#SUCCESSFUL_BUILDS[@]} -ne 0 ]; then
    echo -e "${GREEN}Successfully built:${YELLOW} ${SUCCESSFUL_BUILDS[*]} ${NC}"

    # Check if omnia_core is successfully built and show the next steps for the user
    if [[ " ${SUCCESSFUL_BUILDS[*]} " =~ " omnia_core " ]]; then
        echo -e "\n${GREEN}omnia_core image built successfully!${NC}"
        echo -e "${YELLOW}Next steps:${NC}"
        echo -e "1. Download the omnia.sh script:"
        echo -e "   ${BLUE}If you're using a tagged version of Omnia, run the following command: wget https://raw.githubusercontent.com/dell/omnia/refs/tags/${OMNIA_VERSION}/omnia.sh${NC}"
        echo -e "   ${BLUE}If you're using a specific branch of Omnia, run the following command: wget https://raw.githubusercontent.com/dell/omnia/refs/heads/${OMNIA_VERSION}/omnia.sh${NC}"
        echo -e "2. Make the script executable:"
        echo -e "   ${BLUE}chmod +x omnia.sh${NC}"
        echo -e "3. Execute the script to create the core container and configure passwordless SSH:"
        echo -e "   ${BLUE}./omnia.sh --install${NC}"
    fi
fi
if [ ${#FAILED_BUILDS[@]} -ne 0 ]; then
    echo -e "${RED}Failed builds:${MAGENTA} ${FAILED_BUILDS[*]} ${NC}"
    exit 1
else
    echo -e "${GREEN}All requested images built successfully!${NC}"
fi
