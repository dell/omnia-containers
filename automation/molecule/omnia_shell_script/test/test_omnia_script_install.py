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

import pytest
from automation_library.utils import common_utils as utils
from automation_library.vars import validation_vars as vars
from automation_library.vars import validation_msg as msgs


def test_service_running_installed():
    """
    Verify that omnia_core.service is active (installed state).
    """
    msg = utils.check_service_status(vars.SERVICE_NAME, vars.SERVICE_STATUS_COMMAND)
    print(msg)
    assert msgs.SERVICE_ACTIVE_MSG in msg, msgs.SERVICE_INACTIVE_MSG


def test_container_exists_installed():
    """
    Verify that the omnia_core container exists (installed state).
    """
    msg = utils.check_container_status(vars.CONTAINER_NAME, vars.LIST_CONTAINERS_COMMAND)
    print(msg)
    assert msgs.CONTAINER_EXISTS_MSG in msg, msgs.CONTAINER_NOT_EXISTS_MSG


def test_quadlet_file_and_systemd_service_file_exist():
    """
    Verify the Quadlet .container file and the systemd service file exist
    and print their contents.
    """
    # Check quadlet file
    quadlet_msg = utils.check_quadlet_file(vars.QUADLET_FILE_PATH)
    print(quadlet_msg)
    assert msgs.QUADLET_FILE_EXISTS_MSG in quadlet_msg, msgs.QUADLET_FILE_NOT_EXISTS_MSG

    # Check systemd service file 
    service_msg = utils.check_systemd_service_file(vars.SYSTEMD_SERVICE_PATH, vars.SERVICE_NAME)
    print(service_msg)
    assert msgs.SYSTEMD_SERVICE_EXISTS_MSG in service_msg, msgs.SYSTEMD_SERVICE_NOT_EXISTS_MSG


def test_metadata_file_exists_in_container():
    """
    Verify that the omnia metadata file exists inside the container (installed state)
    using podman exec.
    """
    msg = utils.check_metadata_file_in_container_exec(
        vars.CONTAINER_NAME, 
        vars.METADATA_PATH_IN_CONTAINER, 
        vars.CHECK_METADATA_COMMAND
    )
    print(msg)
    assert msgs.METADATA_EXISTS_MSG in msg, msgs.METADATA_NOT_EXISTS_MSG
