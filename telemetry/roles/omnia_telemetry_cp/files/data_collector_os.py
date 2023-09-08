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

'''
Module to fetch miscellaneous parameters that does not require parsing.
'''

import invoke_commands
import common_logging
import utility


def get_health_node_dmesg():
    '''
    Returns number of unique users logged in
    '''
    dmesg_op_dict = {}
    dmesg_op_dict["Dmesg"] = utility.Result.UNKNOWN.value
    dmesg_cmd = 'dmesg --level=err'
    output = invoke_commands.call_command(dmesg_cmd)
    if output is not None:
        dmesg_op_dict["Dmesg"] = utility.Result.FAILURE.value
        common_logging.log_error("data_collector_os:get_health_node_dmesg",
                                 "dmesg gave errors" + output)
    elif output is None:
        dmesg_op_dict["Dmesg"] = utility.Result.SUCCESS.value
    return dmesg_op_dict

def get_unique_loggedin_users():
    '''
    Returns number of unique users logged in
    '''
    output=invoke_commands.call_command_with_pipe('who|cut -f 1 -d " "|sort -u|wc -l')
    if output is None:
        return utility.Result.NO_DATA.value
    else:
        return output