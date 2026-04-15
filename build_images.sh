#!/bin/bash

# Define color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[34m'
YELLOW='\033[1;33m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Install git if not present
echo -e "${BLUE}Installing git...${NC}"
dnf install -y git
echo -e "${GREEN}Git installation complete.${NC}\n"

# Arrays to store build status
SUCCESSFUL_BUILDS=()
FAILED_BUILDS=()
LOADED_IMAGES=()
PUSHED_IMAGES=()

# Function to build omnia_core image
build_omnia_core() {
    echo "Building omnia_core image..."
    
    # Check if omnia_branch was explicitly set
    if [[ ! " ${CONTAINER_PARAMS[@]} " =~ " omnia_branch " ]]; then
        echo -e "${YELLOW}⚠️  Warning: omnia_branch not specified, using default branch: ${OMNIA_VERSION}${NC}"
    fi
    
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

# Function to build omnia_build_stream image
build_omnia_build_stream() {
    echo "Building omnia_build_stream image..."
    echo -e "Using Build Tool: ${YELLOW}${BUILD_TOOL}${NC}"
    echo -e "Using Build Action: ${YELLOW}${BUILD_ACTION}${NC}"
    echo -e "Using Build Stream Tag: ${YELLOW}${BUILD_STREAM_TAG}${NC}"
    if [ "$BUILD_TOOL" = "docker" ] && [ "$BUILD_ACTION" = "push" ]; then
        echo -e "Registry: ${YELLOW}${OMNIA_DOCKER_REGISTERY}${NC}"
        echo -e "Full Image Name: ${YELLOW}${OMNIA_DOCKER_REGISTERY}/omnia_build_stream:${BUILD_STREAM_TAG}${NC}"
    fi
    echo -e "${RED}---------------------------------${NC}"
    cd "$BUILD_STREAM_DIR" || exit
    if [ "$BUILD_TOOL" = "podman" ]; then
        podman build -t omnia_build_stream:${BUILD_STREAM_TAG} -f Dockerfile
        BUILD_RESULT=$?
        IMAGE_DESTINATION="Local (Podman): omnia_build_stream:${BUILD_STREAM_TAG}"
    elif [ "$BUILD_TOOL" = "docker" ]; then
        if [ "$BUILD_ACTION" = "load" ]; then
            docker buildx build --network=host --no-cache -t omnia_build_stream:${BUILD_STREAM_TAG} --file Dockerfile --platform linux/amd64 --load .
            BUILD_RESULT=$?
            IMAGE_DESTINATION="Local (Docker): omnia_build_stream:${BUILD_STREAM_TAG}"
        elif [ "$BUILD_ACTION" = "push" ]; then
            docker buildx build --network=host --no-cache -t "$OMNIA_DOCKER_REGISTERY/omnia_build_stream:${BUILD_STREAM_TAG}" --file Dockerfile --platform linux/amd64 --provenance=true --sbom=true --push .
            BUILD_RESULT=$?
            IMAGE_DESTINATION="Registry: $OMNIA_DOCKER_REGISTERY/omnia_build_stream:${BUILD_STREAM_TAG}"
        else
            echo -e "${RED}Invalid BUILD_ACTION. Please enter 'load' or 'push'.${NC}"
            exit 1
        fi
    else
        echo -e "${RED}Invalid BUILD_TOOL. Please enter 'podman' or 'docker'.${NC}"
        exit 1
    fi

    if [ $BUILD_RESULT -eq 0 ]; then
        echo -e "${GREEN}omnia_build_stream image built successfully.${NC}"
        SUCCESSFUL_BUILDS+=("omnia_build_stream")
        if [ "$BUILD_TOOL" = "docker" ] && [ "$BUILD_ACTION" = "push" ]; then
            PUSHED_IMAGES+=("$IMAGE_DESTINATION")
        else
            LOADED_IMAGES+=("$IMAGE_DESTINATION")
        fi
    else
        echo -e "${RED}omnia_build_stream image build failed.${NC}"
        FAILED_BUILDS+=("omnia_build_stream")
    fi
    cd - || exit
}

# Function to clone iDRAC Telemetry Reference Tools repo
clone_idrac_telemetry_repo() {
    if [ ! -d "$IDRAC_TELEMETRY_CLONE_DIR" ]; then
        echo -e "${YELLOW}Cloning iDRAC-Telemetry-Reference-Tools at commit ${IDRAC_TELEMETRY_COMMIT}...${NC}"
        git clone https://github.com/dell/iDRAC-Telemetry-Reference-Tools.git "$IDRAC_TELEMETRY_CLONE_DIR"
        cd "$IDRAC_TELEMETRY_CLONE_DIR" || exit 1
        git fetch --all
        git checkout "$IDRAC_TELEMETRY_COMMIT"
        cd - > /dev/null || exit 1
        echo -e "${GREEN}Repository cloned and checked out to ${IDRAC_TELEMETRY_COMMIT}.${NC}"
    else
        echo -e "${YELLOW}iDRAC-Telemetry-Reference-Tools already cloned.${NC}"
    fi
}

# Function to clone OpenCHAMI Image Builder repo
clone_image_builder_repo() {
    if [ ! -d "$IMAGE_BUILDER_CLONE_DIR" ]; then
        echo -e "${YELLOW}Cloning OpenCHAMI/image-builder at commit ${IMAGE_BUILDER_COMMIT}...${NC}"
        git clone https://github.com/OpenCHAMI/image-builder.git "$IMAGE_BUILDER_CLONE_DIR"
        cd "$IMAGE_BUILDER_CLONE_DIR" || exit 1
        git fetch --all
        git checkout "$IMAGE_BUILDER_COMMIT"
        
        # Copy Dockerfile.el10 from ContainerFile/image-build/
        echo -e "${YELLOW}Copying Dockerfile.el10 to dockerfiles/dnf/...${NC}"
        cp "../${IMAGE_BUILDER_DIR}/Dockerfile.el10" "dockerfiles/dnf/Dockerfile.el10"
        
        # Copy requirements.txt from ContainerFile/image-build/
        echo -e "${YELLOW}Copying requirements.txt from ContainerFile/image-build/...${NC}"
        cp "../${IMAGE_BUILDER_DIR}/requirements.txt" "requirements.txt"
        
        # Modify utils.py to remove Setting from import
        echo -e "${YELLOW}Modifying src/utils.py import statement...${NC}"
        sed -i 's/from ansible.config.manager import ConfigManager, Setting/from ansible.config.manager import ConfigManager/' src/utils.py
        
        cd - > /dev/null || exit 1
        echo -e "${GREEN}Repository cloned and configured at ${IMAGE_BUILDER_COMMIT}.${NC}"
    else
        echo -e "${YELLOW}OpenCHAMI/image-builder already cloned.${NC}"
    fi
}

# Function to build kafkapump image (iDRAC Telemetry)
build_kafkapump() {
    echo "Building kafkapump image..."
    echo -e "Using Build Tool: ${YELLOW}${BUILD_TOOL}${NC}"
    echo -e "Using Build Action: ${YELLOW}${BUILD_ACTION}${NC}"
    echo -e "Using iDRAC Commit: ${YELLOW}${IDRAC_TELEMETRY_COMMIT}${NC}"
    echo -e "Using KafkaPump Tag: ${YELLOW}${KAFKAPUMP_TAG}${NC}"
    if [ "$BUILD_TOOL" = "docker" ] && [ "$BUILD_ACTION" = "push" ]; then
        echo -e "Registry: ${YELLOW}$OMNIA_DOCKER_REGISTERY${NC}"
        echo -e "Full Image Name: ${YELLOW}$OMNIA_DOCKER_REGISTERY/kafkapump:${KAFKAPUMP_TAG}${NC}"
    fi
    echo -e "${RED}---------------------------------${NC}"
    
    # Clone repo if needed
    clone_idrac_telemetry_repo
    
    cd "${IDRAC_TELEMETRY_CLONE_DIR}" || exit 1
    if [ "$BUILD_TOOL" = "podman" ]; then
        podman build --build-arg CMD=kafkapump -t kafkapump:${KAFKAPUMP_TAG} -f docker-compose-files/Dockerfile .
        BUILD_RESULT=$?
        IMAGE_DESTINATION="Local (Podman): kafkapump:${KAFKAPUMP_TAG}"
    elif [ "$BUILD_TOOL" = "docker" ]; then
        if [ "$BUILD_ACTION" = "load" ]; then
            docker buildx build --no-cache --build-arg CMD=kafkapump -t kafkapump:${KAFKAPUMP_TAG} \
                --file docker-compose-files/Dockerfile --platform linux/amd64 --load .
            BUILD_RESULT=$?
            IMAGE_DESTINATION="Local (Docker): kafkapump:${KAFKAPUMP_TAG}"
        elif [ "$BUILD_ACTION" = "push" ]; then
            docker buildx build --no-cache --build-arg CMD=kafkapump \
                -t "$OMNIA_DOCKER_REGISTERY/kafkapump:${KAFKAPUMP_TAG}" --file docker-compose-files/Dockerfile \
                --platform linux/amd64 --provenance=true --sbom=true --push .
            BUILD_RESULT=$?
            IMAGE_DESTINATION="Registry: $OMNIA_DOCKER_REGISTERY/kafkapump:${KAFKAPUMP_TAG}"
        else
            echo -e "${RED}Invalid BUILD_ACTION. Please enter 'load' or 'push'.${NC}"
            exit 1
        fi
    else
        echo -e "${RED}Invalid BUILD_TOOL. Please enter 'podman' or 'docker'.${NC}"
        exit 1
    fi

    if [ $BUILD_RESULT -eq 0 ]; then
        echo -e "${GREEN}kafkapump image built successfully.${NC}"
        SUCCESSFUL_BUILDS+=("kafkapump")
        if [ "$BUILD_TOOL" = "docker" ] && [ "$BUILD_ACTION" = "push" ]; then
            PUSHED_IMAGES+=("$IMAGE_DESTINATION")
        else
            LOADED_IMAGES+=("$IMAGE_DESTINATION")
        fi
    else
        echo -e "${RED}kafkapump image build failed.${NC}"
        FAILED_BUILDS+=("kafkapump")
    fi
    cd - > /dev/null || exit 1
}

# Function to build victoriapump image (iDRAC Telemetry)
build_victoriapump() {
    echo "Building victoriapump image..."
    echo -e "Using Build Tool: ${YELLOW}${BUILD_TOOL}${NC}"
    echo -e "Using Build Action: ${YELLOW}${BUILD_ACTION}${NC}"
    echo -e "Using iDRAC Commit: ${YELLOW}${IDRAC_TELEMETRY_COMMIT}${NC}"
    echo -e "Using VictoriaPump Tag: ${YELLOW}${VICTORIAPUMP_TAG}${NC}"
    if [ "$BUILD_TOOL" = "docker" ] && [ "$BUILD_ACTION" = "push" ]; then
        echo -e "Registry: ${YELLOW}$OMNIA_DOCKER_REGISTERY${NC}"
        echo -e "Full Image Name: ${YELLOW}$OMNIA_DOCKER_REGISTERY/victoriapump:${VICTORIAPUMP_TAG}${NC}"
    fi
    echo -e "${RED}---------------------------------${NC}"
    
    # Clone repo if needed
    clone_idrac_telemetry_repo
    
    cd "${IDRAC_TELEMETRY_CLONE_DIR}" || exit 1
    if [ "$BUILD_TOOL" = "podman" ]; then
        podman build --build-arg CMD=victoriapump -t victoriapump:${VICTORIAPUMP_TAG} -f docker-compose-files/Dockerfile .
        BUILD_RESULT=$?
        IMAGE_DESTINATION="Local (Podman): victoriapump:${VICTORIAPUMP_TAG}"
    elif [ "$BUILD_TOOL" = "docker" ]; then
        if [ "$BUILD_ACTION" = "load" ]; then
            docker buildx build --no-cache --build-arg CMD=victoriapump -t victoriapump:${VICTORIAPUMP_TAG} \
                --file docker-compose-files/Dockerfile --platform linux/amd64 --load .
            BUILD_RESULT=$?
            IMAGE_DESTINATION="Local (Docker): victoriapump:${VICTORIAPUMP_TAG}"
        elif [ "$BUILD_ACTION" = "push" ]; then
            docker buildx build --no-cache --build-arg CMD=victoriapump \
                -t "$OMNIA_DOCKER_REGISTERY/victoriapump:${VICTORIAPUMP_TAG}" --file docker-compose-files/Dockerfile \
                --platform linux/amd64 --provenance=true --sbom=true --push .
            BUILD_RESULT=$?
            IMAGE_DESTINATION="Registry: $OMNIA_DOCKER_REGISTERY/victoriapump:${VICTORIAPUMP_TAG}"
        else
            echo -e "${RED}Invalid BUILD_ACTION. Please enter 'load' or 'push'.${NC}"
            exit 1
        fi
    else
        echo -e "${RED}Invalid BUILD_TOOL. Please enter 'podman' or 'docker'.${NC}"
        exit 1
    fi

    if [ $BUILD_RESULT -eq 0 ]; then
        echo -e "${GREEN}victoriapump image built successfully.${NC}"
        SUCCESSFUL_BUILDS+=("victoriapump")
        if [ "$BUILD_TOOL" = "docker" ] && [ "$BUILD_ACTION" = "push" ]; then
            PUSHED_IMAGES+=("$IMAGE_DESTINATION")
        else
            LOADED_IMAGES+=("$IMAGE_DESTINATION")
        fi
    else
        echo -e "${RED}victoriapump image build failed.${NC}"
        FAILED_BUILDS+=("victoriapump")
    fi
    cd - > /dev/null || exit 1
}

# Function to build telemetry_receiver image (iDRAC Telemetry)
build_telemetry_receiver() {
    echo "Building telemetry_receiver image..."
    echo -e "Using Build Tool: ${YELLOW}${BUILD_TOOL}${NC}"
    echo -e "Using Build Action: ${YELLOW}${BUILD_ACTION}${NC}"
    echo -e "Using iDRAC Commit: ${YELLOW}${IDRAC_TELEMETRY_COMMIT}${NC}"
    echo -e "Using Telemetry Receiver Tag: ${YELLOW}${TELEMETRY_RECEIVER_TAG}${NC}"
    if [ "$BUILD_TOOL" = "docker" ] && [ "$BUILD_ACTION" = "push" ]; then
        echo -e "Registry: ${YELLOW}$OMNIA_DOCKER_REGISTERY${NC}"
        echo -e "Full Image Name: ${YELLOW}$OMNIA_DOCKER_REGISTERY/idrac_telemetry_receiver:${TELEMETRY_RECEIVER_TAG}${NC}"
    fi
    echo -e "${RED}---------------------------------${NC}"
    
    # Clone repo if needed
    clone_idrac_telemetry_repo
    
    cd "${IDRAC_TELEMETRY_CLONE_DIR}" || exit 1
    if [ "$BUILD_TOOL" = "podman" ]; then
        podman build -t idrac_telemetry_receiver:${TELEMETRY_RECEIVER_TAG} -f docker-compose-files/Dockerfile.telemetry_receiver .
        BUILD_RESULT=$?
        IMAGE_DESTINATION="Local (Podman): idrac_telemetry_receiver:${TELEMETRY_RECEIVER_TAG}"
    elif [ "$BUILD_TOOL" = "docker" ]; then
        if [ "$BUILD_ACTION" = "load" ]; then
            docker buildx build --no-cache -t idrac_telemetry_receiver:${TELEMETRY_RECEIVER_TAG} \
                --file docker-compose-files/Dockerfile.telemetry_receiver --platform linux/amd64 --load .
            BUILD_RESULT=$?
            IMAGE_DESTINATION="Local (Docker): idrac_telemetry_receiver:${TELEMETRY_RECEIVER_TAG}"
        elif [ "$BUILD_ACTION" = "push" ]; then
            docker buildx build --no-cache -t "$OMNIA_DOCKER_REGISTERY/idrac_telemetry_receiver:${TELEMETRY_RECEIVER_TAG}" \
                --file docker-compose-files/Dockerfile.telemetry_receiver --platform linux/amd64 --provenance=true --sbom=true --push .
            BUILD_RESULT=$?
            IMAGE_DESTINATION="Registry: $OMNIA_DOCKER_REGISTERY/idrac_telemetry_receiver:${TELEMETRY_RECEIVER_TAG}"
        else
            echo -e "${RED}Invalid BUILD_ACTION. Please enter 'load' or 'push'.${NC}"
            exit 1
        fi
    else
        echo -e "${RED}Invalid BUILD_TOOL. Please enter 'podman' or 'docker'.${NC}"
        exit 1
    fi

    if [ $BUILD_RESULT -eq 0 ]; then
        echo -e "${GREEN}telemetry_receiver image built successfully.${NC}"
        SUCCESSFUL_BUILDS+=("telemetry_receiver")
        if [ "$BUILD_TOOL" = "docker" ] && [ "$BUILD_ACTION" = "push" ]; then
            PUSHED_IMAGES+=("$IMAGE_DESTINATION")
        else
            LOADED_IMAGES+=("$IMAGE_DESTINATION")
        fi
    else
        echo -e "${RED}telemetry_receiver image build failed.${NC}"
        FAILED_BUILDS+=("telemetry_receiver")
    fi
    cd - > /dev/null || exit 1
}

# Function to build image-builder image
build_image_builder() {
    echo "Building image-builder image..."
    echo -e "Using Build Tool: ${YELLOW}${BUILD_TOOL}${NC}"
    echo -e "Using Build Action: ${YELLOW}${BUILD_ACTION}${NC}"
    echo -e "Using Image Builder Commit: ${YELLOW}${IMAGE_BUILDER_COMMIT}${NC}"
    echo -e "Using Image Builder Tag: ${YELLOW}${IMAGE_BUILDER_TAG}${NC}"
    if [ "$BUILD_TOOL" = "docker" ]; then
        # Dynamic platform detection for image-builder (only when using docker)
        DETECTED_PLATFORM="$(docker info --format '{{.OSType}}/{{.Architecture}}')" || {
            echo -e "${RED}Error: Failed to detect platform. Docker info command failed.${NC}"
            echo -e "${YELLOW}Please ensure Docker is installed and running.${NC}"
            exit 1
        }
        echo -e "Using Detected Platform: ${YELLOW}${DETECTED_PLATFORM}${NC}"
    fi
    if [ "$BUILD_TOOL" = "docker" ] && [ "$BUILD_ACTION" = "push" ]; then
        echo -e "Registry: ${YELLOW}$OMNIA_DOCKER_REGISTERY${NC}"
        echo -e "Full Image Name: ${YELLOW}$OMNIA_DOCKER_REGISTERY/image-build-el10:${IMAGE_BUILDER_TAG}${NC}"
    fi
    echo -e "${RED}---------------------------------${NC}"
    
    # Clone repo if needed
    clone_image_builder_repo
    
    cd "${IMAGE_BUILDER_CLONE_DIR}" || exit 1
    if [ "$BUILD_TOOL" = "podman" ]; then
        podman build -t image-build-el10:${IMAGE_BUILDER_TAG} -f dockerfiles/dnf/Dockerfile.el10 .
        BUILD_RESULT=$?
        IMAGE_DESTINATION="Local (Podman): image-build-el10:${IMAGE_BUILDER_TAG}"
    elif [ "$BUILD_TOOL" = "docker" ]; then
        if [ "$BUILD_ACTION" = "load" ]; then
            docker buildx build --no-cache -t image-build-el10:${IMAGE_BUILDER_TAG} \
                --file dockerfiles/dnf/Dockerfile.el10 --platform "$DETECTED_PLATFORM" --load .
            BUILD_RESULT=$?
            IMAGE_DESTINATION="Local (Docker): image-build-el10:${IMAGE_BUILDER_TAG}"
        elif [ "$BUILD_ACTION" = "push" ]; then
            docker buildx build --no-cache -t "$OMNIA_DOCKER_REGISTERY/image-build-el10:${IMAGE_BUILDER_TAG}" \
                --file dockerfiles/dnf/Dockerfile.el10 --platform "$DETECTED_PLATFORM" --provenance=true --sbom=true --push .
            BUILD_RESULT=$?
            IMAGE_DESTINATION="Registry: $OMNIA_DOCKER_REGISTERY/image-build-el10:${IMAGE_BUILDER_TAG}"
        else
            echo -e "${RED}Invalid BUILD_ACTION. Please enter 'load' or 'push'.${NC}"
            exit 1
        fi
    else
        echo -e "${RED}Invalid BUILD_TOOL. Please enter 'podman' or 'docker'.${NC}"
        exit 1
    fi

    if [ $BUILD_RESULT -eq 0 ]; then
        echo -e "${GREEN}image-builder image built successfully.${NC}"
        SUCCESSFUL_BUILDS+=("image_builder")
        if [ "$BUILD_TOOL" = "docker" ] && [ "$BUILD_ACTION" = "push" ]; then
            PUSHED_IMAGES+=("$IMAGE_DESTINATION")
        else
            LOADED_IMAGES+=("$IMAGE_DESTINATION")
        fi
    else
        echo -e "${RED}image-builder image build failed.${NC}"
        FAILED_BUILDS+=("image_builder")
    fi
    cd - > /dev/null || exit 1
}

# Default parameterized values
OMNIA_VERSION="main"
BUILD_TOOL="podman"
BUILD_ACTION="load"
OMNIA_DOCKER_REGISTERY="docker.io/dellhpcomniaaisolution"

# Default image tags for each container (can be overridden individually)
CORE_TAG="2.1"
AUTH_TAG="1.0"
PCS_TAG="1.0"
UBUNTU_LDMS_TAG="1.0"
KAFKAPUMP_TAG="1.2"
VICTORIAPUMP_TAG="1.2"
TELEMETRY_RECEIVER_TAG="1.2"
IMAGE_BUILDER_TAG="1.1"
BUILD_STREAM_TAG="1.1"

# Valid parameter names

VALID_PARAMS=("omnia_branch" "build_tool" "build_action" "core_tag" "auth_tag" "pcs_tag" "ubuntu_ldms_tag" "kafkapump_tag" "victoriapump_tag" "telemetry_receiver_tag" "image_builder_tag" "build_stream_tag")

VALID_CONTAINERS=("all" "core" "pcs" "auth" "ubuntu-ldms" "pipeline" "telemetry" "kafkapump" "victoriapump" "telemetry-receiver" "image-builder" "build-stream")

# Common parameters valid for all container types
COMMON_PARAMS=("build_tool" "build_action")

# Store container-specific parameters for later validation
CONTAINER_PARAMS=()
INVALID_PARAMS=()

# Parse command line arguments - first pass to collect parameters
for arg in "$@"; do
    # Skip the first argument if it's a container name or list of containers
    if [[ "$arg" != *"="* ]]; then
        continue
    fi
    
    # Extract parameter name
    param_name="${arg%%=*}"
    
    # Check if parameter is valid (exists in VALID_PARAMS)
    if [[ ! " ${VALID_PARAMS[@]} " =~ " ${param_name} " ]]; then
        INVALID_PARAMS+=("$param_name")
    fi
    
    # Store for container-specific validation later
    CONTAINER_PARAMS+=("$param_name")
    
    if [[ "$arg" =~ ^omnia_branch=.*$ ]]; then
        OMNIA_VERSION="${arg#omnia_branch=}"
    elif [[ "$arg" =~ ^build_tool=.*$ ]]; then
        BUILD_TOOL="${arg#build_tool=}"
    elif [[ "$arg" =~ ^build_action=.*$ ]]; then
        BUILD_ACTION="${arg#build_action=}"
    elif [[ "$arg" =~ ^core_tag=.*$ ]]; then
        CORE_TAG="${arg#core_tag=}"
    elif [[ "$arg" =~ ^auth_tag=.*$ ]]; then
        AUTH_TAG="${arg#auth_tag=}"
    elif [[ "$arg" =~ ^pcs_tag=.*$ ]]; then
        PCS_TAG="${arg#pcs_tag=}"
    elif [[ "$arg" =~ ^ubuntu_ldms_tag=.*$ ]]; then
        UBUNTU_LDMS_TAG="${arg#ubuntu_ldms_tag=}"
    elif [[ "$arg" =~ ^kafkapump_tag=.*$ ]]; then
        KAFKAPUMP_TAG="${arg#kafkapump_tag=}"
    elif [[ "$arg" =~ ^victoriapump_tag=.*$ ]]; then
        VICTORIAPUMP_TAG="${arg#victoriapump_tag=}"
    elif [[ "$arg" =~ ^telemetry_receiver_tag=.*$ ]]; then
        TELEMETRY_RECEIVER_TAG="${arg#telemetry_receiver_tag=}"
    elif [[ "$arg" =~ ^image_builder_tag=.*$ ]]; then
        IMAGE_BUILDER_TAG="${arg#image_builder_tag=}"
    elif [[ "$arg" =~ ^build_stream_tag=.*$ ]]; then
        BUILD_STREAM_TAG="${arg#build_stream_tag=}"
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

# Build Stream container variables
BUILD_STREAM_DIR="ContainerFile/omnia_build_stream"

# Ubuntu LDMS container variables
UBUNTU_LDMS_DIR="ContainerFile/ubuntu-ldms"

# iDRAC Telemetry container variables
IDRAC_TELEMETRY_COMMIT="b9cd6e08ecb58a01f26c12041d428d6d21b438f0"
IDRAC_TELEMETRY_CLONE_DIR=".idrac-telemetry-tools"

# Image Builder container variables
IMAGE_BUILDER_COMMIT="70702bd3d76d066d18441bc0b2fbb89020544d8f"
IMAGE_BUILDER_CLONE_DIR=".image-builder-tools"
IMAGE_BUILDER_DIR="ContainerFile/image-build"

# Function to validate container-specific parameters
validate_container_params() {
    local container=$1
    local allowed_params=("${@:2}")
    
    for param in "${CONTAINER_PARAMS[@]}"; do
        # Skip common parameters (always valid)
        if [[ " ${COMMON_PARAMS[@]} " =~ " ${param} " ]]; then
            continue
        fi
        
        # Check if parameter is in allowed list for this container
        if [[ ! " ${allowed_params[@]} " =~ " ${param} " ]]; then
            echo -e "${RED}Error: Parameter '${param}' is not valid for container '${container}'${NC}"
            echo -e "${YELLOW}Valid parameters for '${container}': ${COMMON_PARAMS[*]} ${allowed_params[*]}${NC}"
            exit 1
        fi
    done
}

# Parse command line arguments
# Set default to 'oim' if no arguments provided
CONTAINER_ARG="${1:-oim}"

# Handle single container options with direct building
case "$CONTAINER_ARG" in
    oim)
        # Build OIM containers (core, auth, and image-builder) - required for Omnia deployment
        ALLOWED_TAG_PARAMS=("core_tag" "auth_tag" "image_builder_tag" "omnia_branch")
        
        if [ ${#INVALID_PARAMS[@]} -ne 0 ]; then
            echo -e "${RED}Error: Invalid parameter(s): ${INVALID_PARAMS[*]}${NC}"
            echo -e "${YELLOW}Valid parameters for 'oim': ${COMMON_PARAMS[*]} ${ALLOWED_TAG_PARAMS[*]}${NC}"
            exit 1
        fi
        
        validate_container_params "oim" "${ALLOWED_TAG_PARAMS[@]}"
        build_omnia_core
        build_omnia_auth
        build_image_builder
        ;;
    
    all)
        # Build all containers
        ALLOWED_TAG_PARAMS=("core_tag" "auth_tag" "ubuntu_ldms_tag" "kafkapump_tag" "victoriapump_tag" "telemetry_receiver_tag" "image_builder_tag" "omnia_branch")
        
        if [ ${#INVALID_PARAMS[@]} -ne 0 ]; then
            echo -e "${RED}Error: Invalid parameter(s): ${INVALID_PARAMS[*]}${NC}"
            echo -e "${YELLOW}Valid parameters for 'all': ${COMMON_PARAMS[*]} ${ALLOWED_TAG_PARAMS[*]}${NC}"
            exit 1
        fi
        
        validate_container_params "all" "${ALLOWED_TAG_PARAMS[@]}"
        build_omnia_core
        build_omnia_auth
        build_ubuntu_ldms
        build_kafkapump
        build_victoriapump
        build_telemetry_receiver
        build_image_builder
        ;;
    
    pipeline)
        # Build pipeline containers (internal use)
        ALLOWED_TAG_PARAMS=("core_tag" "auth_tag" "ubuntu_ldms_tag" "kafkapump_tag" "victoriapump_tag" "telemetry_receiver_tag" "image_builder_tag" "omnia_branch")
        
        if [ ${#INVALID_PARAMS[@]} -ne 0 ]; then
            echo -e "${RED}Error: Invalid parameter(s): ${INVALID_PARAMS[*]}${NC}"
            echo -e "${YELLOW}Valid parameters for 'pipeline': ${COMMON_PARAMS[*]} ${ALLOWED_TAG_PARAMS[*]}${NC}"
            exit 1
        fi
        
        validate_container_params "pipeline" "${ALLOWED_TAG_PARAMS[@]}"
        build_omnia_core
        build_omnia_auth
        build_ubuntu_ldms
        build_kafkapump
        build_victoriapump
        build_telemetry_receiver
        build_image_builder
        ;;
    
    telemetry)
        # Build telemetry containers
        ALLOWED_TAG_PARAMS=("kafkapump_tag" "victoriapump_tag" "telemetry_receiver_tag")
        
        if [ ${#INVALID_PARAMS[@]} -ne 0 ]; then
            echo -e "${RED}Error: Invalid parameter(s): ${INVALID_PARAMS[*]}${NC}"
            echo -e "${YELLOW}Valid parameters for 'telemetry': ${COMMON_PARAMS[*]} ${ALLOWED_TAG_PARAMS[*]}${NC}"
            exit 1
        fi
        
        validate_container_params "telemetry" "${ALLOWED_TAG_PARAMS[@]}"
        build_kafkapump
        build_victoriapump
        build_telemetry_receiver
        ;;
    
    image-builder)
        # Build image-builder container
        ALLOWED_TAG_PARAMS=("image_builder_tag")
        
        if [ ${#INVALID_PARAMS[@]} -ne 0 ]; then
            echo -e "${RED}Error: Invalid parameter(s): ${INVALID_PARAMS[*]}${NC}"
            echo -e "${YELLOW}Valid parameters for 'image-builder': ${COMMON_PARAMS[*]} ${ALLOWED_TAG_PARAMS[*]}${NC}"
            exit 1
        fi
        
        validate_container_params "image-builder" "${ALLOWED_TAG_PARAMS[@]}"
        build_image_builder
        ;;
    
    build-stream)
        # Build build-stream container
        ALLOWED_TAG_PARAMS=("build_stream_tag")
        
        if [ ${#INVALID_PARAMS[@]} -ne 0 ]; then
            echo -e "${RED}Error: Invalid parameter(s): ${INVALID_PARAMS[*]}${NC}"
            echo -e "${YELLOW}Valid parameters for 'build-stream': ${COMMON_PARAMS[*]} ${ALLOWED_TAG_PARAMS[*]}${NC}"
            exit 1
        fi
        
        validate_container_params "build-stream" "${ALLOWED_TAG_PARAMS[@]}"
        build_omnia_build_stream
        ;;
    
    *)
        # Handle individual containers or comma-separated lists
        IFS=',' read -r -a containers <<< "$CONTAINER_ARG"
        
        # Collect allowed parameters for the combination of containers
        ALLOWED_TAG_PARAMS=()
        BUILDING_CORE=false
    
    for container in "${containers[@]}"; do
        case "$container" in
            all)
                ALLOWED_TAG_PARAMS+=("core_tag" "auth_tag" "ubuntu_ldms_tag" "kafkapump_tag" "victoriapump_tag" "telemetry_receiver_tag" "omnia_branch")
                BUILDING_CORE=true
                ;;
            oim)
                ALLOWED_TAG_PARAMS+=("core_tag" "auth_tag" "image_builder_tag" "omnia_branch")
                BUILDING_CORE=true
                ;;
            core)
                ALLOWED_TAG_PARAMS+=("core_tag" "omnia_branch")
                BUILDING_CORE=true
                ;;
            pcs)
                ALLOWED_TAG_PARAMS+=("pcs_tag")
                ;;
            auth)
                ALLOWED_TAG_PARAMS+=("auth_tag")
                ;;
            ubuntu-ldms)
                ALLOWED_TAG_PARAMS+=("ubuntu_ldms_tag")
                ;;
            pipeline)
                ALLOWED_TAG_PARAMS+=("core_tag" "auth_tag" "ubuntu_ldms_tag" "kafkapump_tag" "victoriapump_tag" "telemetry_receiver_tag" "omnia_branch")
                BUILDING_CORE=true
                ;;
            telemetry)
                ALLOWED_TAG_PARAMS+=("kafkapump_tag" "victoriapump_tag" "telemetry_receiver_tag")
                ;;
            kafkapump)
                ALLOWED_TAG_PARAMS+=("kafkapump_tag")
                ;;
            victoriapump)
                ALLOWED_TAG_PARAMS+=("victoriapump_tag")
                ;;
            telemetry-receiver)
                ALLOWED_TAG_PARAMS+=("telemetry_receiver_tag")
                ;;
            image-builder)
                ALLOWED_TAG_PARAMS+=("image_builder_tag")
                ;;
            build-stream)
                ALLOWED_TAG_PARAMS+=("build_stream_tag")
                ;;
            *)
                echo -e "${RED}Invalid container: $container. Available options: oim, all, core, pcs, auth, ubuntu-ldms, pipeline, telemetry, kafkapump, victoriapump, telemetry-receiver, image-builder, build-stream.${NC}"
                exit 1
                ;;
        esac
    done
    
    # Check for invalid parameters with context-specific message
    if [ ${#INVALID_PARAMS[@]} -ne 0 ]; then
        echo -e "${RED}Error: Invalid parameter(s): ${INVALID_PARAMS[*]}${NC}"
        echo -e "${YELLOW}Valid parameters for '$1': ${COMMON_PARAMS[*]} ${ALLOWED_TAG_PARAMS[*]}${NC}"
        exit 1
    fi
    
    # Validate parameters against the combined allowed list
    validate_container_params "$1" "${ALLOWED_TAG_PARAMS[@]}"
    
    # Now build the containers
    for container in "${containers[@]}"; do
        case "$container" in
            all)
                build_omnia_core
                build_omnia_auth
                build_ubuntu_ldms
                build_kafkapump
                build_victoriapump
                build_telemetry_receiver
                build_omnia_build_stream
                ;;
            oim)
                build_omnia_core
                build_omnia_auth
                build_image_builder
                build_omnia_build_stream
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
                build_kafkapump
                build_victoriapump
                build_telemetry_receiver
                build_omnia_build_stream
                ;;
            telemetry)
                build_kafkapump
                build_victoriapump
                build_telemetry_receiver
                ;;
            kafkapump)
                build_kafkapump
                ;;
            victoriapump)
                build_victoriapump
                ;;
            telemetry-receiver)
                build_telemetry_receiver
                ;;
            image-builder)
                build_image_builder
                ;;
            build-stream)
                build_omnia_build_stream
                ;;
        esac
    done
        ;;
esac

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
