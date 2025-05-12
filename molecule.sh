#!/bin/bash

# THIS SCRIPT EXECUTES THE MOLECULE SCENARIOS IN PARTICULAR ORDER

SCENARIO_FILE="scenario_order.txt"

# Exit if the scenario file doesn't exist
if [ ! -f "$SCENARIO_FILE" ]; then
  echo "Error: $SCENARIO_FILE not found!"
  exit 1
fi

MOLECULE_COMMAND="$1"
if [ "$MOLECULE_COMMAND" = "all" ]; then
    MOLECULE_COMMAND="test"
fi

ALL_SUCCESS=true

# Open file descriptor 3 for reading the scenario file
exec 3< "$SCENARIO_FILE"

# Loop through each scenario
while IFS= read -r scenario <&3; do
  if [ -d "molecule/$scenario" ]; then
    echo "Running $MOLECULE_COMMAND for scenario: $scenario"
    molecule "$MOLECULE_COMMAND" -s "$scenario"
    if [ $? -ne 0 ]; then
      echo "Error: Molecule $MOLECULE_COMMAND failed for scenario: $scenario"
      ALL_SUCCESS=false
    fi
  else
    echo "Warning: Scenario directory molecule/$scenario does not exist."
    ALL_SUCCESS=false
  fi
done

# Close file descriptor 3
exec 3<&-

if $ALL_SUCCESS; then
  echo "All scenarios executed successfully in the specified order."
else
  echo "Some scenarios failed or were missing."
  exit 1
fi
