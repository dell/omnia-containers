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

import db_utils
import vars
import validation_msg


def test_fetch_full_nodeinfo_table():
    """
    Test that the full nodeinfo table query returns non-empty result.
    """

    rows = db_utils.run_full_table_query(
        vars.DB_CREDENTIALS,
        vars.TABLE_NODEINFO,
        vars.CONTAINER_NAME,
        vars.FULL_QUERY
    )
    assert rows.strip(), f"{validation_msg.NO_DATA_MSG} {vars.TABLE_NODEINFO}"


def test_all_nodes_status_booted():
    """
    Test that all nodes in the nodeinfo table have a booted status.
    """
        
    status_map = db_utils.run_status_query(
        vars.DB_CREDENTIALS,
        vars.TABLE_NODEINFO,
        vars.CONTAINER_NAME,
        vars.STATUS_QUERY
    )
    assert status_map, f"{validation_msg.NO_STATUS_MSG} {vars.TABLE_NODEINFO}"
    
