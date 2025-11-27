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
LOADED_IMAGES=()
PUSHED_IMAGES=()

# Function to build omnia_core image
build_omnia_core() {
    echo "Building omnia_core image..."
    echo -e "Using Omnia branch: ${YELLOW}${OMNIA_VERSION}${NC}"
    echo -e "Using Build Tool: ${YELLOW}${BUILD_TOOL}${NC}"
    echo -e "Using Build Action: ${YELLOW}${BUILD_ACTION}${NC}"
    echo -e "Using Core Tag: ${YELLOW}${CORE_TAG}${NC}"
    if [ "$BUILD_TOOL" = "docker" ] && [ "$BUILD_ACTION" = "push" ]; then
        echo -e "Registry: ${YELLOW}${OMNIA_DOCKER_REGISTERY}${NC}"
        echo -e "Full Image Name: ${YELLOW}${OMNIA_DOCKER_REGISTERY}/omnia_core:${CORE_TAG}${NC}"
    fi
    echo -e "${RED}---------------------------------${NC}"
    cd "$OMNIA_CORE_DIR" || exit
    if [ "$BUILD_TOOL" = "podman" ]; then
        podman build --build-arg OMNIA_VERSION="$OMNIA_VERSION" -t omnia_core:${CORE_TAG} -f Dockerfile
        BUILD_RESULT=$?
        IMAGE_DESTINATION="Local (Podman): omnia_core:${CORE_TAG}"
    elif [ "$BUILD_TOOL" = "docker" ]; then
	if [ "$BUILD_ACTION" = "load" ]; then
	    docker buildx build --no-cache --build-arg OMNIA_VERSION="$OMNIA_VERSION" -t omnia_core:${CORE_TAG} --file Dockerfile --platform linux/amd64 --load .
	    BUILD_RESULT=$?
	    IMAGE_DESTINATION="Local (Docker): omnia_core:${CORE_TAG}"
	elif [ "$BUILD_ACTION" = "push" ]; then
	    docker buildx build --no-cache --build-arg OMNIA_VERSION="$OMNIA_VERSION" -t "$OMNIA_DOCKER_REGISTERY/omnia_core:${CORE_TAG}" --file Dockerfile --platform linux/amd64 --provenance=true --sbom=true  --push .
	    BUILD_RESULT=$?
	    IMAGE_DESTINATION="Registry: $OMNIA_DOCKER_REGISTERY/omnia_core:${CORE_TAG}"
	else
            echo -e "${RED}Invalid BUILD_ACTION. Please enter 'load' or 'push'.${NC}"
            exit 1
        fi
    else
        echo -e "${RED}Invalid BUILD_TOOL. Please enter 'podman' or 'docker'.${NC}"
        exit 1
    fi
    if [ $BUILD_RESULT -eq 0 ]; then
        echo -e "${GREEN}omnia_core image built successfully.${NC}"
        SUCCESSFUL_BUILDS+=("omnia_core")
        if [ "$BUILD_TOOL" = "docker" ] && [ "$BUILD_ACTION" = "push" ]; then
            PUSHED_IMAGES+=("$IMAGE_DESTINATION")
        else
            LOADED_IMAGES+=("$IMAGE_DESTINATION")
        fi
    else
        echo -e "${RED}omnia_core image build failed.${NC}"
        FAILED_BUILDS+=("omnia_core")
    fi
    cd - || exit
}

# Function to build omnia_provision image
build_omnia_provision() {
    echo "Building omnia_provision image..."
    echo -e "Using Provision Tag: ${YELLOW}${PROVISION_TAG}${NC}"
    cd "$PROVISION_DIR" || exit
    podman build --build-arg xcat_version="$XCAT_VERSION" --cap-add=ALL -t omnia_provision:${PROVISION_TAG} -f Dockerfile
    BUILD_RESULT=$?
    IMAGE_DESTINATION="Local (Podman): omnia_provision:${PROVISION_TAG}"
    if [ $BUILD_RESULT -eq 0 ]; then
        echo -e "${GREEN}omnia_provision image built successfully.${NC}"
        SUCCESSFUL_BUILDS+=("omnia_provision")
        LOADED_IMAGES+=("$IMAGE_DESTINATION")
    else
        echo -e "${RED}omnia_provision image build failed.${NC}"
        FAILED_BUILDS+=("omnia_provision")
    fi
    cd - || exit
}

# Function to build omnia_pcs image
build_omnia_pcs() {
    echo "Building omnia_pcs image..."
    echo -e "Using PCS Tag: ${YELLOW}${PCS_TAG}${NC}"
    cd "$PCS_CONTAINER_DIR" || exit
    podman build -t omnia_pcs:${PCS_TAG} -f Dockerfile
    BUILD_RESULT=$?
    IMAGE_DESTINATION="Local (Podman): omnia_pcs:${PCS_TAG}"
    if [ $BUILD_RESULT -eq 0 ]; then
        echo -e "${GREEN}omnia_pcs image built successfully.${NC}"
        SUCCESSFUL_BUILDS+=("omnia_pcs")
        LOADED_IMAGES+=("$IMAGE_DESTINATION")
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
    echo -e "Using Kubespray Tag: ${YELLOW}${KUBESPRAY_TAG}${NC}"
    echo -e "${RED}---------------------------------${NC}"
    cd "$KUBESPRAY_DIR" || exit
    # Use KUBESPRAY_TAG-KUBESPRAY_VERSION format for kubespray to maintain version tracking
    FINAL_KUBESPRAY_TAG="${KUBESPRAY_TAG}-${KUBESPRAY_VERSION}"
    echo -e "Final Kubespray Tag: ${YELLOW}${FINAL_KUBESPRAY_TAG}${NC}"
    podman build --build-arg KUBESPRAY_VERSION="$KUBESPRAY_VERSION" --build-arg SSH_PORT="$SSH_PORT" -t "omnia_kubespray:$FINAL_KUBESPRAY_TAG" -f Dockerfile
    BUILD_RESULT=$?
    IMAGE_DESTINATION="Local (Podman): omnia_kubespray:$FINAL_KUBESPRAY_TAG"

    if [ $BUILD_RESULT -eq 0 ]; then
        echo -e "${GREEN}omnia_kubespray image built successfully.${NC}"
        SUCCESSFUL_BUILDS+=("omnia_kubespray")
        LOADED_IMAGES+=("$IMAGE_DESTINATION")
    else
        echo -e "${RED}omnia_kubespray image build failed.${NC}"
        FAILED_BUILDS+=("omnia_kubespray")
    fi
    cd - || exit
}

# Function to build ubuntu_ldms image
build_ubuntu_ldms() {
    echo "Building ubuntu_ldms image..."
    echo -e "Using Build Tool: ${YELLOW}${BUILD_TOOL}${NC}"
    echo -e "Using Build Action: ${YELLOW}${BUILD_ACTION}${NC}"
    echo -e "Using Ubuntu LDMS Tag: ${YELLOW}${UBUNTU_LDMS_TAG}${NC}"
    
    if [ "$BUILD_TOOL" = "docker" ] && [ "$BUILD_ACTION" = "push" ]; then
        echo ""
        echo -e "Registry: ${CYAN}$OMNIA_DOCKER_REGISTERY${NC}"
        echo -e "Full Image Name: ${CYAN}$OMNIA_DOCKER_REGISTERY/ubuntu-ldms:${UBUNTU_LDMS_TAG}${NC}"
        echo ""
    fi
    
    cd "$UBUNTU_LDMS_DIR" || exit
    if [ "$BUILD_TOOL" = "podman" ]; then
        podman build -t ubuntu-ldms:${UBUNTU_LDMS_TAG} -f Dockerfile.bld_n_run.ubuntu24.04 .
        BUILD_RESULT=$?
        IMAGE_DESTINATION="Local (Podman): ubuntu-ldms:${UBUNTU_LDMS_TAG}"
    elif [ "$BUILD_TOOL" = "docker" ]; then
        if [ "$BUILD_ACTION" = "load" ]; then
            docker buildx build --no-cache -t ubuntu-ldms:${UBUNTU_LDMS_TAG} --file Dockerfile.bld_n_run.ubuntu24.04 --platform linux/amd64 --load .
            BUILD_RESULT=$?
            IMAGE_DESTINATION="Local (Docker): ubuntu-ldms:${UBUNTU_LDMS_TAG}"
        elif [ "$BUILD_ACTION" = "push" ]; then
            docker buildx build --no-cache -t "$OMNIA_DOCKER_REGISTERY/ubuntu-ldms:${UBUNTU_LDMS_TAG}" --file Dockerfile.bld_n_run.ubuntu24.04 --platform linux/amd64 --provenance=true --sbom=true --push .
            BUILD_RESULT=$?
            IMAGE_DESTINATION="Registry: $OMNIA_DOCKER_REGISTERY/ubuntu-ldms:${UBUNTU_LDMS_TAG}"
        else
            echo -e "${RED}Invalid BUILD_ACTION. Please enter 'load' or 'push'.${NC}"
            exit 1
        fi
    else
        echo -e "${RED}Invalid BUILD_TOOL. Please enter 'podman' or 'docker'.${NC}"
        exit 1
    fi

    if [ $BUILD_RESULT -eq 0 ]; then
        echo -e "${GREEN}ubuntu_ldms image built successfully.${NC}"
        SUCCESSFUL_BUILDS+=("ubuntu_ldms")
        if [ "$BUILD_TOOL" = "docker" ] && [ "$BUILD_ACTION" = "push" ]; then
            PUSHED_IMAGES+=("$IMAGE_DESTINATION")
        else
            LOADED_IMAGES+=("$IMAGE_DESTINATION")
        fi
    else
        echo -e "${RED}ubuntu_ldms image build failed.${NC}"
        FAILED_BUILDS+=("ubuntu_ldms")
    fi
    cd - || exit
}

build_omnia_auth() {
    echo "Building omnia_auth image..."
    echo -e "Using Build Tool: ${YELLOW}${BUILD_TOOL}${NC}"
    echo -e "Using Build Action: ${YELLOW}${BUILD_ACTION}${NC}"
    echo -e "Using Auth Tag: ${YELLOW}${AUTH_TAG}${NC}"
    if [ "$BUILD_TOOL" = "docker" ] && [ "$BUILD_ACTION" = "push" ]; then
        echo -e "Registry: ${YELLOW}${OMNIA_DOCKER_REGISTERY}${NC}"
        echo -e "Full Image Name: ${YELLOW}${OMNIA_DOCKER_REGISTERY}/omnia_auth:${AUTH_TAG}${NC}"
    fi
    echo -e "${RED}---------------------------------${NC}"
    cd "$AUTH_DIR" || exit
    if [ "$BUILD_TOOL" = "podman" ]; then
        podman build -t omnia_auth:${AUTH_TAG} -f Dockerfile
        BUILD_RESULT=$?
        IMAGE_DESTINATION="Local (Podman): omnia_auth:${AUTH_TAG}"
    elif [ "$BUILD_TOOL" = "docker" ]; then
        if [ "$BUILD_ACTION" = "load" ]; then
            docker buildx build --no-cache -t omnia_auth:${AUTH_TAG} --file Dockerfile --platform linux/amd64 --load .
            BUILD_RESULT=$?
            IMAGE_DESTINATION="Local (Docker): omnia_auth:${AUTH_TAG}"
        elif [ "$BUILD_ACTION" = "push" ]; then
            docker buildx build --no-cache -t "$OMNIA_DOCKER_REGISTERY/omnia_auth:${AUTH_TAG}" --file Dockerfile --platform linux/amd64 --provenance=true --sbom=true  --push .
            BUILD_RESULT=$?
            IMAGE_DESTINATION="Registry: $OMNIA_DOCKER_REGISTERY/omnia_auth:${AUTH_TAG}"
        else
            echo -e "${RED}Invalid BUILD_ACTION. Please enter 'load' or 'push'.${NC}"
            exit 1
        fi
    else
        echo -e "${RED}Invalid BUILD_TOOL. Please enter 'podman' or 'docker'.${NC}"
        exit 1
    fi

    if [ $BUILD_RESULT -eq 0 ]; then
        echo -e "${GREEN}omnia_auth image built successfully.${NC}"
        SUCCESSFUL_BUILDS+=("omnia_auth")
        if [ "$BUILD_TOOL" = "docker" ] && [ "$BUILD_ACTION" = "push" ]; then
            PUSHED_IMAGES+=("$IMAGE_DESTINATION")
        else
            LOADED_IMAGES+=("$IMAGE_DESTINATION")
        fi
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
OMNIA_DOCKER_REGISTERY="docker.io/dellhpcomniaaisolution"

# Default image tags for each container (can be overridden individually)
CORE_TAG="latest"
AUTH_TAG="latest"
PROVISION_TAG="latest"
PCS_TAG="latest"
KUBESPRAY_TAG="latest"
UBUNTU_LDMS_TAG="latest"
# Global fallback tag (used when image_tag= is specified)
IMAGE_TAG="latest"

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
    elif [[ "$arg" =~ ^image_tag=.*$ ]]; then
        IMAGE_TAG="${arg#image_tag=}"
        # Set all container tags to the same value when image_tag is used
        CORE_TAG="$IMAGE_TAG"
        AUTH_TAG="$IMAGE_TAG"
        PROVISION_TAG="$IMAGE_TAG"
        PCS_TAG="$IMAGE_TAG"
        KUBESPRAY_TAG="$IMAGE_TAG"
        UBUNTU_LDMS_TAG="$IMAGE_TAG"
    elif [[ "$arg" =~ ^core_tag=.*$ ]]; then
        CORE_TAG="${arg#core_tag=}"
    elif [[ "$arg" =~ ^auth_tag=.*$ ]]; then
        AUTH_TAG="${arg#auth_tag=}"
    elif [[ "$arg" =~ ^provision_tag=.*$ ]]; then
        PROVISION_TAG="${arg#provision_tag=}"
    elif [[ "$arg" =~ ^pcs_tag=.*$ ]]; then
        PCS_TAG="${arg#pcs_tag=}"
    elif [[ "$arg" =~ ^kubespray_tag=.*$ ]]; then
        KUBESPRAY_TAG="${arg#kubespray_tag=}"
    elif [[ "$arg" =~ ^ubuntu_ldms_tag=.*$ ]]; then
        UBUNTU_LDMS_TAG="${arg#ubuntu_ldms_tag=}"
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

# Ubuntu LDMS container variables
UBUNTU_LDMS_DIR="ContainerFile/ubuntu-ldms"

# Parse command line arguments
if [[ $# -eq 0 || "$1" == "all" ]]; then
    # Build all containers
    build_omnia_core
    build_omnia_auth
    build_ubuntu_ldms
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
            ubuntu-ldms)
                build_ubuntu_ldms
                ;;
            pipeline)
                build_omnia_core
                build_omnia_auth
                ;;
            *)
                echo -e "${RED}Invalid container: $container. Available options: provision, core, pcs, kubespray, auth, ubuntu-ldms.${NC}"
                exit 1
                ;;
        esac
    done
fi

# Summary of builds
echo -e "\n${BLUE}=== BUILD SUMMARY ===${NC}"
if [ ${#SUCCESSFUL_BUILDS[@]} -ne 0 ]; then
    echo -e "${GREEN}Successfully built containers:${YELLOW} ${SUCCESSFUL_BUILDS[*]} ${NC}"
    
    # Show loaded images (local)
    if [ ${#LOADED_IMAGES[@]} -ne 0 ]; then
        echo -e "\n${BLUE}📦 Images loaded locally:${NC}"
        for image in "${LOADED_IMAGES[@]}"; do
            echo -e "  ${GREEN}✓${NC} ${image}"
        done
    fi
    
    # Show pushed images (registry)
    if [ ${#PUSHED_IMAGES[@]} -ne 0 ]; then
        echo -e "\n${BLUE}🚀 Images pushed to registry:${NC}"
        for image in "${PUSHED_IMAGES[@]}"; do
            echo -e "  ${GREEN}✓${NC} ${image}"
        done
        echo -e "\n${YELLOW}Registry Images Available:${NC}"
        echo -e "You can now pull these images from the registry using:"
        for image in "${PUSHED_IMAGES[@]}"; do
            registry_image=$(echo "$image" | sed 's/Registry: //')
            echo -e "  ${BLUE}docker pull ${registry_image}${NC}"
        done
    fi

    # Check if omnia_core is successfully built and show the next steps for the user
    if [[ " ${SUCCESSFUL_BUILDS[*]} " =~ " omnia_core " ]]; then
        echo -e "\n${GREEN}🎉 omnia_core image built successfully!${NC}"
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
    echo -e "\n${RED}❌ Failed builds:${MAGENTA} ${FAILED_BUILDS[*]} ${NC}"
    exit 1
else
    if [ ${#SUCCESSFUL_BUILDS[@]} -ne 0 ]; then
        echo -e "\n${GREEN}🎉 All requested images built successfully!${NC}"
        
        # Summary statistics
        total_local=${#LOADED_IMAGES[@]}
        total_pushed=${#PUSHED_IMAGES[@]}
        echo -e "\n${BLUE}📊 Build Statistics:${NC}"
        echo -e "  • Total containers built: ${YELLOW}${#SUCCESSFUL_BUILDS[@]}${NC}"
        echo -e "  • Images loaded locally: ${YELLOW}${total_local}${NC}"
        echo -e "  • Images pushed to registry: ${YELLOW}${total_pushed}${NC}"
    fi
fi
