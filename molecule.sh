#THIS SCRIPT EXECUTES THE MOLECULE SCENARIOS IN PERTICULAR ORDER

#!/bin/bash

# File containing the order of scenarios
SCENARIO_FILE="scenario_order.txt"

# Check if the file exists
if [ ! -f "$SCENARIO_FILE" ]; then
  echo "Error: $SCENARIO_FILE not found!"
fi

MOLECULE_COMMAND="$1"
if [ "$MOLECULE_COMMAND" = "all" ]; then
    MOLECULE_COMMAND="test"
fi
# Loop through each scenario in the file
while IFS= read -r scenario; do
  if [ -d "molecule/$scenario" ]; then
    echo "Running tests for scenario: $scenario"

    molecule "$MOLECULE_COMMAND" -s "$scenario" -- -i ../inv

    if [ $? -ne 0 ]; then
      echo "Error: Molecule test failed for scenario: $scenario"
    fi
  else
    echo "Warning: Scenario directory molecule/$scenario does not exist."
  fi
done < "$SCENARIO_FILE"

echo "All scenarios executed successfully in the specified order."
