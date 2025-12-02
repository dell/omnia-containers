#!/usr/bin/env python3
"""
https://prometheus.github.io/client_python/getting-started/three-step-demo/
This should listen on a port and return metrics

One can start the exporter by doing:
./ldms_exporter_comm.py --xprt sock --hostname localhost --port 6006 --auth munge --auth_opt 'socket=/run/munge/munge.socket'  --exporter_port 8000

In the container:
source /ldms_conf/ldms-env.nersc-ldms-aggr.compute-cpu-0.sh && \
./ldms_exporter.py --xprt sock --hostname $LDMSD_HOST --port $LDMSD_PORT --auth munge --auth_opt 'socket=/run/munge/munge.socket'  --exporter_port $EXPORTER_PORT

One can read the exporter data from:
curl -sLk localhost:8000/metrics
"""

import sys
import os
import time
import logging
import json  # to convert cmd output to data structure
import re
import subprocess
import shlex
import click
from prometheus_client.core import GaugeMetricFamily, REGISTRY
from prometheus_client import start_http_server, Summary

sys.path.append('/opt/ovis-ldms/lib/python3.10/site-packages')
from ldmsd.ldmsd_communicator import Communicator

# Create a metric to track time spent and requests made.
REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')

logging.basicConfig(level=logging.INFO)


class LdmsMetrics():
    """
    Generate a data structured report
    """

    def __init__(self, hostname, xprt, port, auth, auth_opt=None):
        self.hostname = hostname
        self.port = port
        self.xprt = xprt
        self.auth = auth
        self.auth_opt = auth_opt
        self.comm = None
        self.ldms_exporter_name = os.environ.get("EXPORTER_NAME").replace('-metrics', '')
        # Type
        if 'stream' in self.ldms_exporter_name:
            self.ldmsd_type = "stream"
        elif 'store' in self.ldms_exporter_name:
            self.ldmsd_type = "store"
        elif 'agg' in self.ldms_exporter_name:
            self.ldmsd_type = "agg"
        else:
            self.ldmsd_type = "other"
        # Group
        if 'stream' in self.ldms_exporter_name:
            self.ldmsd_group = "stream"
        elif 'comp' in self.ldms_exporter_name and 'cpu' in self.ldms_exporter_name:
            self.ldmsd_group = "comp-gpu"
        elif 'comp' in self.ldms_exporter_name and 'gpu' in self.ldms_exporter_name:
            self.ldmsd_group = "comp-cpu"
        elif 'comp' in self.ldms_exporter_name:
            self.ldmsd_group = "comp"
        elif 'appl' in self.ldms_exporter_name:
            self.ldmsd_group = "appl"
        elif 'mana' in self.ldms_exporter_name:
            self.ldmsd_group = "mana"
        else:
            self.ldmsd_group = "other"

    def describe(self):
        """returns metrics in the same format as collect
        (though you don't have to include the samples).
        This is used to predetermine the names of time series a CollectorRegistry
        exposes and thus to detect collisions and duplicate registrations.
        """
        return []

    def collect(self):
        """This is called when scraped"""
        logging.info("Producing metrics...")
        # Get Report
        report = self.ldmsd_report()
        if not report:
            #raise EOFError("No data from ldmsd")
            logging.error("No data from ldmsd")

        # Convert to metrics
        for k, v in report.items():
            logging.info(f"ldmsd_group:{self.ldmsd_group}, ldmsd_type:{self.ldmsd_type}")
            logging.info(f"convert_to_metric: cmd:{k}:\n{json.dumps(v, indent=4)}")
            if k == 'ldms_ls_summary':
                if isinstance(v, list):
                    logging.info(f"FIXME******k:{k}, v:{v}")
                else:
                    logging.info(f"DEBUG******k:{k}, v:{v}")
                    for key, value in v.items():
                        if key == 'total_sets':
                            this_metric = GaugeMetricFamily(
                                f"ldmsd_metric_total_sets",
                                f"Returns for a ldmsd, count the number of samplers accross producers",
                                labels=['ldms_group', 'ldms_type', 'ldms_name']
                            )
                            this_metric.add_metric([self.ldmsd_group, self.ldmsd_type, self.ldms_exporter_name], value)
                            yield this_metric
                            continue
                        if key == 'meta_data_kb':
                            this_metric = GaugeMetricFamily(
                                f"ldmsd_metric_meta_data_kb",
                                f"Returns for a ldmsd, meta_data_kb",
                                labels=['ldms_group', 'ldms_type', 'ldms_name']
                            )
                            this_metric.add_metric([self.ldmsd_group, self.ldmsd_type, self.ldms_exporter_name], value)
                            yield this_metric
                            continue
                        if key == 'data_kb':
                            this_metric = GaugeMetricFamily(
                                f"ldmsd_metric_data_kb",
                                f"Returns for a ldmsd, data_kb",
                                labels=['ldms_group', 'ldms_type', 'ldms_name']
                            )
                            this_metric.add_metric([self.ldmsd_group, self.ldmsd_type, self.ldms_exporter_name], value)
                            yield this_metric
                            continue
                        if key == 'memory_kb':
                            this_metric = GaugeMetricFamily(
                                f"ldmsd_metric_memory_kb",
                                f"Returns for a ldmsd, memory_kb",
                                labels=['ldms_group', 'ldms_type', 'ldms_name']
                            )
                            this_metric.add_metric([self.ldmsd_group, self.ldmsd_type, self.ldms_exporter_name], value)
                            yield this_metric
                            continue
                        else:
                            this_metric = GaugeMetricFamily(
                                f"ldmsd_metric_summary_{key}",
                                f"Returns for a ldmsd, value of {key}",
                                labels=['ldms_group', 'ldms_type', 'ldms_name']
                            )
                            this_metric.add_metric([self.ldmsd_group, self.ldmsd_type, self.ldms_exporter_name], value)
                            yield this_metric
                            continue

            if k == 'ldms_ls_samplers_count':
                if isinstance(v, list):
                    logging.info(f"FIXME******k:{k}, v:{v}")
                else:
                    logging.info(f"DEBUG******k:{k}, v:{v}")
                    for sampler_type, v2 in v.items():
                        for k3, v3 in v2.items():
                            this_metric = GaugeMetricFamily(
                                f"ldmsd_metric_sampler_count".replace('-', '_'),
                                f"Returns for a ldmsd, the number of producers with with sampler {sampler_type}",
                                labels=['ldms_group', 'ldms_type', 'ldms_name', 'sampler_type']
                            )
                            this_metric.add_metric([self.ldmsd_group, self.ldmsd_type, self.ldms_exporter_name, sampler_type], v3)
                            yield this_metric


            if k == 'prdcr_stats':
                if isinstance(v, list):
                    logging.info(f"FIXME******k:{k}, v:{v}")
                else:
                    logging.info(f"DEBUG******k:{k}, v:{v}")
                    logging.info(f"prdcr_stats: {v}")
                    for key, value in v.items():
                        this_metric = GaugeMetricFamily(
                            f"ldmsd_metric_{k}_{key}".replace('-', '_'),
                            f"Returns value of {k} {key}",
                            labels=['ldms_group', 'ldms_type', 'ldms_name', 'state']
                        )
                        this_metric.add_metric([self.ldmsd_group, self.ldmsd_type, self.ldms_exporter_name, key], value)
                        yield this_metric

            if k == 'update_time_stats':
                if isinstance(v, list):
                    logging.info(f"FIXME******k:{k}, v:{v}")
                    logging.info(json.dumps(v, indent=4))
                else:
                    metrics = {}
                    for damon, v1 in v.items():
                        logging.info(f"damon:{damon}, count:{len(v1)}")
                        for node, v2 in v1.items():
                            logging.info(f"node:{node}")
                            for metric_long, v3 in v2.items():
                                # Remove node name from the sampler name
                                _, metric = metric_long.split('/')
                                logging.info(f"metric:{metric}")
                                # Set default keys
                                metrics.setdefault(metric, {'min':[], 'max':[], 'avg':[], 'cnt':[]})
                                # Pack stats into lists
                                metrics[metric]['min'].append(v3['min'])
                                metrics[metric]['max'].append(v3['max'])
                                metrics[metric]['avg'].append(v3['avg'])
                                metrics[metric]['cnt'].append(v3['cnt'])
                    # Cook metrics
                    metrics_histogram = {}
                    for stat in ['min', 'max', 'avg', 'cnt']:
                        for sampler, v in metrics.items():
                            count = len(v[stat])
                            minimum = min(v[stat])
                            maximum = max(v[stat])
                            ranges = maximum - minimum
                            step_size = ranges // 10
                            logging.info(f"stat:{stat}, sampler:{sampler}, count:{count}, minimum:{minimum}, maximum:{maximum} ranges:{ranges}, step_size:{step_size}")

            if k == 'set_stats':
                if isinstance(v, list):
                    logging.info(f"FIXME******k:{k}, v:{v}")
                else:
                    for key, value in v.items():
                        this_metric = GaugeMetricFamily(
                            f"ldmsd_metric_{k}_{key}",
                            f"Returns value of {k} {key}",
                            labels=['ldms_group', 'ldms_type', 'ldms_name']
                        )
                        this_metric.add_metric([self.ldmsd_group, self.ldmsd_type, self.ldms_exporter_name], value)
                        yield this_metric

            if k == 'thread_stats':
                thread_family = {}
                for key, value in v.items():
                    if key in ["count", "compute_time"]:
                        this_metric = GaugeMetricFamily(
                            f"ldmsd_metric_thread_stats_{key}",
                            f"Returns value of {k} {key}",
                            labels=['ldms_group', 'ldms_type', 'ldms_name']
                        )
                        this_metric.add_metric([self.ldmsd_group, self.ldmsd_type, self.ldms_exporter_name], value)
                        yield this_metric

                    # Handle the list of thread stats
                    if key == "entries":
                        for item in value:
                            thread_family.setdefault(item['name'], {})
                        logging.info(f"YES:{thread_family}")
                        for name in thread_family.keys():
                            # Aggregate thread metrics. find average
                            list_sc = [x['sample_count'] for x in value if x['name'] == name]
                            avg_sc = round(sum(list_sc) / len(list_sc))
                            list_sr = [x['sample_rate'] for x in value if x['name'] == name]
                            avg_sr = round(sum(list_sr) / len(list_sr))
                            list_util = [x['utilization'] for x in value if x['name'] == name]
                            avg_util = round(sum(list_util) / len(list_util))
                            list_sq_sz = [x['sq_sz'] for x in value if x['name'] == name]
                            avg_sq_sz = round(sum(list_sq_sz) / len(list_sq_sz))
                            list_n_eps = [x['n_eps'] for x in value if x['name'] == name]
                            avg_n_eps = round(sum(list_n_eps) / len(list_sq_sz))
                            thread_family[name]['sample_count_avg'] = avg_sc
                            thread_family[name]['sample_rate_avg'] = avg_sr
                            thread_family[name]['utilization_avg'] = avg_util
                            thread_family[name]['sq_sz_avg'] = avg_sq_sz
                            thread_family[name]['n_eps_avg'] = avg_n_eps
                        logging.info(f"thread_family: {thread_family}")
                        # Handle the list of thread stats
                        for thread_type, values in thread_family.items():
                            logging.info(f"thread:{thread_type}, values:{values}")
                            for metric, v in values.items():
                                this_metric = GaugeMetricFamily(
                                    f"ldmsd_metric_thread_stats_{metric}_{thread_type}".replace('-', '_'),
                                    f"Returns value of thread_stats {metric} for {thread_type}".replace('-', '_'),
                                    labels=['ldms_group', 'ldms_type', 'ldms_name']
                                )
                                this_metric.add_metric([self.ldmsd_group, self.ldms_exporter_name, self.ldmsd_type], v)
                                yield this_metric

            if k == 'updtr_status':
                # v is a list of dict
                for updtr in v:
                    # count things in each state
                    updtr_name = updtr['name'].replace('-', '_')
                    updtr_states = {
                        "RUNNING" : 0,
                        "STARTED" : 1,
                        "STOPPED" : 2,
                        "ERROR" : 3
                    }
                    # Count things in each state
                    producers_states = {
                        "CONNECTED" : 0,
                        "CONNECTING" : 0,
                        "DISCONNECTED" : 0,
                        "STOPPED": 0,
                        "STOPPING": 0
                    }
                    # Count producers in each state
                    for producer in updtr["producers"]:
                        producers_states[producer["state"]] += 1
                    logging.info(f"updtr_status: producers in each state:: {producers_states}")
                    for state, state_count in producers_states.items():
                        state_lower = state.lower()
                        this_metric = GaugeMetricFamily(
                            f"ldmsd_metric_producer_state_count",
                            f"Returns number of produers in each state",
                            labels=['ldms_group', 'ldms_type', 'ldms_name', 'state']
                        )
                        this_metric.add_metric([self.ldmsd_group, self.ldmsd_type, self.ldms_exporter_name, state_lower], state_count)
                        yield this_metric
                    # metric: state, convert string to int
                    this_metric = GaugeMetricFamily(
                        f"ldmsd_metric_ldmsd_state",
                        f"Returns ldmsd running state. {updtr_states}",
                        labels=['ldms_group', 'ldms_type', 'ldms_name']
                    )
                    this_metric.add_metric([self.ldmsd_group, self.ldmsd_type], self.ldms_exporter_name, updtr_states[updtr["state"]])
                    yield this_metric
                    # metric: outstanding count
                    this_metric = GaugeMetricFamily(
                        f"ldmsd_metric_outstanding_count",
                        f"Returns for ldmsd, number of outstanding sampler metrics",
                        labels=['ldms_group', 'ldms_type', 'ldms_name']
                    )
                    this_metric.add_metric([self.ldmsd_group, self.ldmsd_type, self.ldms_exporter_name], updtr["outstanding count"])
                    yield this_metric
                    # metric: oversampled count
                    this_metric = GaugeMetricFamily(
                        f"ldmsd_metric_oversampled_count",
                        f"Returns for ldmsd, the number of oversampled sampler metrics",
                        labels=['ldms_group', 'ldms_type', 'ldms_name']
                    )
                    this_metric.add_metric([self.ldmsd_group, self.ldmsd_type, self.ldms_exporter_name], updtr["oversampled count"])
                    yield this_metric


    def comm_connect(self):
        """Open connection to ldmsd
        return: comm object
        """
        # Convert auth_opt to dict
        auth_opt_obj = {}
        logging.debug(f"auth_opt:{self.auth_opt}")
        r = re.compile(r"(\w+)=(.+)")
        m = r.match(self.auth_opt)
        if m is None:
            raise TypeError('Expecting --auth-arg to be NAME=VALUE')
        (k, v) = m.groups()
        auth_opt_obj[k] = v
        # Trying to connect until ldmsd responds
        rc = -1
        while rc != 0:
            logging.info("Connecting")
            comm = Communicator(
                self.xprt,
                self.hostname,
                self.port,
                self.auth,
                auth_opt_obj,
                recv_timeout=None
            )
            rc = comm.connect()
            if rc:
                logging.error(f"Error connecting!!!: {rc}")
                time.sleep(30)
            else:
                logging.info("Connected")
                # for possible race condition
                time.sleep(2)
            return comm

    def ldmsd_report(self):
        """Collect ldmsd stats
        Open connection to ldmsd, get info, and quit
        return: dict object with command output as dict
        """
        report = {}
        shell_cmds = {
            "ldms_ls" :  f"/opt/ovis-ldms/sbin/ldms_ls -a {self.auth} -A {self.auth_opt} -x sock -h {self.hostname} -p {self.port} -v"
        }
        for cmd_alias, cmd_line in shell_cmds.items():
            logging.info(f"Run: {cmd_line}")
            report.update(self.get_metric_from_shell_cmd(cmd_line))

        cmds = [
            #"updtr_status",        # OK  - Gives producers state, outstanding count, and oversampled count
            #"update_time_stats",  # BAD, not ldms_ls
            "prdcr_stats",         # OK
            #"thread_stats",        # OK
            #"set_stats"            # OK
        ]
        for i in cmds:
            # Run command, convert String to objects
            response = self.run_cmd(i)
            if response:
                report[i.replace(" ", "_")] = response
        return report

    def run_cmd(self, cmd: str):
        """Run and exit command
        The Communicator method call returns a tuple (error_code, cmd_output)
        If rc != 0, cmd failed
        :return: dict object from cmd output
        """
        comm = self.comm_connect()
        func = getattr(comm, cmd)
        rc, output = func()
        logging.debug(f"run_cmd:{cmd}, rc:{rc}, output:{output}")
        #if rc:
        #    logging.error(f"ERROR: rc:{rc}, output:{output}")
        response = {}
        if rc:
            logging.error(f"ERROR: rc:{rc}, output:{output}")
        else:
            response = json.loads(output)
        # Hang up
        logging.info("Disconnecting")
        comm.close()
        return response

    def get_metric_from_shell_cmd(self, cmd_line):
        """
        run shell command and parse output,
        returning structured report
        """
        report = {}
        response = run_shell_cmd(cmd_line)
        if response:
            logging.info(f"type of response:{type(response.stdout)}")
            # Aggregate Sampler data
            summary = {}
            # Aggregate Sampler data
            samplers = {}
            # Match: Total Sets: 468, Meta Data (kB): 1431.86, Data (kB) 1913.23, Memory (kB): 3345.09
            re_pat_summary = (
                r'^'
                r'Total Sets:\W+(?P<total_sets>\d+),\W+'
                r'Meta Data \(kB\):\W+(?P<meta_data_kb>\d+(\.\d+)?),\W+'
                r'Data \(kB\)\W+(?P<data_kb>\d+(\.\d+)?),\W+'
                r'Memory \(kB\):\W+(?P<memory_kb>\d+(\.\d+)?)'
            )
            req_pat_summary = re.compile(re_pat_summary)
            #        Schema         Instance                 Flags  Msize  Dsize  Hsize  UID    GID    Perm       Update            Duration          Info
            # Match: dcgm           login01/gpu_0               CR    3896    624      0      0      0 -r--r----- 1743264900.002940          0.000886 "updt_hint_us"="10000000:100000"
            re_pat_sampler = (
                r'^'
                r'(?P<sampler_name>\w+)\W+'
                #r'(?P<instance>(\w+/\w+))\W+'
                #r'(?P<flags>\w+)\W+'
                #r'(?P<msize>\d+)\W+'
                #r'(?P<dsize>\d+)\W+'
                #r'(?P<hsize>\d+)\W+'
                #r'(?P<uid>\d+)\W+'
                #r'(?P<gid>\d+)\W+'
            )
            req_pat_sampler = re.compile(re_pat_sampler)
            for line in response.stdout.split("\n"):
                #logging.info(f"LINE:{line}")
                # Get summary metrics
                if 'Total Sets' in line:
                    found = req_pat_summary.finditer(line)
                    for m in found:
                        summary = {
                            'total_sets':   m['total_sets'],
                            'meta_data_kb': m['meta_data_kb'],
                            'data_kb':      m['data_kb'],
                            'memory_kb':    m['memory_kb'],
                            #'update':       m['update']
                        }
                        logging.info(f"report:{report}")
                # Skip the junk
                substrings = ['Total', 'Schema', '---------']
                if any(substring in line for substring in substrings):
                    logging.info(f"skip line:{line}")
                    continue
                # Count samplers as aggregate
                found = req_pat_sampler.finditer(line)
                for m in found:
                    logging.info(f"sampler_name:{m['sampler_name']}")
                    #samplers.setdefault(m['sampler_name'], {'count':0, 'msize':0, 'dsize':0, 'hsize':0})
                    samplers.setdefault(m['sampler_name'], {'count':0})
                    samplers[m['sampler_name']]['count'] += 1
                    #samplers[m['sampler_name']]['msize'] += int(m['msize'])
                    #samplers[m['sampler_name']]['dsize'] += int(m['dsize'])
                    #samplers[m['sampler_name']]['hsize'] += int(m['hsize'])
            report = {
                'ldms_ls_summary' : summary,
                'ldms_ls_samplers_count' : samplers
            }
            logging.info(f"report:{report}")
        return report

def run_shell_cmd(cmd: str, timeout=None, shell=False):
    """Run and exit command
    :param cmd: str command line to run
    :param timeout: seconds to wait for return
    :param shell: Bool to run in subshell
    :return: str output
    """
    logging.info(cmd)
    try:
        output = subprocess.run(
            shlex.split(cmd),
            shell,
            timeout=timeout,
            check=True,
            universal_newlines=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as c:
        logging.critical(f"ERROR: Returncode: {c.returncode}")
        logging.critical(f"ERROR: stderr :{c.stderr}")
        raise c
    return output


@click.command()
@click.option('--xprt', help='ldmsd xprt [sock]', type=click.STRING, required=True)
@click.option('--hostname', help='ldmsd hostname', type=click.STRING, required=True)
@click.option('--port', help='ldmsd listening port', type=click.INT, required=True)
@click.option('--auth', help='ldmsd auth [munge|ovis]', type=click.STRING, required=True)
@click.option('--auth_opt', help='ldmsd auth_opt [socket=<path>|conf=<path>]', type=click.STRING, required=True)
@click.option('--exporter_port', help='prometheus scrape port', type=click.INT, required=True)
def main(xprt: str, hostname: str, port: int, auth: str, auth_opt: str, exporter_port: int):  # pylint: disable=too-many-arguments
    """Start the LDMS Exporter
    :param xprt: how we connect [sock]
    :param hostname: hostname serving ldmsd
    :param port: ldmsd listening port
    :param auth: ldmsd authentication [munge|ovis]
    :param auth_opt: authenticaiton arguments [socket=<path>|conf=<path>]'
    :param exporter_port: prometheus scrape port
    """
    r = re.compile(r"(\w+)=(.+)")
    m = r.match(auth_opt)

    if m is None:
        raise TypeError('Expecting --auth-arg to be NAME=VALUE')

    # Print args
    logging.info(
        "\nConnecting to ldmsd:\n"
        f"xprt          : {xprt}\n"
        f"hostname      : {hostname}\n"
        f"port          : {port}\n"
        f"auth          : {auth}\n"
        f"auth_opt      : {auth_opt}\n"
        f"exporter_port : {exporter_port}"
    )
    # Start up the server to expose the metrics.
    start_http_server(exporter_port)
    # Remove all the internal python metrics
    for coll in list(REGISTRY._collector_to_names.keys()):  # pylint: disable=protected-access
        REGISTRY.unregister(coll)
    # Wait for requests
    REGISTRY.register(
        LdmsMetrics(
            hostname=hostname,
            port=port,
            xprt=xprt,
            auth=auth,
            auth_opt=auth_opt
        )
    )
    while True:
        time.sleep(60)


if __name__ == '__main__':
    main()
