Telemetry
==========

⦾ **When a Kubernetes worker node fails, affected telemetry services may take time to fail over to available worker nodes.**

**Resolution**: No manual intervention is required.  Wait for the telemetry services to recover and fail over automatically. Do not restart pods or nodes during this period, as it may extend recovery time.

⦾ **Telemetry Pods Enter CrashLoopBackOff After Worker Node Reboot**
 
**Potential Cause**: In Omnia deployments that use PowerScale as NFS-backed persistent
storage, telemetry pods (Kafka and iDRAC/MySQL) may enter a **CrashLoopBackOff** state
following an abrupt worker node reboot or network interruption. During normal operation,
Kafka and MySQL write lock files (``.lock``, ``.pid``, ``.sock``) to their persistent
volumes to prevent concurrent access. When a pod terminates unexpectedly, these lock files
are not released. Because PowerScale operates as an external, highly available NFSv3
server, it retains the lock state across client failures. When the pod restarts, it cannot
acquire the existing locks and fails to initialize, resulting in a crash loop.
 
**Resolution**: Manually remove the stale lock files from the affected Persistent Volume Claims (PVC) and restart
the pods. Follow the steps below based on the affected component.
 
*For Kafka pods:*
 
1. Identify the affected pods:
 
   ::
 
      kubectl get pods -n telemetry -l strimzi.io/kind=Kafka
 
2. Force delete the stuck pod:
 
   ::
 
      kubectl delete pod <kafka-pod-name> -n telemetry --force --grace-period=0
 
3. Retrieve the name of the associated PVC:
 
   ::
 
      kubectl get pod <kafka-pod-name> -n telemetry -o jsonpath='{.spec.volumes[*].persistentVolumeClaim.claimName}'
 
4. Create a temporary cleanup pod to remove stale lock files from the PVC:
 
   ::
 
      kubectl run kafka-lock-cleanup --image=busybox:1.36 -n telemetry --restart=Never \
      --overrides='{"spec":{"containers":[{"name":"cleanup","image":"busybox:1.36",\
      "command":["sh","-c","find /data -type f \\( -name .lock -o -name *.lock \
      -o -name *.sock -o -name *.pid \\) -print -delete 2>/dev/null; echo Done"],\
      "volumeMounts":[{"name":"data","mountPath":"/data"}]}],\
      "volumes":[{"name":"data","persistentVolumeClaim":{"claimName":"<pvc-name>"}}]}}'
 
5. Wait for the cleanup pod to complete:
 
   ::
 
      kubectl wait --for=condition=complete pod/kafka-lock-cleanup -n telemetry --timeout=30s
 
6. Delete the cleanup pod:
 
   ::
 
      kubectl delete pod kafka-lock-cleanup -n telemetry --force --grace-period=0
 
*For iDRAC telemetry pods (MySQL):*
 
1. Identify the affected iDRAC pods:
 
   ::
 
      kubectl get pods -n telemetry -l app=idrac-telemetry
 
2. Check the MySQL container logs to determine the type of failure:
 
   ::
 
      kubectl logs <idrac-pod-name> -n telemetry -c mysqldb --tail=50
 
3. If the logs show a lock file error (``Unable to lock ibdata1 error: 11``), force
   delete the pod, run a cleanup pod to remove stale MySQL lock files (``.sock``,
   ``.pid``, ``.lock``, ``ibdata1.lock``), and then restart the pod.
 
4. If the logs indicate MySQL InnoDB corruption (tablespace errors), delete the PVC
   to reinitialize the MySQL database. Note that this action results in data loss:
 
   ::
 
      kubectl delete pvc <pvc-name> -n telemetry --timeout=60s
 
**Note**: In the case of MySQL InnoDB corruption, deleting the lock files is not
sufficient. Manually delete the affected PVC and redeploy the telemetry service using
``telemetry.yml``. Data will be available only after ``telemetry.yml`` execution
completes successfully.