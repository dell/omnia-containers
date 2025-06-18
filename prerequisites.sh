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

# Function to install packages on RHEL/CentOS
install_rhel() {
    sudo dnf update -y
    sudo dnf install -y python3.11
    sudo dnf install -y sshpass
}

# Function to install packages on Ubuntu
install_ubuntu() {
    sudo apt update -y
    sudo apt install -y python3.11 python3.11-venv
    sudo apt install -y sshpass
}

# Detect the OS and call the appropriate function
if [ -f /etc/redhat-release ]; then
    install_rhel
elif [ -f /etc/lsb-release ]; then
    install_ubuntu
else
    echo "Unsupported OS"
    exit 1
fi

# Create the directory for the virtual environment if it doesn't exist
if [ ! -d "/opt/omnia" ]; then
    sudo mkdir -p /opt/omnia
    sudo chown $USER:$USER /opt/omnia
fi

# Check if the virtual environment already exists
if [ ! -d "/opt/omnia/omnia_test" ]; then
    # Create a virtual environment
    python3.11 -m venv /opt/omnia/omnia_test
fi

# Activate the virtual environment
source /opt/omnia/omnia_test/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install pip packages from test_requirement.txt
pip install -r test_requirement.txt

# Deactivate the virtual environment
deactivate

echo "Setup complete. Virtual environment created at /opt/omnia/omnia_test for testing."
