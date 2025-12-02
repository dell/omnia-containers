#!/bin/bash

chmod 400 ldmsauth.conf 
chmod 400 ldmsd_agg.conf
/opt/ovis-ldms/sbin/ldmsd -x sock:6002 -c ldmsd_producer.conf -a ovis -A conf=$(pwd)/ldmsauth.conf -v DEBUG
