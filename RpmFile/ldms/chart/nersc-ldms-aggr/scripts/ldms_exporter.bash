#!/bin/sh

#python3 /app/nersc_ldms_aggr/ldms_exporter.py --xprt sock --hostname ${LDMSD_HOST} --port ${LDMSD_PORT} --auth munge --auth_opt 'socket=/run/munge/munge.socket' --exporter_port ${EXPORTER_PORT}
python3 /ldms_bin/ldms_exporter.py --xprt sock --hostname ${LDMSD_HOST} --port ${LDMSD_PORT} --auth ${LDMSD_AUTH_PLUGIN} --auth_opt ${LDMSD_AUTH_OPTION} --exporter_port ${EXPORTER_PORT}
