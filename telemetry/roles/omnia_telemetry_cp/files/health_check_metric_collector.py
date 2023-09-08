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
Module to gather health check metrics.
'''

import data_collector_kubernetes
import data_collector_smart
import data_collector_storage
import data_collector_os
from collections import defaultdict
import utility
import data_collector_nvidia_gpu
import data_collector_amd_gpu

class HealthCheckMetricCollector:
    '''
    HealthCheckMetricCollector class is responsible for collecting all health check metrics.
    '''
    def __init__(self):
        self.health_check_metric_output_dict={}

    def get_using_kubernetes(self):
        '''
        This method initiates kubernetes calls to data_collector_kubernetes and retrieves necessary values.
        '''
        #get using "kubectl get pods" commands
        kubernetes_pods_dict=data_collector_kubernetes.get_kubectl_get_pods()
        self.health_check_metric_output_dict["Kubernetespodsstatus"]=\
            kubernetes_pods_dict["Kubernetespodsstatus"]
        #get using "kubectl get nodes" commands
        kubernetes_nodes_dict=data_collector_kubernetes.get_kubectl_get_nodes()
        self.health_check_metric_output_dict["Kuberneteschildnode"]=\
            kubernetes_nodes_dict["Kuberneteschildnode"]
        self.health_check_metric_output_dict["kubernetesnodesstatus"]=\
            kubernetes_nodes_dict["kubernetesnodesstatus"]
        #get using "kubectl get componentstatus" commands
        kubernetes_component_status_dict=data_collector_kubernetes.get_kubectl_get_cs()
        self.health_check_metric_output_dict["kubernetescomponentsstatus"]=\
            kubernetes_component_status_dict["kubernetescomponentsstatus"]

    def get_health_node_dmesg(self):
        '''
           This method checks if dmesg is giving some output or not.
        '''
        dmesg_op_dict = data_collector_os.get_health_node_dmesg()
        self.health_check_metric_output_dict["Dmesg"] = dmesg_op_dict["Dmesg"]

    def get_beegfs_details(self):
        '''
            This method checks if beeGFS client is reachable or not.
        '''
        beegfs_op_dict = data_collector_storage.get_beegfs_details()
        self.health_check_metric_output_dict["Beegfs client Reachable"] = beegfs_op_dict["Beegfs client Reachable"]

    def get_nvidia_metrics(self):
        '''
        This method collects all the nvidia gpu health metrics
        '''
        health_metrics = defaultdict(list)

        # run nvidia-smi command and store output in a variable
        nvidia_metrics_cmd_output = data_collector_nvidia_gpu.get_nvidia_metrics_output()

        # get driver health details for NVIDIA GPU
        health_metrics['gpu_driver'] = data_collector_nvidia_gpu.get_gpu_health_driver \
            (nvidia_metrics_cmd_output)

        # get nvlink health details for NVIDIA GPU
        health_metrics['gpu_nvlink'] = data_collector_nvidia_gpu.get_gpu_health_nvlink \
            (nvidia_metrics_cmd_output)

        # get pcie health details for NVIDIA GPUs
        health_metrics['gpu_pcie'] = data_collector_nvidia_gpu.get_gpu_health_pcie \
            (nvidia_metrics_cmd_output)

        # get pmu health details for NVIDIA GPUs
        health_metrics['gpu_pmu'] = data_collector_nvidia_gpu.get_gpu_health_pmu \
            (nvidia_metrics_cmd_output)

        # get power health details for NVIDIA GPUs
        gpu_power_limit,gpu_power_draw = data_collector_nvidia_gpu.get_gpu_health_power \
            (nvidia_metrics_cmd_output)
        health_metrics['gpu_power_max'] = gpu_power_limit
        health_metrics['gpu_power_avg'] = gpu_power_draw


        # get thermal health details for NVIDIA GPUs
        health_metrics['gpu_thermal'] = data_collector_nvidia_gpu.get_gpu_health_thermal \
            (nvidia_metrics_cmd_output)

        self.gpu_health_metrics(health_metrics)


    def get_amd_metrics(self):
        '''
        This method collects all the amd gpu health metrics
        '''
        health_metrics = defaultdict(list)
        # get driver health details for AMD GPU
        health_metrics['gpu_driver'] = data_collector_amd_gpu.get_gpu_health_driver()
        # get nvlink health details for AMD GPU

        health_metrics['gpu_nvlink'] = data_collector_amd_gpu.get_gpu_health_nvlink()

        # get pcie health details for AMD GPU
        health_metrics['gpu_pcie'] = data_collector_amd_gpu.get_gpu_health_pcie()

        # get pmu health details for AMD GPU
        health_metrics['gpu_pmu'] = data_collector_amd_gpu.get_gpu_health_nvlink()

        # get power health details for AMD GPU
        gpu_power_max,gpu_power_avg = data_collector_amd_gpu.get_gpu_health_power()
        health_metrics['gpu_power_max'] = gpu_power_max
        health_metrics['gpu_power_avg'] = gpu_power_avg

        # get thermal health details for AMD GPU
        health_metrics['gpu_thermal'] = data_collector_amd_gpu.get_gpu_health_thermal()

        self.gpu_health_metrics(health_metrics)

    def gpu_health_metrics(self,health_metrics):
        '''
        This method calls the gpu health metric methods for storing metric data
        '''
        self.get_gpu_driver_health_metric(health_metrics['gpu_driver'])
        self.get_gpu_nvlink_health_metric(health_metrics['gpu_nvlink'])
        self.get_gpu_pcie_health_metric(health_metrics['gpu_pcie'])
        self.get_gpu_pmu_health_metric(health_metrics['gpu_pmu'])
        self.get_gpu_power_health_metric(health_metrics['gpu_power_max'], \
                                         health_metrics['gpu_power_avg'])
        self.get_gpu_thermal_health_metric(health_metrics['gpu_thermal'])

    def get_gpu_driver_health_metric(self, gpu_driver):
        '''
		This method collects gpu driver health details
		'''
        if gpu_driver is not None:
            for index, item in enumerate(gpu_driver):
                if item is not None or item!="N/A":
                    self.health_check_metric_output_dict["gpu_driver_health:gpu" \
                                                        + str(index)] = \
                                                           utility.Result.SUCCESS.value
                else:
                    self.health_check_metric_output_dict["gpu_driver_health:gpu" \
                                                        + str(index)] = \
                                                           utility.Result.FAILURE.value
        else:
            self.health_check_metric_output_dict["gpu_driver_health:gpu"] = \
                utility.Result.UNKNOWN.value

    def get_gpu_nvlink_health_metric(self, gpu_nvlink):
        '''
		This method collects gpu nvlink health details
		'''
        if gpu_nvlink is not None:
            for index, item in gpu_nvlink.items():
                if item is not None:
                    if 'inActive' not in item:
                        self.health_check_metric_output_dict["gpu_health_nvlink:gpu" \
                                                            + str(index)] = \
                                                                utility.Result.SUCCESS.value
                    else:
                        self.health_check_metric_output_dict["gpu_health_nvlink:gpu" \
                                                            + str(index)] = \
                                                                utility.Result.FAILURE.value
                else:
                    self.health_check_metric_output_dict["gpu_health_nvlink:gpu"] = \
                        utility.Result.UNKNOWN.value
        else:
            self.health_check_metric_output_dict["gpu_health_nvlink:gpu"] = \
                utility.Result.UNKNOWN.value

    def get_gpu_pcie_health_metric(self, gpu_pcie):
        '''
		This method collects gpu pcie health details
		'''
        if gpu_pcie is not None:
            for index, item in enumerate(gpu_pcie):
                if item is not None or item!="N/A":
                    self.health_check_metric_output_dict["gpu_health_pcie:gpu" \
                                                         + str(index)] = \
                                                            utility.Result.SUCCESS.value
                else:
                    self.health_check_metric_output_dict["gpu_health_pcie:gpu" \
                                                         + str(index)] = \
                                                            utility.Result.FAILURE.value
        else:
            self.health_check_metric_output_dict["gpu_health_pcie:gpu"] = \
                utility.Result.UNKNOWN.value

    def get_gpu_pmu_health_metric(self, gpu_pmu):
        '''
		This method collects gpu power management unit health details
		'''
        if gpu_pmu is not None:
            for index, item in enumerate(gpu_pmu):
                if item is not None or item.strip() == "Enabled" or item.strip() == "Supported":
                    self.health_check_metric_output_dict["gpu_health_pmu:gpu" \
                                                         + str(index)] = \
                                                            utility.Result.SUCCESS.value
                else:
                    self.health_check_metric_output_dict["gpu_health_pmu:gpu" \
                                                         + str(index)] = \
                                                            utility.Result.FAILURE.value
        else:
            self.health_check_metric_output_dict["gpu_health_pmu:gpu"] = \
                utility.Result.UNKNOWN.value

    def get_gpu_power_health_metric(self, gpu_power_max,gpu_power_avg):
        '''
		This method collects gpu power health details
		'''
        if gpu_power_max is not None and gpu_power_avg is not None:
            for index,item in enumerate(gpu_power_avg):
                if float(item) <= float(gpu_power_max[index]):
                    self.health_check_metric_output_dict["gpu_health_power:gpu" \
                                                         + str(index)] = \
                                                            utility.Result.SUCCESS.value
                else:
                    self.health_check_metric_output_dict["gpu_health_power:gpu" \
                                                         + str(index)] = \
                                                            utility.Result.FAILURE.value
        else:
            self.health_check_metric_output_dict["gpu_health_power:gpu"] = \
                utility.Result.UNKNOWN.value

    def get_gpu_thermal_health_metric(self, gpu_thermal):
        '''
		This method collects gpu thermal/temperature health details
		'''
        if gpu_thermal is not None:
            for index, item in enumerate(gpu_thermal):
                if int(item) < 85:
                    self.health_check_metric_output_dict["gpu_temperature:gpu" \
                                                         + str(index)] = \
                                                            utility.Result.SUCCESS.value
                else:
                    self.health_check_metric_output_dict["gpu_temperature:gpu" \
                                                         + str(index)] = \
                                                            utility.Result.FAILURE.value

        else:
            self.health_check_metric_output_dict["gpu_temperature:gpu"] = \
                utility.Result.UNKNOWN.value

    def get_smart_health_parameters(self):
        '''
        Get the following health metric parameters:
        1. smart
        '''
        smart_dict=data_collector_smart.get_using_smartctl("smart")
        for key in smart_dict.keys():
            self.health_check_metric_output_dict["smart:"+key]=smart_dict[key]

    def metric_collector(self, aggregation_level="compute"):
        '''
        This method aggregates all the health check parameters.
        '''
        self.health_check_metric_output_dict={}
        self.get_health_node_dmesg()
        self.get_beegfs_details()
        self.get_nvidia_metrics()
        self.get_amd_metrics()
        self.get_smart_health_parameters()

        if aggregation_level in ["manager", "manager,login"]:
            # Get following information's through kubernetes
            # 1.Kubernetespodsstatus
            # 2.Kuberneteschildnode
            # 3.kubernetesnodesstatus
            # 4.kubernetescomponentsstatus
            self.get_using_kubernetes()
