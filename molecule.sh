# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

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
