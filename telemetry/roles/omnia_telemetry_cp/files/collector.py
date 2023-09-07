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
Module to initiate omnia telemetry data collection
'''
import time
import sys
import signal
import common_logging
import utility
import prerequisite
from dbupdate import DatabaseClient
from regular_metric_collector import RegularMetricCollector
from gpu_metric_collector import GPUMetricCollector
from health_check_metric_collector import HealthCheckMetricCollector

# Declare global variables for metric collector objects and DBCLIENT_OBJ
REGULAR_METRIC_COLLECTOR_OBJ = None
HEALTH_METRIC_COLLECTOR_OBJ = None
GPU_METRIC_COLLECTOR_OBJ = None
DBCLIENT_OBJ = None

def cleanup():
    '''
    Cleanup operations to be executed during graceful shutdown.
    '''
    global REGULAR_METRIC_COLLECTOR_OBJ, HEALTH_METRIC_COLLECTOR_OBJ, GPU_METRIC_COLLECTOR_OBJ
    global DBCLIENT_OBJ

    # Delete the metric collector objects if they exist
    if REGULAR_METRIC_COLLECTOR_OBJ:
        del REGULAR_METRIC_COLLECTOR_OBJ
    if HEALTH_METRIC_COLLECTOR_OBJ:
        del HEALTH_METRIC_COLLECTOR_OBJ
    if GPU_METRIC_COLLECTOR_OBJ:
        del GPU_METRIC_COLLECTOR_OBJ

    # Close any open database connections
    if DBCLIENT_OBJ:
        DBCLIENT_OBJ.db_close()

    # Close syslog
    common_logging.close_syslog()

def handle_sigterm(signum, frame):
    '''
    sigterm handler for restart,stop omnia telemetry service
    '''
    cleanup()
    sys.exit(0)

def main():
    '''
    Module main to initiate the telemetry data collection functionality
    '''
    global REGULAR_METRIC_COLLECTOR_OBJ, HEALTH_METRIC_COLLECTOR_OBJ, GPU_METRIC_COLLECTOR_OBJ
    global DBCLIENT_OBJ

    common_logging.setup_syslog('omnia_telemetry')

    # Register signal handler for SIGTERM
    signal.signal(signal.SIGTERM, handle_sigterm)

    # Copy telemetry ini to dictionary dict_telemetry_ini
    if utility.set_telemetry_ini_values() is True:
        # Sleep for fuzzy_offset value
        time.sleep(utility.generate_random_fuzzy_offset(int(utility.dict_telemetry_ini["fuzzy_offset"])))

        # Create objects for different telemetry groups
        if utility.dict_telemetry_ini["collect_regular_metrics"] =="true":
            REGULAR_METRIC_COLLECTOR_OBJ=RegularMetricCollector()
        if utility.dict_telemetry_ini["collect_health_check_metrics"]=="true":
            HEALTH_METRIC_COLLECTOR_OBJ=HealthCheckMetricCollector()
        if utility.dict_telemetry_ini["collect_gpu_metrics"]=="true":
            GPU_METRIC_COLLECTOR_OBJ=GPUMetricCollector()

        # Create object for database client
        DBCLIENT_OBJ = DatabaseClient()

        while True:
            combined_result_dict={"Regular Metric":{},"Health Check Metric":{},"GPU Metric":{}}

            if utility.dict_telemetry_ini["collect_regular_metrics"] == "true":
                REGULAR_METRIC_COLLECTOR_OBJ.metric_collector(utility.dict_telemetry_ini["group_info"])
                combined_result_dict["Regular Metric"]=REGULAR_METRIC_COLLECTOR_OBJ.regular_metric_output_dict

            if utility.dict_telemetry_ini["collect_health_check_metrics"] == "true":
                HEALTH_METRIC_COLLECTOR_OBJ.metric_collector(utility.dict_telemetry_ini["group_info"])
                combined_result_dict["Health Check Metric"]=HEALTH_METRIC_COLLECTOR_OBJ.health_check_metric_output_dict

            if utility.dict_telemetry_ini["collect_gpu_metrics"] == "true":
                GPU_METRIC_COLLECTOR_OBJ.metric_collector(utility.dict_telemetry_ini["group_info"])
                combined_result_dict["GPU Metric"]=GPU_METRIC_COLLECTOR_OBJ.gpu_metric_output_dict
            #DB Update
            DBCLIENT_OBJ.update_db(combined_result_dict,prerequisite.get_system_name())
            #sleep for omnia_telemetry_collection_interval time
            time.sleep(int(utility.dict_telemetry_ini["omnia_telemetry_collection_interval"]))

if __name__ == "__main__":
    main()