# Copyright 2023 Dell Inc. or its subsidiaries. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Utility functions for miscellaneous tasks.
"""

import random
from enum import Enum
import common_parser
import common_logging
import platform

# Dictionary to hold the telemetry.ini values. telemetry.ini holds telemetry user inputs
dict_telemetry_ini = {}
TELEMETRY_INI_PATH = "/opt/omnia/telemetry/telemetry.ini"

class Result(Enum):
    '''
    Enum values for mapping value to result in database
    '''
    NO_DATA = "No data"
    SUCCESS = "Pass"
    FAILURE = "Fail"
    UNKNOWN = "Unknown"

def set_telemetry_ini_values():
    """
        Set the ini values from TELEMETRY_INI_PATH
    """
    global dict_telemetry_ini
    dict_telemetry_ini = common_parser.get_ini_dict(TELEMETRY_INI_PATH)["omnia_telemetry"]
    if dict_telemetry_ini is not None:
        return True
    common_logging.log_error("Utility:set_telemetry_ini_values", "Unable to parse telemetry ini")
    return False


def generate_random_fuzzy_offset(fuzzy_offset=60):
    """
    Generate a random fuzzy offset.

    Args:
        fuzzy_offset (float): The maximum offset value.

    Returns:
        float: A random fuzzy offset value rounded to 2 decimal places.
    """
    random_fuzzy_offset = round(random.uniform(0, fuzzy_offset), 2)
    return random_fuzzy_offset


def get_system_hostname():
    ''' Get the system hostname '''
    try:
        hostname = platform.uname()[1]
        return hostname
    except Exception as exc:
        common_logging.log_error('utility:get_system_hostname', f"An error occurred: {exc}")
        return None
