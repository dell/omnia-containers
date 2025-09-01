# Copyright 2024 Dell Inc. or its subsidiaries. All Rights Reserved.
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

 
# Container details
CONTAINER_NAME = "omnia_provision"
 
# DB credentials
DB_CREDENTIALS = {
    "user": "postgres",
    "password": "",
    "database": "omniadb"
}
 
# Table/column details
TABLE_NODEINFO = "cluster.nodeinfo"
NODE_STATUS_COLUMN = "status"
ADMIN_IP_COLUMN = "admin_ip"
HOSTNAME_COLUMN = "hostname"
EXPECTED_STATUS = "booted"
FULL_QUERY = "*"
STATUS_QUERY = "node, status"


