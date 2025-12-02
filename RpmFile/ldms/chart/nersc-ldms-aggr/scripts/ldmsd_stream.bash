#!/bin/sh
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib/libserdes.so /opt/ovis-ldms/sbin/ldmsd -F -c ${LDMSD_CONF} -m 128M -a ${LDMSD_AUTH_PLUGIN} -A ${LDMSD_AUTH_OPTION} -x sock:${LDMSD_PORT} -P 4 -v INFO
