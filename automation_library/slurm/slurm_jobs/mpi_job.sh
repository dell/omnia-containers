#!/bin/bash
#SBATCH --job-name=omnia_test_mpi
#SBATCH --partition=normal
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --ntasks-per-node=1
#SBATCH --output={{OUTPUT_PATH}}/omnia_test_mpi_%j.out
#SBATCH --error={{OUTPUT_PATH}}/omnia_test_mpi_%j.err
#SBATCH --time=00:05:00

# OpenMPI compile+run job for OMNIA Slurm test automation.
# Creates a simple MPI C program, compiles with mpicc, and runs it.

# Create user-writable temp directory
TEMP_DIR="$HOME/tmp/slurm_job_$SLURM_JOB_ID"
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"

echo "=== Basic MPI Job ==="
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $(hostname)"
echo "Number of tasks: $SLURM_NTASKS"
echo "Task ID: $SLURM_PROCID"
echo "Node list: $SLURM_NODELIST"
echo "Working directory: $TEMP_DIR"
echo "---"

# Create a simple MPI program
cat > hello_mpi.c << 'EOF'
#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
int main(int argc, char *argv[]) {
    int rank, size;
    char processor_name[MPI_MAX_PROCESSOR_NAME];
    int name_len;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    MPI_Get_processor_name(processor_name, &name_len);

    printf("Hello World from rank %d of %d on processor %s\n",
           rank, size, processor_name);

    // Simple barrier test
    MPI_Barrier(MPI_COMM_WORLD);

    if (rank == 0) {
        printf("All %d processes completed the barrier\n", size);
    }

    MPI_Finalize();
    return 0;
}
EOF

# Compile the MPI program
echo "Compiling MPI program..."
echo "MPI_HOME: $MPI_HOME"
echo "PATH: $PATH"
echo "LD_LIBRARY_PATH: $LD_LIBRARY_PATH"
echo "mpicc location: $(which mpicc 2>/dev/null || echo 'not found')"
mpicc -o hello_mpi hello_mpi.c 2>&1
if [ $? -eq 0 ]; then
    echo "Compilation successful"
    echo "Running MPI program..."

    # Run the MPI program using srun for better SLURM integration
    srun --mpi=pmi2 ./hello_mpi

    echo ""
    echo "MPI job completed successfully"
else
    echo "Compilation failed"
    exit 1
fi

