#!/bin/sh

LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib/libserdes.so /opt/ovis-ldms/sbin/ldmsd -F -c ${LDMSD_CONF} -m 128M -a ${LDMSD_AUTH_PLUGIN} -A ${LDMSD_AUTH_OPTION} -x sock:${LDMSD_PORT} -P 4 -v INFO

HOST="${LDMSD_HOST}"
PORT="${LDMSD_PORT}"
AUTH="${LDMSD_AUTH_PLUGIN}"
AUTH_ARG=""
NOW="$(date +"%Y%m%d-%H%M%S")"
echo "=====================
DATE:$NOW
SCRIPT:$0
LDMSD_HOST:$LDMSD_HOST
LDMSD_PORT:$LDMSD_PORT
LDMSD_AUTH_PLUGIN:$LDMSD_AUTH_PLUGIN
LDMSD_AUTH_OPTION:$LDMSD_AUTH_OPTION
====================="
echo "
======================
daemon_status:
======================
"
/opt/ovis-ldms/bin/ldmsd_controller -a ${LDMSD_AUTH_PLUGIN} -A ${LDMSD_AUTH_OPTION} -x sock -h ${LDMSD_HOST} -p ${LDMSD_PORT} --cmd daemon_status
echo "
======================
updtr_status summary:
======================
"
/opt/ovis-ldms/bin/ldmsd_controller -a ${LDMSD_AUTH_PLUGIN} -A ${LDMSD_AUTH_OPTION} -x sock -h ${LDMSD_HOST} -p ${LDMSD_PORT} --cmd "updtr_status summary"
echo "
===================
prdcr_stats:
===================
"
/opt/ovis-ldms/bin/ldmsd_controller -a ${LDMSD_AUTH_PLUGIN} -A ${LDMSD_AUTH_OPTION} -x sock -h ${LDMSD_HOST} -p ${LDMSD_PORT} --cmd prdcr_stats
echo "
===================
strgp_status:
===================
"
/opt/ovis-ldms/bin/ldmsd_controller -a ${LDMSD_AUTH_PLUGIN} -A ${LDMSD_AUTH_OPTION} -x sock -h ${LDMSD_HOST} -p ${LDMSD_PORT} --cmd strgp_status
echo "
===================
stream_status:
===================
"
/opt/ovis-ldms/bin/ldmsd_controller -a ${LDMSD_AUTH_PLUGIN} -A ${LDMSD_AUTH_OPTION} -x sock -h ${LDMSD_HOST} -p ${LDMSD_PORT} --cmd stream_status
echo "
===================
update_time_stats:
===================
"
/opt/ovis-ldms/bin/ldmsd_controller -a ${LDMSD_AUTH_PLUGIN} -A ${LDMSD_AUTH_OPTION} -x sock -h ${LDMSD_HOST} -p ${LDMSD_PORT} --cmd update_time_stats
echo "
===================
thread_stats:
===================
"
/opt/ovis-ldms/bin/ldmsd_controller -a ${LDMSD_AUTH_PLUGIN} -A ${LDMSD_AUTH_OPTION} -x sock -h ${LDMSD_HOST} -p ${LDMSD_PORT} --cmd "thread_stats"
echo "
===================
set_stats: (Units: Bytes/sec)
===================
"
/opt/ovis-ldms/bin/ldmsd_controller -a ${LDMSD_AUTH_PLUGIN} -A ${LDMSD_AUTH_OPTION} -x sock -h ${LDMSD_HOST} -p ${LDMSD_PORT} --cmd "set_stats"
