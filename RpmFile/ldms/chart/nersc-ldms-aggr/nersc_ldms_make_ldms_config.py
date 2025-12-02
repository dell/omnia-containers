#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create ldmsd config files and parameters from host map files.
"""

import argparse
import json
import logging
import os
import shutil
import time
import yaml

def setup_logging(verbose=False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s %(levelname)s: %(message)s')

def load_config(config_path):
    """Load JSON config file from a given file path."""
    if not os.path.exists(config_path):
        return {}
    with open(config_path, 'r') as f:
        return json.load(f)

def str_presenter(dumper, data):
    """Custom YAML representer for multiline strings."""
    if len(data.splitlines()) > 1:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

class LdmsdManager:
    """Generate ldmsd configs and parameters."""

    def __init__(self, config=None):
        self.config = config
        self.namespace = self.config['sys_opts']['namespace']
        self.base_dir = os.path.dirname(os.path.realpath(__file__))
        self.out_dir = os.path.join(self.base_dir, "out_dir")
        self.env = {}
        self.configmaps = []
        self.ldmsd_port = 6000

    def main(self):
        """Main loop."""
        now = time.strftime("%Y%m%d-%H%M%S", time.localtime())
        logging.info(f"BEGIN LDMS Make LDMS Config: {now}")
        self.make_agg_configs()
        self.make_store_configs()
        self.make_stream_config()
        self.make_exporter_configs()
        self.make_munge_configs()
        self.create_env_json()
        self.create_env_yaml()
        self.create_configmaps()
        self.copy_configmaps_to_helm()
        now = time.strftime("%Y%m%d-%H%M%S", time.localtime())
        logging.info(f"END LDMS Make LDMS Config: {now}")

    def make_munge_configs(self):
        logging.info("Make Agg Configs")
        munge_configs = {}
        
        for node_conf in self.config.get('node_types',{}).values():
            for conf in (node_conf, node_conf.get('sampler', {})):
                auth_type = conf.get('auth_type')
                if not auth_type:
                    continue
                if auth_type == "munge":
                    auth_secret = conf.get('auth_secret')
                    auth_secret_file = conf.get('auth_secret_file')
                    conf_file_name = f"{auth_secret}_munge.conf"
                    munge_configs[conf_file_name] = {
                        "MUNGED_BIN" : "/usr/sbin/munged",
                        "MUNGE_RUN_DIR": f"/run/{auth_secret}",
                        "MUNGE_PID_FILE": "$MUNGE_RUN_DIR/munged.pid",
                        "MUNGE_SOCKET_FILE": "$MUNGE_RUN_DIR/munge.socket",
                        "MUNGE_LOG_DIR" : "/var/log/munge",
                        "MUNGE_LOG_FILE" : f"$MUNGE_LOG_DIR/{auth_secret}.log",
                        "MUNGE_KEY_FILE" : f"/{auth_secret}/munge.key"
                    }
        for conf_file_name, munge_conf in munge_configs.items():
            config_lines = []
            for key, value in munge_conf.items():
                config_lines.append(f'export {key}="{value}"')
            with open(os.path.join(self.out_dir, conf_file_name), "w") as f:
                f.write("\n".join(config_lines))
            self.configmaps.extend([ 
                os.path.join(self.out_dir, conf_file_name)
            ])

    def make_agg_configs(self):
        logging.info("Make Agg Configs")

        for ldmsd_name, ldmsd_conf in self.config['node_types'].items():
            # grab auth data
            auth_type = ldmsd_conf.get('auth_type')
            auth_secret = ldmsd_conf.get('auth_secret')
            auth_secret_file = ldmsd_conf.get('auth_secret_file')
            if auth_type == "munge":
                ldms_auth_option = f"socket=/run/{auth_secret}/munge.socket"
            elif auth_type == "ovis":
                ldms_auth_option = f"conf=/{auth_secret}/{auth_secret_file}"
            
            host_map_file = ldmsd_conf["host_map_file"]
            with open(host_map_file) as fh:
                node_list = json.load(fh)
            split = ldmsd_conf.get("agg_count", 1)
            midpoint = len(node_list) // split
            for index, sub_list in enumerate(self.split_list(node_list, midpoint)):
                sub_host_map_file = host_map_file.replace(".json", f"-{index}.json")
                with open(sub_host_map_file, 'w') as fh:
                    json.dump(sub_list, fh, ensure_ascii=False, indent=4)
                self.ldmsd_port += 1
                alias_base = ldmsd_conf.get("alias", "other")
                container_alias = f"{alias_base}-{index}"
                logging.info(f"\tSPLIT: container_alias: {container_alias}, index: {index}, len sub_list: {len(sub_list)}")
                self.make_config_agg(
                    ldmsd_name=ldmsd_name,
                    ldmsd_conf=ldmsd_conf,
                    nodes=sub_list,
                    out_file=os.path.join(self.out_dir, f"ldmsd.nersc-ldms-aggr.{ldmsd_name}-{index}.conf")
                )
                self.env.setdefault(ldmsd_name, {}).setdefault('agg', []).append({
                    'LDMSD_PORT': self.ldmsd_port,
                    'LDMSD_HOST': f"nersc-ldms-aggr.{self.namespace}.svc.cluster.local",
                    'LDMSD_AUTH_PLUGIN': f"{auth_type}",
                    'LDMSD_AUTH_OPTION': f"{ldms_auth_option}",
                    'LDMSD_AUTH_SECRET': f"{auth_secret}",
                    'LDMSD_AUTH_SECRET_FILE' : f"{auth_secret_file}",
                    'LDMSD_ALIAS': container_alias,
                    'LDMSD_ALIAS_LONG': f"{ldmsd_name}-{index}",
                    'LDMSD_CONF': f"/ldms_conf/ldmsd.nersc-ldms-aggr.{ldmsd_name}-{index}.conf",
                    'EXPORTER_PORT': 9101
                })
                self.create_ldms_env(
                    os.path.join(self.out_dir, f"ldms-env.nersc-ldms-aggr.{ldmsd_name}-{index}.sh"),
                    self.env[ldmsd_name]['agg'][-1]
                )
                self.configmaps.extend([
                    os.path.join(self.out_dir, f"ldmsd.nersc-ldms-aggr.{ldmsd_name}-{index}.conf"),
                    os.path.join(self.out_dir, f"ldms-env.nersc-ldms-aggr.{ldmsd_name}-{index}.sh")
                ])

    def make_store_configs(self):
        logging.info("Make Store Configs")
        for ldmsd_name, ldmsd_conf in self.config['node_types'].items():
            # grab auth data
            auth_type = ldmsd_conf.get('auth_type')
            auth_secret = ldmsd_conf.get('auth_secret')
            auth_secret_file = ldmsd_conf.get('auth_secret_file')
            if auth_type == "munge":
                ldms_auth_option = f"socket=/run/{auth_secret}/munge.socket"
            elif auth_type == "ovis":
                ldms_auth_option = f"conf=/{auth_secret}/{auth_secret_file}"

            store_pod_index = 0
            host_map_file = ldmsd_conf["host_map_file"]
            for agg_index in range(len(self.env[ldmsd_name]['agg'])):
                with open(host_map_file.replace(".json", f"-{agg_index}.json")) as fh:
                    node_list = json.load(fh)
                nid_names = [x['hostname'] for x in node_list]
                split = ldmsd_conf.get("store_split", 99999999)
                for index, sub_list in enumerate(self.split_list(nid_names, split)):
                    alias_base = ldmsd_conf.get("alias", "other")
                    container_alias = f"{alias_base}-{store_pod_index}"
                    logging.info(
                        f"\tSPLIT: container_alias: {container_alias}, index: {index}, len sub_list: {len(sub_list)}"
                    )
                    split_regex = "|".join([f"{x}.*" for x in sub_list])
                    self.make_config_store(
                        ldmsd_name=f"{ldmsd_name}-{store_pod_index}",
                        ldmsd_agg_name=self.env[ldmsd_name]['agg'][agg_index]["LDMSD_HOST"],
                        ldmsd_agg_port=self.env[ldmsd_name]['agg'][agg_index]["LDMSD_PORT"],
                        ldmsd_conf=ldmsd_conf,
                        out_file=os.path.join(self.out_dir, f"ldmsd.nersc-ldms-store-{ldmsd_name}-{store_pod_index}.conf"),
                        split=split_regex
                    )
                    self.env.setdefault(ldmsd_name, {}).setdefault('store', []).append({
                        'LDMSD_PORT': 6001,
                        'LDMSD_HOST': f"nersc-ldms-store-{ldmsd_name}-{store_pod_index}.nersc-ldms-store.{self.namespace}.svc.cluster.local",
                        'LDMSD_AUTH_PLUGIN': auth_type,
                        'LDMSD_AUTH_SECRET': f"{auth_secret}",
                        'LDMSD_AUTH_SECRET_FILE' : f"{auth_secret_file}",
                        'LDMSD_AUTH_OPTION': f"socket=/run/{auth_secret}/munge.socket",
                        'LDMSD_ALIAS': container_alias,
                        'LDMSD_CONF': f"/ldms_conf/ldmsd.nersc-ldms-store-{ldmsd_name}-{store_pod_index}.conf",
                        'EXPORTER_PORT': 9101
                    })
                    self.create_ldms_env(
                        os.path.join(self.out_dir, f"ldms-env.nersc-ldms-store-{ldmsd_name}-{store_pod_index}.sh"),
                        self.env[ldmsd_name]['store'][-1]
                    )
                    self.configmaps.extend([
                        os.path.join(self.out_dir, f"ldmsd.nersc-ldms-store-{ldmsd_name}-{store_pod_index}.conf"),
                        os.path.join(self.out_dir, f"ldms-env.nersc-ldms-store-{ldmsd_name}-{store_pod_index}.sh")
                    ])
                    store_pod_index += 1

    def make_config_stream(self, out_file):
        """Make the ldmsd config file for the stream
        This ldmsd must talk to the other aggregators via their service name, and respective ports
        :param out_file: string path to output file
        """
        logging.info("Create Stream Config")
        if os.path.isfile(out_file):
            logging.info(f"File already present: {out_file}")
            return
        cfg = list()
        #--------
        # Get uniqe auth types
        munge_auth_sec = set( v['auth_secret'] for k, v in self.config['node_types'].items())
        for auth_secret in munge_auth_sec:
            cfg.extend([
                f"auth_add name={auth_secret} plugin=munge socket=/run/{auth_secret}/munge.socket",
            ])
        #--------
        ldms_host = "nersc-ldms-aggr.sma.svc.cluster.local"
        for k, v in self.env.items():  #  k: application, compute-cpu, compute-gpu, management
            if k == "stream":
                continue
            for index, sub_list in enumerate(v['agg']):
                ldmsd_name = f"{k}-{index}"   # e.g. compute-cpu-0
                ldmsd_port = sub_list['LDMSD_PORT']
                auth_secret = sub_list['LDMSD_AUTH_SECRET']
                auth_type = 'munge'
                auth_arg = 'socket=/run/{auth_secret}/munge.socket'
                logging.debug(f"ldmsd_name:{ldmsd_name} ldmsd_port:{ldmsd_port}, auth_type:{auth_type}, auth_arg:{auth_arg}, auth_secret:{auth_secret}")
                cfg.extend([
                    f"prdcr_add name=prdcr_{ldmsd_name} type=active interval=30000000 xprt=sock host={ldms_host} port={ldmsd_port} auth={auth_secret}",
                ])
        cfg.extend([
            "prdcr_start_regex regex=.*",
            "prdcr_subscribe stream=nersc regex=.*",
        ])
        # To avoid reading metrics, and only handle streams make a pattern that will never match
        cfg.extend([
            f"updtr_add name=stream interval=10000000 auto_interval=true  #(Honor hints if true)",
            f"updtr_prdcr_add name=stream regex=prdcr.*",
            f"updtr_match_add name=stream match=schema regex=(DONOTMATCH)"
            f"updtr_start name=stream"
        ])
        cfg.extend([
            "#Log Stream data",
            "load name=hello_sampler",
            "config name=hello_sampler producer=${HOSTNAME} instance=${HOSTNAME}/hello_sampler stream=nersc component_id=1",
            "start name=hello_sampler interval=1000000 offset=0"
        ])
        with open(out_file, 'w') as fh:
            fh.write('\n'.join(cfg))
            title = "Wrote:"
            logging.debug(f"{title:.<20} {out_file}")

    def make_stream_config(self):
        logging.info("Create Stream Config")
        auth_type = self.config['stream'].get('auth_type')
        auth_secret = self.config['stream'].get('auth_secret')
        auth_secret_file = self.config['stream'].get('auth_secret_file')
        if auth_type == "munge":
            ldms_auth_option = f"socket=/run/{auth_secret}/munge.socket"
        elif auth_type == "ovis":
            ldms_auth_option = f"conf=/{auth_secret}/{auth_secret_file}"
        else:
            logging.error(f"Unhandled auth_type. self.config: {self.config}")
            raise
        self.make_config_stream(
            out_file=os.path.join(self.out_dir, "ldmsd.nersc-ldms-stream-0.conf")
        )
        self.env.setdefault('stream', [])
        self.env['stream'].append({
            'LDMSD_PORT': 60001,
            'LDMSD_HOST': f"nersc-ldms-stream-0.nersc-ldms-stream.{self.namespace}.svc.cluster.local",
            'LDMSD_AUTH_PLUGIN': auth_type,
            'LDMSD_AUTH_SECRET': f"{auth_secret}",
            'LDMSD_AUTH_SECRET_FILE' : f"{auth_secret_file}",
            'LDMSD_AUTH_OPTION': ldms_auth_option,
            'LDMSD_CONF': "/ldms_conf/ldmsd.nersc-ldms-stream-0.conf",
            'EXPORTER_PORT': 9101,
        })
        self.create_ldms_env(
            os.path.join(self.out_dir, "ldms-env.nersc-ldms-stream-0.sh"),
            self.env['stream'][-1]
        )
        self.configmaps.extend([
            os.path.join(self.out_dir, "ldmsd.nersc-ldms-stream-0.conf"),
            os.path.join(self.out_dir, "ldms-env.nersc-ldms-stream-0.sh")
        ])

    def make_exporter_configs(self):
        logging.info("Create Exporter Config")
        expo = []
        for ntype, val in self.env.items():
            if ntype == 'stream':
                expo.append({
                    'EXPORTER_NAME': 'stream-metrics',
                    'LDMSD_HOST': val[0]['LDMSD_HOST'],
                    'LDMSD_PORT': val[0]['LDMSD_PORT'],
                    'LDMSD_AUTH_PLUGIN': val[0]['LDMSD_AUTH_PLUGIN'],
                    'LDMSD_AUTH_SECRET': val[0]['LDMSD_AUTH_SECRET'],
                    'LDMSD_AUTH_SECRET_FILE' : val[0]['LDMSD_AUTH_SECRET_FILE'],
                    'LDMSD_AUTH_OPTION': val[0]['LDMSD_AUTH_OPTION'],
                    'EXPORTER_PORT': val[0]['EXPORTER_PORT']
                })
                continue
            for agg in val.get('agg', []):
                expo.append({
                    'EXPORTER_NAME': f"agg-{agg['LDMSD_ALIAS']}-metrics",
                    'LDMSD_HOST': agg['LDMSD_HOST'],
                    'LDMSD_PORT': agg['LDMSD_PORT'],
                    'LDMSD_AUTH_PLUGIN': agg['LDMSD_AUTH_PLUGIN'],
                    'LDMSD_AUTH_SECRET': agg['LDMSD_AUTH_SECRET'],
                    'LDMSD_AUTH_SECRET_FILE': agg['LDMSD_AUTH_SECRET_FILE'],
                    'LDMSD_AUTH_OPTION': agg['LDMSD_AUTH_OPTION'],
                    'EXPORTER_PORT': agg['EXPORTER_PORT']
                })
            for store in val.get('store', []):
                expo.append({
                    'EXPORTER_NAME': f"store-{store['LDMSD_ALIAS']}-metrics",
                    'LDMSD_HOST': store['LDMSD_HOST'],
                    'LDMSD_PORT': store['LDMSD_PORT'],
                    'LDMSD_AUTH_PLUGIN': store['LDMSD_AUTH_PLUGIN'],
                    'LDMSD_AUTH_SECRET': store['LDMSD_AUTH_SECRET'],
                    'LDMSD_AUTH_SECRET_FILE': store['LDMSD_AUTH_SECRET_FILE'],
                    'LDMSD_AUTH_OPTION': store['LDMSD_AUTH_OPTION'],
                    'EXPORTER_PORT': store['EXPORTER_PORT']
                })
        for i, exporter in enumerate(expo):
            self.create_ldms_env(
                os.path.join(self.out_dir, f"expo-env.nersc-ldms-exporter-{i}.sh"),
                exporter
            )
            self.configmaps.append(
                os.path.join(self.out_dir, f"expo-env.nersc-ldms-exporter-{i}.sh")
            )

    def create_env_json(self):
        """Write env data structure to JSON."""
        with open(os.path.join(self.out_dir, "nersc-ldmsd-port-map.json"), 'w') as fh:
            json.dump(self.env, fh, ensure_ascii=False, sort_keys=True, indent=4)

    def create_env_yaml(self):
        """Write env data structure to YAML."""
        yaml.add_representer(str, str_presenter)
        yaml.representer.SafeRepresenter.add_representer(str, str_presenter)
        with open(os.path.join(self.out_dir, "nersc-ldmsd-port-map.yml"), 'w') as fh:
            #yaml.dump(self.env, fh, default_flow_style=False, sort_keys=False)
            yaml.dump(self.env, fh, default_flow_style=False)

    def create_ldms_env(self, out_file, data):
        """Create the env file used before running ldmsd."""
        with open(out_file, "w") as fh:
            for k, v in data.items():
                fh.write(f'export {k}="{v}"\n')

    def asseble_configmap_data(self, files_list):
        """Load data object with script files."""
        data = {}
        for fname in files_list:
            base_fname = os.path.basename(fname)
            if not fname in data:
                with open(fname) as fh:
                    data[base_fname] = fh.read()
        return data

    def create_configmaps(self):
        """Create configmap YAMLs for configs and scripts."""
        data = self.asseble_configmap_data(self.configmaps)
        self.create_configmap_yaml(
            name="nersc-ldms-conf",
            namespace=self.namespace,
            data=data,
            out_filename=os.path.join(self.out_dir, "cm.nersc-ldms-conf.yaml")
        )
        script_files = [
            "scripts/ldmsd.bash",
            "scripts/ldmsd_stream.bash",
            "scripts/ldms_ls.bash",
            "scripts/ldms_stats.bash",
            "scripts/ldms_exporter.bash",
            "scripts/ldms_exporter.py",
            "scripts/start_munge.bash",
            "scripts/decomp.json"
        ]
        data = self.asseble_configmap_data(script_files)
        self.create_configmap_yaml(
            name="nersc-ldms-bin",
            namespace=self.namespace,
            data=data,
            out_filename=os.path.join(self.out_dir, "cm.nersc-ldms-bin.yaml")
        )

    def copy_configmaps_to_helm(self):
        """Copy generated configmaps into the helm chart."""
        for i in ["cm.nersc-ldms-conf.yaml", "cm.nersc-ldms-bin.yaml"]:
            src_path = os.path.join(self.out_dir, i)
            dst_path = os.path.join(self.base_dir, "nersc-ldms-aggr", "templates", i)
            shutil.copy2(src_path, dst_path)

    def create_configmap_yaml(self, name, namespace, data, out_filename):
        """Creates ConfigMap YAML file, using custom str_presenter."""
        configmap = {
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'metadata': {
                'name': name,
                'namespace': namespace
            },
            'data': data
        }
        yaml.add_representer(str, str_presenter)
        yaml.representer.SafeRepresenter.add_representer(str, str_presenter)
        with open(out_filename, 'w') as fh:
            #yaml.dump(configmap, fh, default_flow_style=False, sort_keys=False)
            yaml.dump(configmap, fh, default_flow_style=False)

    def split_list(self, input_list, group_size):
        """Yield successive group_size-sized chunks from input_list."""
        for i in range(0, len(input_list), group_size):
            yield input_list[i:i + group_size]

    def make_config_agg(self, ldmsd_name, ldmsd_conf, nodes, out_file):
        """Make a new ldmsd config file for each aggregator."""
        if os.path.isfile(out_file):
            logging.info(f"File already present: {out_file}")
            return
        # auth data
        sampler = ldmsd_conf.get('sampler')
        auth_type = sampler.get('auth_type')
        auth_secret = sampler.get('auth_secret')
        auth_secret_file = sampler.get('auth_secret_file')
        if auth_type == "munge":
            ldms_auth_option = f"socket=/run/{auth_secret}/munge.socket"
        elif auth_type == "ovis":
            ldms_auth_option = f"conf=/{auth_secret}/{auth_secret_file}"
        else:
            logging.error(f"auth_type:{auth_type}")
            raise
        cfg = []
        cfg.append(f"auth_add name={auth_secret} plugin={auth_type}  {ldms_auth_option}")
        cfg.append(f"updtr_add name={ldmsd_conf['alias']} interval=10000000 auto_interval=true  #(Honor hints if true)")
        for node in nodes:
            hsn_node_prefixes = ['nid', 'service', 'workflow', 'login']
            if any(node_prefix in node['hostname'] for node_prefix in hsn_node_prefixes):
                cfg.append(f"prdcr_add name={node['hostname']} host={node['hostaddr']} type=active xprt=sock port={sampler['port']} interval=60000000 auth={auth_secret}")
            elif 'ncn-' in node['hostname']:
                cfg.append(f"prdcr_add name={node['hostname']} host={node['hostname']} type=active xprt=sock port={sampler['port']} interval=60000000 auth={auth_secret}")
            else:
                cfg.append(f"prdcr_add name={node['hostname']} host={node['ip_address']} type=active xprt=sock port={sampler['port']} interval=60000000 auth={auth_secret}")
        cfg.append("prdcr_subscribe stream=nersc regex=.*")
        cfg.append("prdcr_start_regex regex=.*")
        cfg.append(f"updtr_prdcr_add name={ldmsd_conf['alias']} regex=.*")
        cfg.append(f"updtr_match_add name={ldmsd_conf['alias']} match=schema regex=(procnetdev|procstat|vmstat|meminfo|lustre_llite|lustre2_client|loadavg|dcgm|dvs|proc_group|procdiskstats|slingshot_metrics|slingshot_info)")
        cfg.append(f"updtr_start name={ldmsd_conf['alias']}")
        with open(out_file, 'w') as fh:
            fh.write('\n'.join(cfg))

    def make_config_store(self, ldmsd_name, ldmsd_agg_name, ldmsd_agg_port, ldmsd_conf, out_file, split=None):
        """Make a store ldmsd config file for each aggregator."""
        if os.path.isfile(out_file):
            logging.debug(f"File already present: {out_file}")
            return
        # auth data
        auth_type = ldmsd_conf.get('auth_type')
        auth_secret = ldmsd_conf.get('auth_secret')
        auth_secret_file = ldmsd_conf.get('auth_secret_file')
        if auth_type == "munge":
            ldms_auth_option = f"socket=/run/{auth_secret}/munge.socket"
        elif auth_type == "ovis":
            ldms_auth_option = f"conf=/{auth_secret}/{auth_secret_file}"

        cfg = []
        cfg.append(f"auth_add name={ldmsd_name} plugin={auth_type} {ldms_auth_option}")
        cfg.append(f"prdcr_add name=prdcr_{ldmsd_name} type=active interval=30000000 xprt=sock host={ldmsd_agg_name} port={ldmsd_agg_port} auth={ldmsd_name}")
        if any(prefix in out_file for prefix in ['application', 'gpu', 'management']) and 'store' in out_file:
            cfg.append(f"updtr_add name={ldmsd_name} interval=10000000 auto_interval=true  #(Honor hints if true)")
            cfg.append(f"updtr_prdcr_add name={ldmsd_name} regex=prdcr.*")
        else:
            cfg.append(f"updtr_add name={ldmsd_name} interval=10000000")
            cfg.append(f"updtr_prdcr_add name={ldmsd_name} regex=prdcr.*")
        if split:
            cfg.append(f"updtr_match_add name={ldmsd_name} regex={split}")
        cfg.append(f"updtr_start name={ldmsd_name}")
        cfg.append("prdcr_start_regex regex=.*")
        cfg.extend([
            "# Store in kafka",
            "load name=store_avro_kafka",
            "config name=store_avro_kafka encoding=json topic=nersc-ldms",
            f"strgp_add name=kafka regex=.* plugin=store_avro_kafka container=cluster-kafka-bootstrap.{self.namespace}.svc.cluster.local:9092 decomposition=/ldms_bin/decomp.json",
            "strgp_start name=kafka"
        ])
        with open(out_file, 'w') as fh:
            fh.write('\n'.join(cfg))

    def make_config_stream2(self, out_file):
        """Make the ldmsd config file for the stream."""
        logging.info("Make Config: stream")
        if os.path.isfile(out_file):
            logging.info(f"File already present: {out_file}")
            return
        cfg = []
        #--------
        for ldmsd_name, ldmsd_conf in self.config['node_types'].items():
            # grab auth data
            auth_type = ldmsd_conf.get('auth_type')
            auth_secret = ldmsd_conf.get('auth_secret')
            auth_secret_file = ldmsd_conf.get('auth_secret_file')
            if auth_type == "munge":
                ldms_auth_option = f"socket=/run/{auth_secret}/munge.socket"
            elif auth_type == "ovis":
                ldms_auth_option = f"conf=/{auth_secret}/{auth_secret_file}"

            cfg.append(f"auth_add name={ldmsd_name} plugin={auth_type} {ldms_auth_option}")
            ldms_host = f"nersc-ldms-aggr.{self.namespace}.svc.cluster.local"
            for k, v in self.env.items():
                if k == "stream":
                    continue
                for index, sub_list in enumerate(v['agg']):
                    ldmsd_name_i = f"{k}-{index}"
                    ldmsd_port = sub_list['LDMSD_PORT']
                    cfg.append(f"prdcr_add name=prdcr_{ldmsd_name_i} type=active interval=30000000 xprt=sock host={ldms_host} port={ldmsd_port} auth={ldmsd_name}")
        cfg.extend([
            "prdcr_start_regex regex=.*",
            "prdcr_subscribe stream=nersc regex=.*",
            "updtr_add name=stream interval=10000000 auto_interval=true  #(Honor hints if true)",
            "updtr_prdcr_add name=stream regex=prdcr.*",
            "updtr_match_add name=stream match=schema regex=(DONOTMATCH)",
            "updtr_start name=stream",
            "#Log Stream data",
            "load name=hello_sampler",
            "config name=hello_sampler producer=${HOSTNAME} instance=${HOSTNAME}/hello_sampler stream=nersc component_id=1",
            "start name=hello_sampler interval=1000000 offset=0"
        ])
        with open(out_file, 'w') as fh:
            fh.write('\n'.join(cfg))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--verbose", "-v", action="store_true", default=False, help="Turn on verbose output"
    )
    parser.add_argument(
        "--config", "-c", default="ldms_machine_config.json", help="Path to JSON config file"
    )
    args = parser.parse_args()
    config = load_config(args.config)
    verbose = args.verbose if args.verbose is not None else config.get("verbose", False)
    setup_logging(verbose)
    agg = LdmsdManager(config)
    agg.main()
