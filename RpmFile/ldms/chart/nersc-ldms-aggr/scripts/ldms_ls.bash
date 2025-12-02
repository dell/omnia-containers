#!/bin/sh

OUTPUT="$(/opt/ovis-ldms/sbin/ldms_ls -a ${LDMSD_AUTH_PLUGIN} -A ${LDMSD_AUTH_OPTION} -x sock -h ${LDMSD_HOST} -p ${LDMSD_PORT} -v)"
# to make this: {"Summary":[{"TotalSets":"12859"},{"MetaData_kB":"27756.42"},{"Data_kB":"4178.67"},{"Memory_kB":"31935.10"}]}
echo "$OUTPUT" |grep Tot | sed -e 's|(kB)|_kB|g' -e 's/: /=/g' -e 's/kB /kB=/g' -e 's/ //g' |jq -rc --raw-input 'split(",") | map(split("=") | { (.[0]): .[1] })|{"Summary":.}'
# to make this: {"cray_dvs":27,"cray_iostat":558,"cray_vmstat":4121,"dcgm":6174,"ldmsd_grp_schema":48}
echo "$OUTPUT" |awk '{print $1}' |egrep -v 'Total|Schema|^$|---' |sort |uniq -c |awk '{print "\""$2"\"" ":" $1}' |paste -s -d',' | awk '{print "{" $1 "}"}' | jq -cC
