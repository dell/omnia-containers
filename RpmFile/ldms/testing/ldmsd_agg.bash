#!/bin/bash

chmod 400 ldmsauth.conf 
chmod 400 ldmsd_agg.conf
/opt/ovis-ldms/sbin/ldmsd -x sock:6003 -c ldmsd_agg.conf -a ovis -A conf=$(pwd)/ldmsauth.conf -v DEBUG
