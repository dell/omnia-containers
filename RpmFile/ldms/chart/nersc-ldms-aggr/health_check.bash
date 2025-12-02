#!/bin/bash
echo "LDMS HEALTH CHECK"

function pause {
  echo "press enter to continue"
  read foo
}
NAMESPACE="telem"
echo "===================================
[>>] TEST: Check PODS: kubectl -n $NAMESPACE get pods |grep nersc |sort -n "
pause
kubectl -n $NAMESPACE get pods |grep nersc |sort -n

echo "===================================
[>>] TEST: Check Running: kubectl -n $NAMESPACE top pods --containers |grep nersc |sort -n"
pause
kubectl -n $NAMESPACE top pods --containers |grep nersc |sort -n

echo "===================================
[>>] TEST: ldmsd metrics: /ldms_bin/ldms_ls.bash"
pause

# Get one pod
POD="$(kubectl -n sma get pods -l "app=nersc-ldms-store" |grep -v NAME |head -1 |awk '{print $1}')"

# Check ldmsd all the pods from that pod
kubectl -n $NAMESPACE exec -it $POD -c store -- /bin/bash -c 'for i in $(ls /ldms_conf/ldms-env*); do echo "## $i"; source $i && /ldms_bin/ldms_ls.bash ; done'

echo "===================================
[>>] TEST: ldmsd metrics: update_time_stats"

pause
echo "Updater         Min(usec)       Max(usec)       Average(usec)   Count
--------------- --------------- --------------- --------------- ----------"
kubectl -n $NAMESPACE exec -it $POD -c store -- /bin/bash -c 'export PYTHONPATH=/app:/opt/ovis-ldms/lib/python3.10/site-packages; for i in $(ls /ldms_conf/ldms-env*); do echo "## $i"; source $i && /opt/ovis-ldms/bin/ldmsd_controller -a $LDMSD_AUTH_PLUGIN -A $LDMSD_AUTH_OPTION -x sock -h $LDMSD_HOST -p $LDMSD_PORT --cmd "update_time_stats" |egrep -v "Updater|----|division by zero"|awk '"'{print \$3}'"'; done'

echo "===================================
[--] TEST: Metric Exporter: Local: curl localhost from the container
"
kubectl -n $NAMESPACE exec -it nersc-ldms-exporter-0 -- /bin/bash -c 'source /ldms_conf/expo-env.${MY_POD_NAME}.sh; curl -sLk localhost:9101/metrics|grep HELP'

echo "[--] TEST: Metric Exporter: Service: curl nersc-ldms-exporter-0.nersc-ldms-exporter.sma.svc.cluster.local:9101"

kubectl -n $NAMESPACE exec -it nersc-ldms-exporter-0 -- /bin/bash -c "curl -sLk nersc-ldms-exporter-6.nersc-ldms-exporter.sma.svc.cluster.local:9101 |grep HELP"

echo "[--] TEST: The Service should point to this endpoint Container"

kubectl -n $NAMESPACE get endpoints nersc-ldms-exporter -o json |jq -rc '.subsets[0].addresses[]|.hostname'

echo "[--] TEST: We need a ServiceMonitor pointing to the Service" 

kubectl -n $NAMESPACE get servicemonitor nersc-ldms-exporter --show-labels

echo "[--] TEST: Check vmagent logs for scraping errors. Site dependent configuraiton"
