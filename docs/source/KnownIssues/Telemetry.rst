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
 
**Resolution**: Follow the steps below based on the type of failure:
- **Lock Issue**: Manually remove the stale lock files from the affected Persistent Volume Claims (PVC) and restart the pods.
- **File Corruption Issue**: Delete the affected PVCs and redeploy the telemetry services.
 
*For Kafka pods:*
 
1. Identify the affected pods:
 
   ::
 
      kubectl get pods -n telemetry -l strimzi.io/kind=Kafka

..image:: ../../images/2253_get_pods.png
 
2. Force delete the stuck pod:
 
   ::
 
      kubectl delete pod <kafka-pod-name> -n telemetry --force --grace-period=0
 
    
..image:: ../../images/2253_delete_pod.png
 
3. Retrieve the name of the associated PVC:
 
   ::
 
      kubectl get pod <kafka-pod-name> -n telemetry -o jsonpath='{.spec.volumes[*].persistentVolumeClaim.claimName}'
 
.. image:: ../../images/2253_retrieve_name.png
 
 4. Create a temporary cleanup pod to remove stale lock files from the PVC:
 
   ::
 
     kubectl run kafka-lock-cleanup --image=busybox:1.36 -n telemetry --restart=Never --overrides='{"spec":{"containers":[{"name":"cleanup","image":"busybox:1.36","command":["sh","-c","find /data -type f \\( -name .lock -o -name *.lock -o -name *.sock -o -name *.pid \\) -print -delete 2>/dev/null; echo Done"],"volumeMounts":[{"name":"data","mountPath":"/data"}]}],"volumes":[{"name":"data","persistentVolumeClaim":{"claimName":"<pvc-name>"}}]}}'
 
5. Wait for the cleanup pod to complete:
 
   ::
 
      kubectl wait --for=condition=complete pod/kafka-lock-cleanup -n telemetry --timeout=30s

..image:: ../../images/2253_cleanup_complete.png
 
6. Delete the cleanup pod:
 
   ::
 
      kubectl delete pod kafka-lock-cleanup -n telemetry
 
*For iDRAC telemetry pods (MySQL) - Lock Issue:*
 
1. Identify the affected iDRAC pods:
 
   ::
 
      kubectl get pods -n telemetry -l app=idrac-telemetry

..image:: ../../images/2253_get_pods_idrac.png
 
2. Check the MySQL container logs to confirm lock-related failure:
 
   ::
 
      kubectl logs <idrac-pod-name> -n telemetry -c mysqldb --tail=50

..image:: ../../images/2253_logs_idrac.png
 
3. Get the PVC name:
 
   ::
 
      kubectl get pod <idrac-pod-name> -n telemetry -o jsonpath='{.spec.volumes[*].persistentVolumeClaim.claimName}'

..image:: ../../images/2253_get_pvc_name_idrac.png

4. Force delete all iDRAC telemetry pods:
 
   ::
 
      kubectl delete pod -n telemetry -l app=idrac-telemetry --force --grace-period=0
 
..image:: ../../images/2253_delete_pod_idrac.png

5. Run cleanup script to remove stale MySQL lock files. Replace `<PVC-NAME>` with the PVC name obtained in step 3.
 
   ::
 
    kubectl run mysql-lock-cleanup --image=busybox:1.36 -n telemetry --restart=Never --overrides='
    {
    "spec": {
        "containers": [{
        "name": "cleanup",
        "image": "busybox:1.36",
        "command": ["sh", "-c", "find /data -type f \\( -name .sock -o -name *.pid -o -name *.lock -o -name ibdata1.lock \\) -print -delete 2>/dev/null; echo Done"],
        "volumeMounts": [{"name": "data", "mountPath": "/data"}]
        }],
        "volumes": [{"name": "data", "persistentVolumeClaim": {"claimName": "<PVC-NAME>"}}]
    }
    }'

    .. image:: ../../images/2253_remove_lock_files.png
    
6. Delete cleanup pod once complete:
 
   ::
 
      kubectl delete pod mysql-lock-cleanup -n telemetry

      ..image:: ../../images/2253_delete_cleanup_pod.png

*For iDRAC telemetry pods (MySQL) - File Corruption Issue:*

If the MySQL logs show an error message indicating "trying to read with page id" or similar data corruption errors, follow these steps:
 
..image:: ../../images/2253_data_corruption.png
 
1. Identify the affected iDRAC pod:
 
   ::
 
      kubectl get pods -n telemetry -l app=idrac-telemetry

..image:: ../../images/2253_get_pods_idrac.png
 
2. Check the MySQL container logs to confirm data corruption:
 
   ::
 
      kubectl logs <idrac-pod-name> -n telemetry -c mysqldb --tail=50

..image:: ../../images/2253_logs_idrac.png
 
3. Get the PVC name for the affected iDRAC pod:
 
   ::
 
      kubectl get pvc -n telemetry -l app=idrac-telemetry

..image:: ../../images/2253_get_pvc_name_idrac_corruption.png

4. Delete all PVC. The following command will delete all PVCs with the label `app=idrac-telemetry` in the `telemetry` namespace:
 
   ::
 
      kubectl delete pvc -n telemetry -l app=idrac-telemetry

..image:: ../../images/2253_delete_pvc_idrac_corruption.png

5. Delete all iDRAC telemetry pods again:
 
    ::
 
        kubectl delete pod -n telemetry -l app=idrac-telemetry --force --grace-period=0
 
    ..image:: ../../images/2253_delete_pod_idrac_corruption.png

6. Execute ``telemetry.yml`` with same inputs as previous deployment.

⦾ **Telemetry Pods Enter CrashLoopBackOff After Worker Node Reboot - Script-Based Resolution**

**Potential Cause**: In Omnia deployments that use PowerScale as NFS-backed persistent
storage, telemetry pods (Kafka and iDRAC/MySQL) may enter a **CrashLoopBackOff** state
following an abrupt worker node reboot or network interruption. During normal operation,
Kafka and MySQL write lock files (``.lock``, ``.pid``, ``.sock``) to their persistent
volumes to prevent concurrent access. When a pod terminates unexpectedly, these lock files
are not released. Because PowerScale operates as an external, highly available NFSv3
server, it retains the lock state across client failures. When the pod restarts, it cannot
acquire the existing locks and fails to initialize, resulting in a crash loop.

**Resolution**: Use the following scripts to automate lock cleanup and data corruption recovery. These scripts check for the type of failure and apply the appropriate resolution automatically.

**Kafka Lock Cleanup Script**

Save the following script as ``kafka_lock_cleanup.sh``:

.. code-block:: bash

   #!/bin/bash

   set -euo pipefail

   NAMESPACE="telemetry"

   echo "=== Kafka Lock Cleanup ==="

   # Step 1: Get PVC names before deleting pods

   echo "[1] Collecting PVC names..."

   PVCS=$(kubectl get pods -n "$NAMESPACE" -l strimzi.io/kind=Kafka \
     -o jsonpath='{.items[*].spec.volumes[*].persistentVolumeClaim.claimName}')

   echo "PVCs found: $PVCS"

   # Step 2: Force delete all Kafka pods

   echo "[2] Force deleting Kafka pods..."

   kubectl delete pod -n "$NAMESPACE" -l strimzi.io/kind=Kafka --force --grace-period=0

   # Step 3: Clean lock files from each PVC

   for PVC in $PVCS; do

     echo "[3] Cleaning lock files from PVC: $PVC"

     kubectl run kafka-lock-cleanup --image=busybox:1.36 -n "$NAMESPACE" --restart=Never --overrides="

   {

     \"spec\": {

       \"containers\": [{

         \"name\": \"cleanup\",

         \"image\": \"busybox:1.36\",

         \"command\": [\"sh\", \"-c\", \"find /data -type f \\\\( -name '*.lock' -o -name '*.sock' -o -name '*.pid' \\\\) -print -delete; echo Done\"],

         \"volumeMounts\": [{\"name\": \"data\", \"mountPath\": \"/data\"}]

       }],

       \"volumes\": [{\"name\": \"data\", \"persistentVolumeClaim\": {\"claimName\": \"$PVC\"}}]

     }

   }"

     # Step 4: Wait for completion

     echo "[4] Waiting for cleanup pod..."

     kubectl wait --for=condition=completed pod/kafka-lock-cleanup -n "$NAMESPACE" --timeout=120s

     kubectl logs kafka-lock-cleanup -n "$NAMESPACE"

     kubectl delete pod kafka-lock-cleanup -n "$NAMESPACE"

   done

   echo "[5] Verify: kubectl get pods -n $NAMESPACE -l strimzi.io/kind=Kafka"

**iDRAC Lock Cleanup Script**

Save the following script as ``idrac_lock_cleanup.sh``:

.. code-block:: bash

   #!/bin/bash

   set -euo pipefail

   NAMESPACE="telemetry"

   echo "=== iDRAC Lock Cleanup ==="

   # Step 1: Check for corruption — abort if found

   echo "[1] Checking logs for data corruption..."

   for POD in $(kubectl get pods -n "$NAMESPACE" -l app=idrac-telemetry -o jsonpath='{.items[*].metadata.name}'); do

     LOGS=$(kubectl logs "$POD" -n "$NAMESPACE" --tail=50 2>/dev/null || echo "")

     # Check for ALL corruption indicators from screenshot

     if echo "$LOGS" | grep -qiE "trying to read page|corruption in the InnoDB tablespace|innodb_force_recovery"; then

       echo ""

       echo "============================================================"

       echo "ERROR: Data corruption detected in pod: $POD"

       echo ""

       echo "Errors found:"

       echo "$LOGS" | grep -iE "trying to read page|Unable to lock mysql.ibd|corruption|Assertion failure|innodb_force_recovery|Unable to read page" | head -5

       echo ""

       echo "Lock cleanup will NOT fix this issue."

       echo "Run: ./idrac_data_corruption_recovery.sh"

       echo "============================================================"

       exit 1

     fi

   done

   echo "No corruption detected. Proceeding with lock cleanup..."

   # Step 2: Get PVC names

   echo "[2] Collecting PVC names..."

   PVCS=$(kubectl get pods -n "$NAMESPACE" -l app=idrac-telemetry \

     -o jsonpath='{.items[*].spec.volumes[*].persistentVolumeClaim.claimName}')

   echo "PVCs found: $PVCS"

   # Step 3: Force delete all iDRAC pods

   echo "[3] Force deleting iDRAC pods..."

   kubectl delete pod -n "$NAMESPACE" -l app=idrac-telemetry --force --grace-period=0

   # Step 4: Clean lock files from each PVC

   for PVC in $PVCS; do

     echo "[4] Cleaning lock files from PVC: $PVC"

     kubectl run mysql-lock-cleanup --image=busybox:1.36 -n "$NAMESPACE" --restart=Never --overrides="

   {

     \"spec\": {

       \"containers\": [{

         \"name\": \"cleanup\",

         \"image\": \"busybox:1.36\",

         \"command\": [\"sh\", \"-c\", \"find /data -type f \\\\( -name '*.sock' -o -name '*.pid' -o -name '*.lock' -o -name 'ibdata1.lock' \\\\) -print -delete; echo Done\"],

         \"volumeMounts\": [{\"name\": \"data\", \"mountPath\": \"/data\"}]

       }],

       \"volumes\": [{\"name\": \"data\", \"persistentVolumeClaim\": {\"claimName\": \"$PVC\"}}]

     }

   }"

     echo "[5] Waiting for cleanup pod..."

     kubectl wait --for=condition=completed pod/mysql-lock-cleanup -n "$NAMESPACE" --timeout=120s

     kubectl logs mysql-lock-cleanup -n "$NAMESPACE"

     kubectl delete pod mysql-lock-cleanup -n "$NAMESPACE"

   done

   echo "[6] Verify: kubectl get pods -n $NAMESPACE -l app=idrac-telemetry"

**iDRAC Data Corruption Recovery Script**

Save the following script as ``idrac_data_corruption_recovery.sh``:

.. code-block:: bash

   #!/bin/bash

   set -euo pipefail

   NAMESPACE="telemetry"

   echo "=== iDRAC Data Corruption Recovery ==="

   echo "WARNING: This will DELETE all iDRAC PVCs and wipe stored data."

   read -rp "Type DELETE to confirm: " CONFIRM

   [[ "$CONFIRM" != "DELETE" ]] && echo "Aborted." && exit 0

   # Step 1: List PVCs

   echo "[1] Current iDRAC PVCs:"

   kubectl get pvc -n "$NAMESPACE" -l app=idrac-telemetry

   # Step 2: Delete all PVCs

   echo "[2] Deleting iDRAC PVCs..."

   kubectl delete pvc -n "$NAMESPACE" -l app=idrac-telemetry

   # Step 3: Force delete all pods

   echo "[3] Force deleting iDRAC pods..."

   kubectl delete pod -n "$NAMESPACE" -l app=idrac-telemetry --force --grace-period=0

   # Step 4: Re-deploy

   echo "[4] Re-deploy with: ansible-playbook telemetry/telemetry.yml"

   echo "    Use the SAME inputs as previous deployment."

**Usage Instructions**

1. Save each script to a file with the corresponding name (e.g., ``kafka_lock_cleanup.sh``, ``idrac_lock_cleanup.sh``, ``idrac_data_corruption_recovery.sh``)

2. Make the scripts executable::

   chmod +x kafka_lock_cleanup.sh idrac_lock_cleanup.sh idrac_data_corruption_recovery.sh

3. Run the appropriate script based on the affected component:

   - For Kafka lock issues: ``./kafka_lock_cleanup.sh``
   - For iDRAC lock issues: ``./idrac_lock_cleanup.sh`` (this script automatically checks for corruption and aborts if found)
   - For iDRAC data corruption: ``./idrac_data_corruption_recovery.sh``