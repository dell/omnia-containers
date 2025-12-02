#!/bin/bash
set -e

# Repository details
SLURM_REPO_URL="http://100.96.22.157/repo/slurm/rhel/10.0/x86_64/"
SLURM_REPO_NAME="x86_64_slurm_custom"

# Get the current working directory
CURRENT_DIR=$(pwd)

# Append with RpmFile/ldms/build/
TARGET_DIR="$CURRENT_DIR/RpmFile/ldms/build/"

# Print the result
echo "Target directory: $TARGET_DIR"

# === Step 1: Clone OVIS repo if not already present ===
REPO_URL="https://github.com/ovis-hpc/ovis.git"
DEST_DIR="$HOME/ovis-code"

mkdir -p "$DEST_DIR"
cd "$DEST_DIR"

if [ ! -d "ovis" ]; then
    echo "Cloning OVIS repository..."
    git clone "$REPO_URL"
else
    echo "Repository already exists. Updating..."
    cd ovis
    git pull origin main
    cd ..
fi

# === Step 2: Export LDMS_REPO path ===
export LDMS_REPO="$DEST_DIR/ovis"
echo "LDMS_REPO set to $LDMS_REPO"

# === Step 3: Start container build script ===
# Change into working  directory
if [ -d "$TARGET_DIR" ]; then
    cd "$TARGET_DIR"
    echo "Changed into $TARGET_DIR"
else
    echo "Directory $TARGET_DIR does not exist."
fi
echo "Starting container build..."
bash "./start_build_container.rockylinux10.bash" "$SLURM_REPO_URL" "$SLURM_REPO_NAME"
