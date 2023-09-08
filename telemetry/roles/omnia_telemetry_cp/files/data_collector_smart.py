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
Module to fetch smart parameters.
'''
import common_parser
import invoke_commands
import common_logging
import utility

def get_using_smartctl(parameter):
    '''
    Gets the following parameters using smartctl.
    1.Smart: Smart health
    2.SMARTHDATemp: Hard Disk temperature
    '''
    dict_smartctl={}
    # get available storage devices
    command='smartctl --scan|cut -f 1 -d " "'
    hdd_output=invoke_commands.call_command_with_pipe(command)
    if hdd_output is not None:
        hdd_list=common_parser.split_by_regex(hdd_output,"\n")
        for hdd in hdd_list:
            #initialization
            if parameter=="smart":
                dict_smartctl[hdd]=utility.Result.UNKNOWN.value
            elif parameter=="SMARTHDATemp":
                dict_smartctl[hdd]=utility.Result.NO_DATA.value

            # Form the command and execute
            command='smartctl -a '+hdd
            # Use run_command because in few cases command gives output but return code is non zero.
            command_output=invoke_commands.run_command(command)
            if command_output is not None:

                if parameter=="SMARTHDATemp":
                    # Get temperature
                    # Search for following pattern
                    # Current Drive Temperature:     23 C
                    pattern="Current Drive Temperature:\\s*(.*)"
                    temperature=common_parser.query_from_txt(command_output,pattern)
                    if temperature is None:
                        # Search for another pattern
                        # Temperature:                        25 Celsius
                        pattern="Temperature:\\s*(.*)"
                        temperature=common_parser.query_from_txt(command_output,pattern)
                    if temperature is not None:
                        dict_smartctl[hdd]=temperature.strip()

                elif parameter=="smart":
                    '''get SMART health status.
                    Few drives give "SMART Health Status" value and other gives 
                    "SMART overall-health self-assessment test result" value.
                    So we check for both.
                    '''
                    pattern="SMART Health Status:\\s*(.*)"
                    smart_health_status=common_parser.query_from_txt(command_output,pattern)
                    pattern="SMART overall-health self-assessment test result:\\s*(.*)"
                    smart_overall_health_self_assessment=common_parser.query_from_txt(command_output,pattern)

                    if smart_health_status is None and smart_overall_health_self_assessment is None:
                        dict_smartctl[hdd]=utility.Result.UNKNOWN.value
                    elif smart_health_status is not None:
                        if smart_health_status.strip()=="OK":
                            dict_smartctl[hdd]=utility.Result.SUCCESS.value
                        else:
                            dict_smartctl[hdd]=utility.Result.FAILURE.value
                    elif smart_overall_health_self_assessment is not None:
                        if smart_overall_health_self_assessment.strip()=="PASSED":
                            dict_smartctl[hdd]=utility.Result.SUCCESS.value
                        else:
                            dict_smartctl[hdd]=utility.Result.FAILURE.value
            else:
                common_logging.log_error("data_collector_smart:get_using_smartctl",command+ " output is None")
    else:
        common_logging.log_error("data_collector_smart:get_using_smartctl","smartctl scan output is None")
    return dict_smartctl