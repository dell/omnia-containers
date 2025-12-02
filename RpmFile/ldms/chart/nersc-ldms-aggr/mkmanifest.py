#!/usr/bin/env python3
"""Generate manifest for cluster specific variables"""

import os
import sys
import logging
import yaml
import json
import argparse

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Exception classes
class Error(Exception):
    """Generic Error Exception"""
    pass

class NoMachineNameException(Error):
    pass

class NoScratchPathException(Error):
    pass

class NoManifestTemplateException(Error):
    pass

class FailedManifestCreateException(Error):
    pass

class NoIPException(Error):
    pass

# Utility functions
def remove_prefix(input_string, prefix):
    """pre-python-3.9 function to remove prefix string"""
    if prefix and input_string.startswith(prefix):
        return input_string[len(prefix):]
    return input_string

def remove_suffix(input_string, suffix):
    """pre-python-3.9 function to remove suffix string"""
    if suffix and input_string.endswith(suffix):
        return input_string[:-len(suffix)]
    return input_string

def safe_get(dic, keys, default=None):
    """Safely get nested dict key."""
    for k in keys:
        if not isinstance(dic, dict):
            return default
        dic = dic.get(k)
        if dic is None:
            return default
    return dic

def load_yaml_file(path, required=True):
    """Load a YAML file, optionally required."""
    if not os.path.exists(path):
        if required:
            logging.error(f"Required YAML file missing: {path}")
            raise FileNotFoundError(path)
        else:
            logging.warning(f"Optional YAML file missing: {path}")
            return None
    with open(path, 'r') as fh:
        return yaml.safe_load(fh)

def load_json_file(path, required=True):
    """Load a JSON file, optionally required."""
    if not os.path.exists(path):
        if required:
            logging.error(f"Required JSON file missing: {path}")
            raise FileNotFoundError(path)
        else:
            logging.warning(f"Optional JSON file missing: {path}")
            return None
    with open(path, 'r') as fh:
        return json.load(fh)

def harvest_cluster_info(cluster_file):
    """Extract machine name and network variables."""
    conf = load_yaml_file(cluster_file, required=False)
    if conf is None:
        raise FileNotFoundError(f"Cluster file {cluster_file} not found.")
    machine_name = safe_get(conf, ['nersc', 'machineName'])
    if not machine_name:
        logging.error("No machine name found in cluster config!")
        raise NoMachineNameException()
    logging.info(f"Machine name: {machine_name}")
    return machine_name

def harvest_network_vars(vars_file):
    """Extract network-related variables from vars yaml."""
    vars_data = load_yaml_file(vars_file, required=False)
    if vars_data is None:
        raise FileNotFoundError(f"Vars file {vars_file} not found.")
    try:
        allvars = vars_data['all']['vars']
        ldms_agg_ip_hsn = allvars['ldms_agg_ip_hsn']
        hsn_network_prefix = allvars['hsn_network_prefix']
        ldms_agg_gateway_hsn = allvars['bare_metal_nfs_lb']
        ldms_agg_ip_cmn = allvars['ldms_agg_ip_cmn']
        ldms_agg_gateway_cmn = allvars['ldms_agg_gateway_cmn']
        ldms_agg_subnet_prefix_cmn = allvars['cmn_virtual_ip_range']
        omni_network_prefix = allvars['omni_network_prefix']
    except KeyError as e:
        logging.error(f"Missing expected key in vars file: {e}")
        raise NoIPException()
    logging.debug(
        "NetworkAttachDefinition debug\n"
        f"ldms_agg_ip_hsn: {ldms_agg_ip_hsn}, hsn_network_prefix: {hsn_network_prefix}, "
        f"ldms_agg_ip_cmn: {ldms_agg_ip_cmn}, ldms_agg_gateway_cmn: {ldms_agg_gateway_cmn}, "
        f"ldms_agg_subnet_prefix_cmn: {ldms_agg_subnet_prefix_cmn}, omni_network_prefix: {omni_network_prefix}"
    )
    return {
        'ldms_agg_ip_hsn': ldms_agg_ip_hsn,
        'hsn_network_prefix': hsn_network_prefix,
        'ldms_agg_gateway_hsn': ldms_agg_gateway_hsn,
        'ldms_agg_ip_cmn': ldms_agg_ip_cmn,
        'ldms_agg_gateway_cmn': ldms_agg_gateway_cmn,
        'ldms_agg_subnet_prefix_cmn': ldms_agg_subnet_prefix_cmn,
        'omni_network_prefix': omni_network_prefix,
    }

def harvest_replica_info(map_file):
    """Process replica map JSON and extract aggs and replicas."""
    rep_map = load_json_file(map_file)
    store_stateful_replicas = {}
    aggs = []
    replicas_exporter = 0

    for key, val in rep_map.items():
        if key == "stream":
            continue
        store_stateful_replicas[key] = len(val.get('store', []))
        logging.info(f"Replica key: {key}, count: {store_stateful_replicas[key]}")

    for ntype, v1 in rep_map.items():
        if ntype == 'stream':
            replicas_exporter += 1
            continue
        for ltype, v2 in v1.items():
            replicas_exporter += len(v2)
    logging.info(f"Total exporter replicas: {replicas_exporter}")

    for ntype, val in rep_map.items():
        if ntype == 'stream':
            continue
        for agg in val.get('agg', []):
            aggs.append({
                'name':     agg['LDMSD_ALIAS'],
                'conf':     agg['LDMSD_CONF'],
                'env':      f"/ldms_conf/ldms-env.nersc-ldms-aggr.{agg['LDMSD_ALIAS_LONG']}.sh",
                'port':     agg['LDMSD_PORT'],
            })
    logging.debug(json.dumps(aggs, indent=4, sort_keys=True))
    return aggs, store_stateful_replicas, replicas_exporter

def harvest_sys_config(sys_conf_path):
    """Extract namespace, imagePullSecretsOption, and unique ldms auth info."""
    sys_conf = load_json_file(sys_conf_path)
    sys_opts = sys_conf.get('sys_opts', {})
    namespace = sys_opts.get('namespace')
    img_pull_sec_opt = sys_opts.get('imagePullSecretsOption')
    mounts = {}

    for node_conf in sys_conf.get('node_types',{}).values():
        for conf in (node_conf, node_conf.get('sampler', {})):
            auth_type = conf.get('auth_type')
            if not auth_type:
                continue
            entry = {
                "auth_secret": conf.get("auth_secret"),
                "auth_secret_file": conf.get("auth_secret_file")
            }
            if auth_type not in mounts:
                mounts[auth_type] = []
            if entry not in mounts[auth_type]:
                mounts[auth_type].append(entry)

    conf = sys_conf.get('stream', None)
    if conf:
        auth_type = conf.get('auth_type')
        if auth_type:
            entry = {
                "auth_secret": conf.get("auth_secret"),
                "auth_secret_file": conf.get("auth_secret_file")
            }
            if auth_type not in mounts:
                mounts[auth_type] = []
            if entry not in mounts[auth_type]:
                mounts[auth_type].append(entry)

    return namespace, img_pull_sec_opt, mounts

def update_manifest(manifest, aggs, store_stateful_replicas, replicas_exporter, net_vars, namespace, img_pull_opts, all_mounts):
    
    charts = safe_get(manifest, ['spec', 'charts'], [])
    for x in charts:
        if x.get('name') == 'nersc-ldms-aggr':
            if x.get('values') is None:
                x['values'] = {}
            if x['values'].get('statefulSet') is None:
                x['values']['statefulSet'] = {}

            if net_vars is not None:
                x['values']['net_atat_def'] = {
                    'hsn': {
                        'name': "ipvlan-ldms-agg-hsn",
                        'iface': "hsn0",
                        'subnet': net_vars['hsn_network_prefix'],
                        'rangeStart': net_vars['ldms_agg_ip_hsn'],
                        'rangeEnd': net_vars['ldms_agg_ip_hsn'],
                        'gateway': None,
                        'routes': [{"dst": "0.0.0.0/0"}]
                    },
                    'cmn': {
                        'name': "ipvlan-ldms-agg-cmn",
                        'iface': "bond0.cmn0",
                        'subnet': net_vars['ldms_agg_subnet_prefix_cmn'],
                        'rangeStart': net_vars['ldms_agg_ip_cmn'],
                        'rangeEnd': net_vars['ldms_agg_ip_cmn'],
                        'gateway': net_vars['ldms_agg_gateway_cmn'],
                        'routes': [
                            {"dst": "0.0.0.0/0"},
                            {"dst": net_vars['omni_network_prefix'], "gw": net_vars['ldms_agg_gateway_cmn']}
                        ]
                    }
                }
            else:
                x['values']['net_atat_def'] = None
            if img_pull_opts is not None:
                x['values']['imagePullSecretsOption'] = img_pull_opts
            if namespace is not None:
                x['namespace'] = namespace
                x['values']['namespace'] = namespace

            x['values']['authVolOption'] = []
            x['values']['authVolMountOption'] = []

            if all_mounts:
                # Iterate over auth type
                for auth_type, auth_vals in all_mounts.items():
                    # We just append these
                    if auth_type == "ovis":
                        for sec in auth_vals: 
                            auth_secret = sec.get("auth_secret")
                            x['values']['authVolMountOption'].append(
                                {
                                    "mountPath" : f"/{auth_secret}",
                                    "name" : auth_secret
                                }
                            )        
                            x['values']['authVolOption'].append(
                                { 
                                    "name": auth_secret,
                                    "secret": {
                                        "secretName": auth_secret,
                                        "defaultMode": "0o400"
                                    }
                                }
                            )
                    if auth_type == "munge":
                        for sec in auth_vals:
                            auth_secret = sec.get("auth_secret")
                            x['values']['authVolMountOption'].append(
                                {
                                    "mountPath" : f"/{auth_secret}",
                                    "name" : auth_secret
                                }
                            )        
                            x['values']['authVolOption'].append(
                                { 
                                    "name": auth_secret,
                                    "secret": {
                                        "secretName": auth_secret,
                                        "defaultMode": "0o400"
                                    }
                                }
                            )
                            
            x['values']['statefulSet']['exporter'] = {'replicas': replicas_exporter}
            x['values']['statefulSet']['store'] = [{'name': k, 'replicas': v} for k, v in store_stateful_replicas.items()]
            x['values']['aggs'] = aggs
            logging.info("Manifest updated for nersc-ldms-aggr chart.")
    return manifest

def write_yaml_file(path, data, description=None):
    """Write YAML data to file."""
    try:
        with open(path, 'w') as fh:
            yaml.dump(data, fh, indent=2)
        if description:
            logging.info(f"Wrote {description} to {path}")
    except Exception as e:
        logging.error(f"Failed to write {description or 'YAML'} to {path}: {e}")
        raise FailedManifestCreateException()

def main():
    parser = argparse.ArgumentParser(description="Generate manifest for cluster specific variables")
    parser.add_argument('--cluster-file', default="/etc/shasta.yml", help="Path to cluster YAML")
    parser.add_argument('--manifest-template', default="manifest.yaml.in", help="Path to manifest template YAML")
    parser.add_argument('--output-manifest', default="manifest.yaml", help="Path for output manifest")
    parser.add_argument('--replica-map', default="out_dir/nersc-ldmsd-port-map.json", help="Path to replica map JSON")
    parser.add_argument('--sys_conf', default='ldms_machine_config.json', help="Path to ldms_machine_config JSON")
    parser.add_argument('--values-output', default="values.yaml", help="Path for output values.yaml")
    args = parser.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))

    cluster_file = os.path.abspath(args.cluster_file)
    manifest_template_file = os.path.join(here, args.manifest_template)
    manifest_output_file = os.path.join(here, args.output_manifest)
    replica_map_file = os.path.join(here, args.replica_map)
    sys_conf = os.path.join(here, args.sys_conf)
    values_output_file = os.path.join(here, args.values_output)

    logging.info(f"JOB: Generate manifest: {manifest_output_file}")

    # Step 1: Cluster info and vars file
    net_vars = None
    machine_name = None
    try:
        machine_name = harvest_cluster_info(cluster_file)
        vars_file = os.path.join(here, "..", "..", f"{machine_name}_vars", "nersc.yaml")
        try:
            net_vars = harvest_network_vars(vars_file)
        except FileNotFoundError:
            logging.warning(f"Vars file {vars_file} not found. Skipping population of network variables.")
    except FileNotFoundError:
        logging.warning(f"Cluster file {cluster_file} not found. Skipping population of network variables.")

    # Step 2: Replica info
    aggs, store_stateful_replicas, replicas_exporter = harvest_replica_info(replica_map_file)

    # Step 3: System config
    namespace, img_pull_sec_opt, all_mounts = harvest_sys_config(sys_conf)

    # Step 4: Load manifest template
    manifest = load_yaml_file(manifest_template_file)
    if not manifest:
        logging.error("Manifest template could not be loaded.")
        raise NoManifestTemplateException()

    # Step 5: Update manifest
    manifest = update_manifest(manifest, aggs, store_stateful_replicas, replicas_exporter, net_vars, namespace, img_pull_sec_opt, all_mounts)

    # Step 6: Write manifest.yaml
    write_yaml_file(manifest_output_file, manifest, description="manifest")

    # Step 7: Write values.yaml as before
    chart_values = None
    for chart in manifest.get('spec', {}).get('charts', []):
        if chart.get('name') == 'nersc-ldms-aggr':
            chart_values = chart.get('values')
            break

    if chart_values is not None:
        write_yaml_file(values_output_file, chart_values, description="values.yaml")
    else:
        logging.error("Could not find values for 'nersc-ldms-aggr' chart to write to values.yaml")
        raise FailedManifestCreateException("Missing values for 'nersc-ldms-aggr' chart")

    logging.info("Manifest generation complete.")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logging.critical(f"Fatal error: {e}")
        sys.exit(1)

