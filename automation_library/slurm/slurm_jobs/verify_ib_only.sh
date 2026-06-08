#!/bin/bash
#SBATCH --job-name=verify_ib_only
#SBATCH --partition=normal
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=1
#SBATCH --time=00:10:00
#SBATCH -w {{NODES}}
#SBATCH --output=/scratch/%u/results/verify_ib_only_%j.out

echo "============================================================"
echo "  VERIFY: Inter-Node Communication Uses InfiniBand ONLY"
echo "============================================================"
echo "Job ID  : $SLURM_JOB_ID"
echo "Nodes   : $SLURM_JOB_NODELIST"
echo "Start   : $(date)"
echo "============================================================"

# ---------------------------------------------------------------
# Environment
# ---------------------------------------------------------------
export PATH={{MPI_PATH}}:$PATH
export LD_LIBRARY_PATH={{MPI_LIB_PATH}}:$LD_LIBRARY_PATH

# Force OpenMPI to use UCX
export OMPI_MCA_pml=ucx
export OMPI_MCA_btl="^uct,tcp,openib,ofi"
export OMPI_MCA_mtl="^ofi"

# THE KEY SETTING: only allow IB-class transports
# ib = umbrella for rc, rc_mlx5, dc_mlx5, ud, ud_mlx5
# sm = shared memory (intra-node)
# self = loopback (required)
# NOTE: tcp is intentionally EXCLUDED
export UCX_TLS=ib,sm,self

# Verbose so we can see the transport selection
export UCX_LOG_LEVEL=info
export UCX_PROTO_INFO=y
export UCX_WARN_UNUSED_ENV_VARS=n

# ---------------------------------------------------------------
# Step 1: Compile a tiny MPI ping-pong
# ---------------------------------------------------------------
WORKDIR=/scratch/verify_ib_${SLURM_JOB_ID}
mkdir -p $WORKDIR && cd $WORKDIR

cat > ib_pingpong.c << 'MPIEOF'
#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);
    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    char host[256]; gethostname(host, sizeof(host));
    printf("[Rank %d] running on %s\n", rank, host);
    fflush(stdout);

    if (size != 2) {
        if (rank == 0) printf("This test needs exactly 2 ranks (one per node).\n");
        MPI_Finalize(); return 0;
    }

    size_t sizes[] = {8, 1024, 65536, 1048576, 16777216};
    int nsizes = sizeof(sizes)/sizeof(sizes[0]);
    char *buf = (char*)malloc(16777216);
    memset(buf, rank, 16777216);

    MPI_Barrier(MPI_COMM_WORLD);
    if (rank == 0) printf("\n--- Inter-node MPI Ping-Pong ---\n");

    for (int s = 0; s < nsizes; s++) {
        size_t msg = sizes[s];
        int iters = 50;

        for (int i = 0; i < 5; i++) {
            if (rank == 0) {
                MPI_Send(buf, msg, MPI_BYTE, 1, 0, MPI_COMM_WORLD);
                MPI_Recv(buf, msg, MPI_BYTE, 1, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            } else {
                MPI_Recv(buf, msg, MPI_BYTE, 0, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
                MPI_Send(buf, msg, MPI_BYTE, 0, 0, MPI_COMM_WORLD);
            }
        }

        double t0 = MPI_Wtime();
        for (int i = 0; i < iters; i++) {
            if (rank == 0) {
                MPI_Send(buf, msg, MPI_BYTE, 1, 0, MPI_COMM_WORLD);
                MPI_Recv(buf, msg, MPI_BYTE, 1, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
            } else {
                MPI_Recv(buf, msg, MPI_BYTE, 0, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
                MPI_Send(buf, msg, MPI_BYTE, 0, 0, MPI_COMM_WORLD);
            }
        }
        double t1 = MPI_Wtime();

        if (rank == 0) {
            double secs   = (t1 - t0) / iters;
            double lat_us = secs * 1e6 / 2.0;
            double bw_gbs = (2.0 * msg) / secs / (1024.0*1024.0*1024.0);
            printf("  msg=%9zu B | lat=%9.2f us | bw=%7.3f GB/s\n",
                   msg, lat_us, bw_gbs);
        }
    }

    free(buf);
    MPI_Finalize();
    return 0;
}
MPIEOF

mpicc -O2 ib_pingpong.c -o ib_pingpong \
  && echo "Compile: PASS" || { echo "Compile: FAIL"; exit 1; }

# ---------------------------------------------------------------
# Step 2: Capture IB counters BEFORE the run
# ---------------------------------------------------------------
echo ""
echo "=== IB COUNTERS BEFORE (per node) ==="
srun --ntasks-per-node=1 --label bash -c '
  for f in /sys/class/infiniband/*/ports/*/counters/port_xmit_data; do
    [ -r "$f" ] || continue
    val=$(cat "$f")
    path="${f%/counters/port_xmit_data}"
    port="${path##*/}"
    path="${path%/ports/*}"
    dev="${path##*/}"
    echo "[$(hostname -s)] ${dev}:${port} xmit_data=${val}"
  done
'

# ---------------------------------------------------------------
# Step 3: Run the ping-pong (UCX will log its transport choice)
# ---------------------------------------------------------------
echo ""
echo "=== RUN: MPI ping-pong with UCX_TLS=ib,sm,self ==="
srun --mpi=pmix ./ib_pingpong 2>&1

# ---------------------------------------------------------------
# Step 4: Capture IB counters AFTER the run
# ---------------------------------------------------------------
echo ""
echo "=== IB COUNTERS AFTER (per node) ==="
srun --ntasks-per-node=1 --label bash -c '
  for f in /sys/class/infiniband/*/ports/*/counters/port_xmit_data; do
    [ -r "$f" ] || continue
    val=$(cat "$f")
    path="${f%/counters/port_xmit_data}"
    port="${path##*/}"
    path="${path%/ports/*}"
    dev="${path##*/}"
    echo "[$(hostname -s)] ${dev}:${port} xmit_data=${val}"
  done
'

echo ""
echo "============================================================"
echo "  COMPLETE at $(date)"
echo "============================================================"
echo ""
echo ">>> RESULTS INTERPRETATION:"
echo "  1. Compile: PASS  -- mpicc succeeded"
echo "  2. Rank lines      -- both ranks communicated"
echo "  3. UCX log shows rc_mlx5/dc_mlx5 (NOT tcp) -- IB RDMA confirmed"
echo "  4. IB counters increased   -- physical IB traffic confirmed"
echo "  5. bw > 10 GB/s for large messages -- RDMA performance confirmed"
