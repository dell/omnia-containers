#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create host map for ldms config file generation from nodes found in the SLS and HSM.
"""

import os
import json
import yaml
import time
import shutil
import logging
import argparse
import requests
import urllib3
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# --- Constants ---
# These values must match exactly the hardware type names from the API
HWTYPE_CPU = "WNC"
HWTYPE_GPU = "GrizzlyPeakNC"
SKIP_XNAMES = {"x1402c0s7b1n1", "x1402c0s7b1n0", "x1402c2s6b1n0", "x1402c2s6b1n1"}

def setup_logging(verbose=False):
    """Configure logging facility."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s %(levelname)s: %(message)s')

def setup_requests_session():
    """Create durable HTTP requests session with retry."""
    urllib3.disable_warnings()
    retry_strategy = Retry(
        total=5,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

http = setup_requests_session()

def read_shasta_config(shasta_config_file='/etc/shasta.yml'):
    """Read Shasta configuration file."""
    try:
        with open(shasta_config_file, 'r') as rfp:
            return yaml.safe_load(rfp)
    except Exception as e:
        logging.error(f"Could not read {shasta_config_file}: {e}")
        raise

def read_cray_token():
    """Get API token from Cray token directory."""
    token_dir = os.path.expanduser("~/.config/cray/tokens")
    try:
        filenames = next(os.walk(token_dir))[2]
        if not filenames:
            raise RuntimeError("No token files found in cray token directory.")
        token_path = os.path.join(token_dir, filenames[0])
        with open(token_path) as rfp:
            data = json.load(rfp)
            return data['access_token']
    except Exception as e:
        logging.error(f"Could not read Cray token: {e}")
        raise

def load_config(config_path):
    """Load the json config file given a file path."""
    if not os.path.exists(config_path):
        return {}
    with open(config_path, 'r') as f:
        return json.load(f)

def print_node_list(nodes):
    """Format the node list data structure"""
    node_str = f"{'hostname':>15}{'xname':>18}{'ip_address':>15}{'role':>15}{'subrole':>15}\n"
    for node in nodes:
        node_str += (
            f"{node['hostname']:>15}"
            f"{node['hostaddr']:>15}"
            f"{node['ip_address']:>15}"
            f"{node['role']:>15}"
            f"{node['subrole']:>15}"
            "\n"
        )
    return node_str


def str_presenter(dumper, data):
    """YAML multiline string presenter."""
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

yaml.add_representer(str, str_presenter)

class LdmsdManager:
    """Generate ldmsd config and params."""

    def __init__(self, config=None):
        self.config = config
        self.base_dir = os.path.dirname(os.path.realpath(__file__))
        self.out_dir = os.path.join(self.base_dir, "out_dir")
        self.hwtype_map = {}
        self.nodes = {}

        # Load Shasta config and Cray token once
        self.shasta = read_shasta_config()
        self.token = read_cray_token()
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }

    def api_get(self, url):
        """Helper for authenticated API GET requests."""
        response = http.get(url, headers=self.headers, allow_redirects=True, verify=False)
        response.raise_for_status()
        return response.json()

    def main(self):
        """Make host lists for each node type."""
        now = time.strftime("%Y%m%d-%H%M%S", time.localtime())
        logging.info(f"BEGIN LDMS INIT: {now}")

        # Clean out previous
        if os.path.isdir(self.out_dir):
            logging.info(f"Clean out_dir: {self.out_dir}")
            shutil.rmtree(self.out_dir)
        os.makedirs(self.out_dir, exist_ok=True)

        # Initialize hardware type map
        hwtype_map_file = os.path.join(self.out_dir, "hwtype_map.json")
        if os.path.isfile(hwtype_map_file):
            logging.info("Loading hwtype_map from cache")
            with open(hwtype_map_file, "r") as fh:
                self.hwtype_map = json.load(fh)
        else:
            logging.info("Fetching hwtype_map from API")
            self.hwtype_map = self.get_hwtype_map()
            with open(hwtype_map_file, "w") as fh:
                json.dump(self.hwtype_map, fh, ensure_ascii=False, indent=4)

        # Create node lists
        for ldmsd_name, ldmsd_conf in self.config['node_types'].items():
            host_map_file = ldmsd_conf.get("host_map_file")
            base_type, suffix_type = (ldmsd_name.split('-') + [None])[:2]
            hwtype = None
            if suffix_type == "cpu":
                hwtype = HWTYPE_CPU
            elif suffix_type == 'gpu':
                hwtype = HWTYPE_GPU
            nodes_role_all = self.get_nodes(base_type)
            if base_type == 'compute' and hwtype:
                filtered_nodes = [
                    node for node in nodes_role_all
                    if node['hostaddr'][:13] in self.hwtype_map.get(hwtype, [])
                ]
                self.nodes[ldmsd_name] = filtered_nodes
            else:
                self.nodes[ldmsd_name] = nodes_role_all
            logging.info(f"Node Count: {ldmsd_name:.<20} {len(self.nodes[ldmsd_name])}")
            with open(host_map_file, "w") as fh:
                json.dump(self.nodes[ldmsd_name], fh, ensure_ascii=False, indent=4)

    def get_nodes(self, role):
        """Get nodes running an LDMS sampler daemon for a given role."""
        nodes = []
        host_map = []
        logging.debug(f"Getting Nodes for Role: {role}")
        sls_network_chn = self.get_sls_network_chn()
        sls_hardware = self.get_sls_hardware()
        for item in sls_network_chn:
            hostname = item['hostname']
            xname = next((x['xname'] for x in sls_hardware if x['hostname'] == hostname), None)
            if xname in SKIP_XNAMES:
                continue
            if xname:
                host_map.append({'ip_address': item['ip_address'], 'hostname': hostname, 'xname': xname})
        active_nodes = self.get_active_nodes(role)
        for node in active_nodes:
            host_info = next((x for x in host_map if x['xname'] == node['ID']), None)
            if host_info:
                nodes.append({
                    'hostname': host_info['hostname'],
                    'hostaddr': f"{host_info['xname']}h0",
                    'ip_address': host_info['ip_address'],
                    'role': node['Role'],
                    'subrole': node.get('SubRole', '')
                })

        logging.debug(f"Nodes Found:\n{print_node_list(nodes)}")
        logging.debug(f"Nodes Found: {len(nodes)}")
        return nodes

    def get_active_nodes(self, role):
        """Get active nodes for a given role, filtering for State = On or Ready."""
        hsm_api = f"http://{self.shasta['shasta']['api_endpoint']}/apis/smd/hsm/v2/State/Components"
        hsm_query = f"{hsm_api}?Role={role.capitalize()}"
        logging.debug(f"Querying HSM: {hsm_query}")
        data = self.api_get(hsm_query)
        node_components = sorted(
            [i for i in data['Components'] if i.get('NID')],
            key=lambda d: d['NID']
        )
        return node_components

    def get_hwtype_map(self):
        """Get map of compute node types."""
        url = f"http://{self.shasta['shasta']['api_endpoint']}/apis/smd/hsm/v2/Inventory/Hardware"
        data = self.api_get(url)
        hwtype_map = {}
        for i in data:
            node_info = i.get('NodeLocationInfo')
            if node_info and node_info.get('Description'):
                hwtype = node_info['Description']
                hwtype_map.setdefault(hwtype, []).append(i['ID'])
        return hwtype_map

    def get_sls_hardware(self):
        """Get list of hostnames and xnames from SLS hardware API endpoint."""
        url = f"http://{self.shasta['shasta']['api_endpoint']}/apis/sls/v1/hardware"
        data = self.api_get(url)
        return [
            {'hostname': i['ExtraProperties']['Aliases'][0], 'xname': i['Xname']}
            for i in data if 'ExtraProperties' in i and 'Aliases' in i['ExtraProperties']
        ]

    def get_sls_network_chn(self):
        """Get list of hostnames and IP addresses from SLS network CHN API endpoint."""
        url = f"http://{self.shasta['shasta']['api_endpoint']}/apis/sls/v1/networks/CHN"
        logging.debug(f"Querying SLS: {url}")
        data = self.api_get(url)
        sls_name_lookup = []
        for subnet in data['ExtraProperties']['Subnets']:
            for res in subnet.get('IPReservations', []):
                if 'Aliases' in res and 'nid' in res['Aliases'][0]:
                    hostname = res['Aliases'][0]
                else:
                    hostname = res['Name']
                sls_name_lookup.append({'hostname': hostname, 'ip_address': res['IPAddress']})
        return sls_name_lookup

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Turn on verbose output"
    )
    parser.add_argument(
        "--config", '-c',
        default='ldms_machine_config.json',
        help="Path to JSON config file"
    )
    args = parser.parse_args()

    config = load_config(args.config)
    verbose = args.verbose if args.verbose is not None else config.get("verbose", False)
    setup_logging(verbose)

    agg = LdmsdManager(config)
    agg.main()

if __name__ == '__main__':
    main()
