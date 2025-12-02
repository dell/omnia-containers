#!/bin/bash
set -e

if [ ! -f "build_auth/.git-credentials" ]; then
    echo "File not found: build_auth/.git-credentials
 If git repository needs auth token, save token to build_auth/.git-credentials
    "
fi
systemctl --user enable --now podman.socket
TESTS_DIR="testsd"
#DOCKER_FILE="Dockerfile.bld_n_run.ubuntu"
DOCKER_FILE="oci/Dockerfile.bld_n_run.ubuntu24.04"
NOW="$(date +"%Y%m%dT%H%M")"
IMG_NAME="ubuntu-ldms"
IMG_REG_REMOTE="YOUR_REGISTRY_HERE"
IMG_REG_CLUSTER="registry.local/nersc"
echo "VARS:
SCRIPT_DIR=$SCRIPT_DIR
DOCKER_FILE=$DOCKER_FILE
NOW=$NOW
IMG_NAME=$IMG_NAME
IMG_REG_REMOTE=$IMG_REG_REMOTE
IMG_REG_CLUSTER=$IMG_REG_CLUSTER
"
echo "Broaden the Build Context, in order to copy the tests into the container image"
pushd ../

echo "build=$IMG_NAME:$NOW"
echo "[>>] Build"
podman --storage-driver vfs --root $HOME/.local/share/containers/vfs-storage/ build . -f $DOCKER_FILE --tag $IMG_NAME:$NOW --build-arg VER="0.1.0"

echo "[>>] TAG"
podman --storage-driver vfs --root $HOME/.local/share/containers/vfs-storage/ tag $IMG_NAME:$NOW $IMG_REG_REMOTE/$IMG_NAME:$NOW
read -p "[>>] PUSH to $IMG_REG_REMOTE? [y/N]" DO_PUSH_REMOTE
if [ "$DO_PUSH_REMOTE" == 'y' ]; then
  podman --storage-driver vfs --root $HOME/.local/share/containers/vfs-storage/ push --format=docker $IMG_REG_REMOTE/$IMG_NAME:$NOW
  echo "[>>] SEARCH"
  podman search --list-tags --limit 999 $IMG_REG_REMOTE/$IMG_NAME
fi
read -p "[>>] PUSH to $IMG_REG_CLUSTER? [y/N]" DO_PUSH_CLUSTER 
if [ "$DO_PUSH_CLUSTER" == 'y' ]; then
  echo "[>>] Test if user is logged into $IMG_REG_CLUSTER"
  podman login --get-login $IMG_REG_CLUSTER
  echo "[>>] LOGIN to $IMG_REG_CLUSTER"
  podman login $IMG_REG_CLUSTER
  echo "[>>] SYNC $IMG_REG_CLUSTER"
  skopeo sync --src docker --dest docker "$IMG_REG_REMOTE/$IMG_NAME:$NOW" "$IMG_REG_CLUSTER"
  echo "[>>] SEARCH for ${IMG_NAME} in $IMG_REG_CLUSTER"
  podman search --list-tags --limit 999 "$IMG_REG_CLUSTER/${IMG_NAME}"
fi
echo "[--] DONE"
echo "
new_image=${IMG_NAME}:${NOW}
tag=$NOW
registry=registry.local
repository="nersc/${IMG_NAME}"
"
MANIF_TEMPLATE="../chart/nersc-ldms-aggr/manifest.yaml.in"
echo "[>>] UPDATE loftsman manifest template:$MANIF_TEMPLATE"
if [ -f "$MANIF_TEMPLATE" ]; then
  (
    sed -i "s|tag:.*|tag: $NOW|g" "$MANIF_TEMPLATE" 

    echo "Manifest template patched"
  )
else
    echo "Manifest template not found"
fi
echo "[--] DONE
#
# Test Image Locally
#
podman --storage-driver vfs --root $HOME/.local/share/containers/vfs-storage/ run -it $IMG_NAME:$NOW
# For debug: Set LDMS_REPO to your source path, and apt-get install  gdb
podman --storage-driver vfs --root $HOME/.local/share/containers/vfs-storage/ run -it --mount type=bind,source=\$LDMS_REPO,target=/builds/ovis $IMG_NAME:$NOW 
"
