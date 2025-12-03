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

# Function to build ubuntu_ldms image
build_ubuntu_ldms() {
    echo "Building ubuntu_ldms image..."
    echo -e "Using Build Tool: ${YELLOW}${BUILD_TOOL}${NC}"
    echo -e "Using Build Action: ${YELLOW}${BUILD_ACTION}${NC}"
    echo -e "Using Ubuntu LDMS Tag: ${YELLOW}${UBUNTU_LDMS_TAG}${NC}"
    if [ "$BUILD_TOOL" = "docker" ] && [ "$BUILD_ACTION" = "push" ]; then
        echo -e "Registry: ${YELLOW}$OMNIA_DOCKER_REGISTERY${NC}"
        echo -e "Full Image Name: ${YELLOW}$OMNIA_DOCKER_REGISTERY/ubuntu-ldms:${UBUNTU_LDMS_TAG}${NC}"
    fi
    echo -e "${RED}---------------------------------${NC}"
    
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
OMNIA_VERSION="staging"
BUILD_TOOL="podman"
BUILD_ACTION="load"
OMNIA_DOCKER_REGISTERY="docker.io/dellhpcomniaaisolution"

# Default image tags for each container (can be overridden individually)
CORE_TAG="latest"
AUTH_TAG="latest"
PCS_TAG="latest"
UBUNTU_LDMS_TAG="latest"
# Global fallback tag (used when image_tag= is specified)
IMAGE_TAG="latest"

# Valid parameter names
VALID_PARAMS=("omnia_branch" "build_tool" "build_action" "image_tag" "core_tag" "auth_tag" "pcs_tag" "ubuntu_ldms_tag")
VALID_CONTAINERS=("all" "core" "pcs" "auth" "ubuntu-ldms" "pipeline")

# Parse command line arguments
for arg in "$@"; do
    # Skip the first argument if it's a container name or list of containers
    if [[ "$arg" != *"="* ]]; then
        continue
    fi
    
    # Extract parameter name
    param_name="${arg%%=*}"
    
    # Validate parameter name
    if [[ ! " ${VALID_PARAMS[@]} " =~ " ${param_name} " ]]; then
        echo -e "${RED}Error: Invalid parameter '${param_name}'${NC}"
        echo -e "${YELLOW}Valid parameters are: ${VALID_PARAMS[*]}${NC}"
        exit 1
    fi
    
    if [[ "$arg" =~ ^omnia_branch=.*$ ]]; then
        OMNIA_VERSION="${arg#omnia_branch=}"
    elif [[ "$arg" =~ ^build_tool=.*$ ]]; then
        BUILD_TOOL="${arg#build_tool=}"
    elif [[ "$arg" =~ ^build_action=.*$ ]]; then
        BUILD_ACTION="${arg#build_action=}"
    elif [[ "$arg" =~ ^image_tag=.*$ ]]; then
        IMAGE_TAG="${arg#image_tag=}"
        # Set all container tags to the same value when image_tag is used
        CORE_TAG="$IMAGE_TAG"
        AUTH_TAG="$IMAGE_TAG"
        PCS_TAG="$IMAGE_TAG"
        UBUNTU_LDMS_TAG="$IMAGE_TAG"
    elif [[ "$arg" =~ ^core_tag=.*$ ]]; then
        CORE_TAG="${arg#core_tag=}"
    elif [[ "$arg" =~ ^auth_tag=.*$ ]]; then
        AUTH_TAG="${arg#auth_tag=}"
    elif [[ "$arg" =~ ^pcs_tag=.*$ ]]; then
        PCS_TAG="${arg#pcs_tag=}"
    elif [[ "$arg" =~ ^ubuntu_ldms_tag=.*$ ]]; then
        UBUNTU_LDMS_TAG="${arg#ubuntu_ldms_tag=}"
    fi
done

# Validate build_tool value
if [[ "$BUILD_TOOL" != "podman" && "$BUILD_TOOL" != "docker" ]]; then
    echo -e "${RED}Error: Invalid build_tool value '${BUILD_TOOL}'${NC}"
    echo -e "${YELLOW}Valid values are: podman, docker${NC}"
    exit 1
fi

# Validate build_action value
if [[ "$BUILD_ACTION" != "load" && "$BUILD_ACTION" != "push" ]]; then
    echo -e "${RED}Error: Invalid build_action value '${BUILD_ACTION}'${NC}"
    echo -e "${YELLOW}Valid values are: load, push${NC}"
    exit 1
fi

# Validate that push requires docker
if [[ "$BUILD_ACTION" == "push" && "$BUILD_TOOL" != "docker" ]]; then
    echo -e "${RED}Error: build_action=push requires build_tool=docker${NC}"
    echo -e "${YELLOW}Please set build_tool=docker when using build_action=push${NC}"
    exit 1
fi

# Omnia core container variables
OMNIA_CORE_DIR="ContainerFile/omnia_core"

# PCS container variables
PCS_CONTAINER_DIR="ContainerFile/pcs_container"

# Auth container variables
AUTH_DIR="ContainerFile/auth"

# Ubuntu LDMS container variables
UBUNTU_LDMS_DIR="ContainerFile/ubuntu-ldms"

# Parse command line arguments
if [[ $# -eq 0 || "$1" == "all" ]]; then
    # Build all containers (core and auth)
    build_omnia_core
    build_omnia_auth
else
    # Loop through each container specified in the arguments and build
    IFS=',' read -r -a containers <<< "$1"
    for container in "${containers[@]}"; do
        case "$container" in
            all)
                build_omnia_core
                build_omnia_auth
                ;;
            core)
                build_omnia_core
                ;;
            pcs)
                build_omnia_pcs
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
                build_ubuntu_ldms
                ;;
            *)
                echo -e "${RED}Invalid container: $container. Available options: all, core, pcs, auth, ubuntu-ldms, pipeline.${NC}"
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
