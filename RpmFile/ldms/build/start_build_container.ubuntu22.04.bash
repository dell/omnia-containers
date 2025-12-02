#!/bin/bash

if [ -z "$LDMS_REPO" ] ; then
    echo "Set path to your clone of https://github.com/ovis-hpc/ovis.git:
export LDMS_REPO=<PATH_TO_LDMS_CLONE>
"
    exit 1
fi
export LDMS_REPO="$(readlink -f "$LDMS_REPO")"

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

echo "Start build container. From there: pushd /builds/ovis/ && ../scripts/build_ldms.ubuntu22.04.bash"
podman run -it --rm \
  --mount type=bind,source=$LDMS_REPO,target=/builds/ovis \
  --mount type=bind,source=$SCRIPT_DIR,target=/builds/scripts \
  --mount type=bind,source=../testing,target=/builds/testing \
  ubuntu:22.04 \
  /bin/bash


