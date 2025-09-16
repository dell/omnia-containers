# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.


# Name of the systemd service installed by omnia
SERVICE_NAME = "omnia_core.service"

# Name of the container
CONTAINER_NAME = "omnia_core"

# Full path where the systemd service file and quadlet file  should exist
SYSTEMD_SERVICE_PATH = f"/run/systemd/generator/{SERVICE_NAME}"
QUADLET_FILE_PATH = f"/etc/containers/systemd/omnia_core.container"

# Path inside the container where omnia's metadata file is stored
METADATA_PATH_IN_CONTAINER = "/opt/omnia/.data/oim_metadata.yml"

# Command to check systemd service status
SERVICE_STATUS_COMMAND = "systemctl status {service_name}"

# Command to list all containers (using podman), formatted to get just the names
LIST_CONTAINERS_COMMAND = "podman ps -a --format '{{.Names}}'"

# Command to check for metadata file
CHECK_METADATA_COMMAND = "podman exec -it {container_name} ls {metadata_path}"

# Name of the systemd target
TARGET_NAME = "omnia.target"

# Command to check systemd target status
TARGET_STATUS_COMMAND = "systemctl status {target_name}"
