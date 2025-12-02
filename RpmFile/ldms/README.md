*** Copyright Notice ***

NERSC_Lightweight Distributed Metric Service (NERSC_LDMS) Copyright (c) 2025, The Regents of the University of California, through Lawrence Berkeley National Laboratory (subject to receipt of any required approvals from the U.S. Dept. of Energy). All rights reserved.

If you have questions about your rights to use or distribute this software,
please contact Berkeley Lab's Intellectual Property Office at
IPO@lbl.gov.

NOTICE.  This Software was developed under funding from the U.S. Department
of Energy and the U.S. Government consequently retains certain rights.  As
such, the U.S. Government has been granted for itself and others acting on
its behalf a paid-up, nonexclusive, irrevocable, worldwide license in the
Software to reproduce, distribute copies to the public, prepare derivative 
works, and perform publicly and display publicly, and to permit others to do so.

Overview
---

This repository contains material for working with ldms.

Contents
---

* ansible   -> Create ldms config file during a node boot
* build     -> Create ldms package (rpm, pkg) from exiting repo clone.
* chart     -> Loftsman/Helm Chart for deploying ldms in kubernetes, and guide to strimzi kafka setup
* dashboard -> Grafana Dashboard for ldms pipeline observability
* oci       -> build ldms container used in the chart
* testing   -> simple sample scripts for using ldms
* LICENSE   -> Modified BSD license
* README.md -> This file

Pipeline
---

![Pipeline Diagram](images/ldms_pipline.svg)

Steps
---

Build ldms package for the nodes (Producers)

```console
#
# Change to build dir
#
cd build

#
# Start the Ubuntu build container
#
./start_build_container.ubuntu.bash

#
# Inside the container, build the LDMS package
#
pushd /builds/ovis/ && ../scripts/build_ldms.ubuntu.bash

#
# The build prodcut (ovis-ldms-<YOUR_VERSION>.deb) will be in the root of the ovis source dir.
#
# On each producer node, install the package and start the LDMS sampler service:
#
dpkg -i ovis-ldms-<YOUR_VERSION>.deb
systemctl enable nersc-ldmsd.sampler.service
systemctl daemon-reload
systemctl start nersc-ldmsd.sampler.service
systemctl is-active nersc-ldmsd.sampler.service

#
# Verify the LDMS service is running:
#
/opt/ovis-ldms/sbin/ldms_ls -a ovis -A conf=/opt/ovis-ldms/etc/ldms/ldmsauth.conf -p 6002 -h localhost
```

Setup Aggregator image and helm chart

```console
#
# Build the OCI Image for the LDMS Aggregator, and push to registry used by k8s
#
pushd oci
./build.bash

#
# Setup Helm chart (node_map, ldms confg files, bundle in k8s ConfigMaps)
#
pushd ../chart/nersc-ldms-aggr/
cp ldms_machine_config.dell.json default_config.json
make clean
make

#
# Test Chart template
#
helm template --debug --values values.yaml nersc-ldms-aggr

#
# Install Chart
#
helm install -n telem nersc-ldms-aggr nersc-ldms-aggr --values values.yaml

#
# Verify
#
./health_check.bash

#
# Setup kafka, as ldms will publish to the kafka topic
#
setup_strimzi_kafka.bash

#
# Watch kafka for data
#
kubectl -n telem exec -it cluster-controller-0 -- bin/kafka-console-consumer.sh --bootstrap-server cluster-kafka-bootstrap:9092 --topic nersc-ldms
```
