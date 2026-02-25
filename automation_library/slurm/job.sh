#!/bin/bash

# Specify the number of CPUs to use
#SBATCH --cpus-per-task=4

# Specify the maximum runtime
#SBATCH --time=0-00:30:00

# Specify the output file
#SBATCH --output=output.txt

# Specify the error file
#SBATCH --error=error.txt

# Your commands go here
echo "Job completed"
