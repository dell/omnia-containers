#!/bin/bash
set -e
# Parse command-line inputs for SLURM repo URL and name.
print_usage() {
    echo "Usage: $0 -u|--url <SLURM_REPO_URL> -n|--name <SLURM_REPO_NAME>"
    echo "       or: $0 <SLURM_REPO_URL> <SLURM_REPO_NAME>"
}

SLURM_REPO_URL=""
SLURM_REPO_NAME=""

# Support both flags and positional args
while [[ $# -gt 0 ]]; do
    case "$1" in
        -u|--url)
            SLURM_REPO_URL="$2"
            shift 2
            ;;
        -n|--name)
            SLURM_REPO_NAME="$2"
            shift 2
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            # accept two positional args if flags not used
            if [[ -z "$SLURM_REPO_URL" ]]; then
                SLURM_REPO_URL="$1"
            elif [[ -z "$SLURM_REPO_NAME" ]]; then
                SLURM_REPO_NAME="$1"
            else
                echo "Unexpected argument: $1"
                print_usage
                exit 1
            fi
            shift
            ;;
    esac
done

if [[ -z "$SLURM_REPO_URL" || -z "$SLURM_REPO_NAME" ]]; then
    echo "Warning: SLURM_REPO_URL and SLURM_REPO_NAME are not provided, user might not be able to generate ldms slurm metrics."
    print_usage
fi

echo "Using SLURM_REPO_URL=$SLURM_REPO_URL"
echo "Using SLURM_REPO_NAME=$SLURM_REPO_NAME"

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
if [[ -n "$SLURM_REPO_URL" && -n "$SLURM_REPO_NAME" ]]; then
    echo "Starting container build with SLURM_REPO_URL=$SLURM_REPO_URL and SLURM_REPO_NAME=$SLURM_REPO_NAME"
    bash "./start_build_container.rockylinux10.bash" "$SLURM_REPO_URL" "$SLURM_REPO_NAME"
else
    echo "Warning: Starting container build without SLURM "
    bash "./start_build_container.rockylinux10.bash"
fi

