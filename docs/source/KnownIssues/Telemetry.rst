Telemetry
==========

⦾ **When a Kubernetes worker node fails, affected telemetry services may take time to fail over to available worker nodes.**

**Resolution**: No manual intervention is required.  Wait for the telemetry services to recover and fail over automatically. Do not restart pods or nodes during this period, as it may extend recovery time.


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

**Usage Instructions**

1. Save each script to a file with the corresponding name (e.g., ``kafka_lock_cleanup.sh``, ``idrac_lock_cleanup.sh``, ``idrac_data_corruption_recovery.sh``)

2. Make the scripts executable::

    chmod +x kafka_lock_cleanup.sh idrac_lock_cleanup.sh idrac_data_corruption_recovery.sh

3. Run the scripts in the following order:

   **Important**: If both Kafka and iDRAC scripts need to be executed, run the Kafka script first and wait for 1 minute before executing the iDRAC script.

   - For Kafka lock issues: ``./kafka_lock_cleanup.sh``
   - For iDRAC lock issues: ``./idrac_lock_cleanup.sh``
   - For iDRAC data corruption: ``./idrac_data_corruption_recovery.sh``

**Kafka Lock Cleanup Script**

Save the following script as ``kafka_lock_cleanup.sh``::
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
        kubectl wait --for=jsonpath='{.status.phase}'=Succeeded pod/kafka-lock-cleanup -n telemetry --timeout=120s
        kubectl logs kafka-lock-cleanup -n "$NAMESPACE"
        kubectl delete pod kafka-lock-cleanup -n "$NAMESPACE"
    done
    echo "[5] Verify: kubectl get pods -n $NAMESPACE -l strimzi.io/kind=Kafka"


**iDRAC Lock Cleanup Script**
Save the following script as ``idrac_lock_cleanup.sh``::
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
     kubectl wait --for=jsonpath='{.status.phase}'=Succeeded pod/mysql-lock-cleanup -n "$NAMESPACE" --timeout=120s
     kubectl logs mysql-lock-cleanup -n "$NAMESPACE"
     kubectl delete pod mysql-lock-cleanup -n "$NAMESPACE"
   done
   echo "[6] Verify: kubectl get pods -n $NAMESPACE -l app=idrac-telemetry"

**iDRAC Data Corruption Recovery Script**

Save the following script as ``idrac_data_corruption_recovery.sh``::
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

   # Step 2: Force delete all pods FIRST (releases PVC binding)

   echo "[2] Force deleting iDRAC pods..."
   kubectl delete pod -n "$NAMESPACE" -l app=idrac-telemetry --force --grace-period=0

   # Step 3: Wait for pods to terminate

   echo "[3] Waiting for pods to terminate..."
   sleep 10

   # Step 4: Delete PVCs (now unbound)

   echo "[4] Deleting iDRAC PVCs..."
   kubectl delete pvc -n "$NAMESPACE" -l app=idrac-telemetry --wait=false

   # Step 5: Verify PVCs are terminating


   echo "[5] Checking PVC status..."
   sleep 5
   REMAINING=$(kubectl get pvc -n "$NAMESPACE" -l app=idrac-telemetry --no-headers 2>/dev/null | wc -l)
   if [[ "$REMAINING" -gt 0 ]]; then
     echo "PVCs still terminating. Removing finalizers..."
     for PVC in $(kubectl get pvc -n "$NAMESPACE" -l app=idrac-telemetry -o jsonpath='{.items[*].metadata.name}'); do
       kubectl patch pvc "$PVC" -n "$NAMESPACE" -p '{"metadata":{"finalizers":null}}'
       echo "Finalizer removed from: $PVC"
     done
     sleep 5
   fi

   # Step 6: Final verification


   echo "[6] Verifying cleanup..."
   kubectl get pvc -n "$NAMESPACE" -l app=idrac-telemetry 2>/dev/null || echo "All PVCs deleted."
   kubectl get pod -n "$NAMESPACE" -l app=idrac-telemetry 2>/dev/null || echo "All pods deleted."

   # Step 7: Re-deploy


   echo ""
   echo "[7] Re-deploy with: ansible-playbook telemetry/telemetry.yml"
   echo "    Use the SAME inputs as previous deployment."
