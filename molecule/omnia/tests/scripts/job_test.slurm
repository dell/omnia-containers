#!/bin/bash
#SBATCH --job-name=mpi_matrix_mult_python
#SBATCH --output=/home/testuser/output_%j.log
#SBATCH --error=/home/testuser/error_%j.log
#SBATCH --ntasks=n
#SBATCH --nodes=n
#SBATCH --time=00:10:00

set -x  # <-- Enable script debugging

echo "Running as user: $(whoami)"
echo "Running on host: $(hostname)"

# Check environment
which mpicc
which srun

# Load or source modules if required
# source /etc/profile.d/modules.sh

export PATH=$PATH:/home/benchmarks/openmpi-4.1.6/openmpi/bin/
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/benchmarks/openmpi-4.1.6/openmpi/lib/

export OMPI_CC=gcc
export OMPI_CXX=g++

# Compile and run
echo "Compiling MPI program..."
mpicc -o /home/scripts/hello /home/scripts/hello_mpi.c

echo "Running MPI job with srun..."
srun --mpi=pmix /home/scripts/hello
