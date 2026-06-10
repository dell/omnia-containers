Kubernetes
==========

⦾ **Why do static pods show "Running" status after a control plane node is powered off or rebooted?**

**Potential Causes**: This is a known Kubernetes limitation with graceful node shutdown. When a control plane node is powered off, shut down, or rebooted, kubelet may not have enough time to update pod status to the API server before the node shuts down. This creates a race condition where the behavior is **intermittent and unpredictable**:

- The node is marked as ``NotReady``.
- Static pods (``kube-apiserver``, ``etcd``, ``kube-controller-manager``, ``kube-scheduler``, ``kube-vip``) show stale "Running" status.
- Container state remains as "running" even though containers are stopped.

This occurs due to a race condition during shutdown. Kubelet attempts to update pod status to the API server, but the API server itself is shutting down or the VIP (kube-vip) becomes unavailable before the status update completes, creating a circular dependency. The behavior varies - sometimes pods show correct status, sometimes they show stale "Running" status, depending on timing and network conditions.

**Impact**: 

- No functional impact on cluster operations
- Cluster continues to operate normally with remaining control planes
- Pods are automatically garbage collected based on ``--terminated-pod-gc-threshold=5``
- When node powers back on, pods restart automatically

**Resolution**: This is expected behavior and does not require action. For detailed information, see `Static Pods Show Stale "Running" State After Node Shutdown <../troubleshootingguide.html#static-pods-show-stale-running-state-after-node-shutdown>`_ in the Troubleshooting Guide.

**Related Kubernetes Issues**:

- `Issue #110755 <https://github.com/kubernetes/kubernetes/issues/110755>`_
- `Issue #124448 <https://github.com/kubernetes/kubernetes/issues/124448>`_
- `Issue #109531 <https://github.com/kubernetes/kubernetes/issues/109531>`_

**Official Documentation**: `Kubernetes Node Shutdowns <https://kubernetes.io/docs/concepts/cluster-administration/node-shutdown/>`_
