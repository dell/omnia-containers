# Deploy CSI Driver for Dell PowerScale

Dell PowerScale is a scale-out NAS storage solution for AI and HPC workloads.
Omnia deploys the **Dell CSI PowerScale driver v2.17.0** on Kubernetes clusters
using Helm charts, enabling persistent storage backed by PowerScale.

For more information on the CSI PowerScale driver, see the
[Dell CSM Installation Guide](https://dell.github.io/csm-docs/docs/getting-started/installation/kubernetes/powerscale/helm/).

!!! note
    - Omnia does **not** configure any PowerScale device via OneFS. It only
      configures the deployed Kubernetes cluster to interact with PowerScale
      storage.
    - Sample `secret.yaml` and `values.yaml` files are available in
      `omnia/examples/powerscale_reference_files/CSI_driver/` for reference
      only. Always download the actual files from the links provided in the
      prerequisite steps below.


## Overview

Omnia automates the following steps when the CSI PowerScale driver is enabled:

- Creates the `isilon` namespace on the Kubernetes cluster
- Creates and patches the `isilon-creds` secret with Base64-encoded credentials from `omnia_config_credentials`
- Applies the empty certificate secret (`isilon-certs-0`)
- Deploys the external-snapshotter CRDs and snapshot controller (v8.5.0)
- Installs the CSI PowerScale driver via the `csi-install.sh` Helm installer
- Creates the `ps01` StorageClass and sets it as the default (demoting `nfs-client` if present)


## PowerScale SmartConnect (Optional)

To use the PowerScale SmartConnect hostname, you need an upstream DNS server
that includes delegation mappings of hostname to PowerScale IP addresses.

**During provisioning:** Specify the upstream DNS server IP in
`/opt/omnia/input/project_default/network_spec.yml`:

```yaml title="File: /opt/omnia/input/project_default/network_spec.yml"
---
Networks:
  - admin_network:
      oim_nic_name: <network name>
      netmask_bits: "24"
      primary_oim_admin_ip: "172.16.107.254"
      primary_oim_bmc_ip: ""
      dynamic_range: "172.16.107.201-172.16.107.250"
      dns: ["10.x.x.x", "11.x.x.x"]
```

**After provisioning:** If the upstream DNS server was not specified during
provisioning, add the DNS server IP to `network_spec.yml` and re-run the
`provision.yml` playbook.


## Prerequisites

1. **Kubernetes cluster configured:** A `service_k8s_cluster` must be defined
   in `omnia_config.yml` with `deployment: true`. See
   [Set Up Kubernetes](setup_service_k8s.md) for details.

2. **NFS share for Kubernetes:** An NFS mount entry named to match the
   `nfs_storage_name` in your `service_k8s_cluster` must exist in
   `storage_config.yml`. This NFS share stores the CSI driver artifacts,
   Helm charts, and deployment scripts for the cluster nodes.

    ```yaml title="File: /opt/omnia/input/project_default/storage_config.yml"
    mounts:
      - name: "nfs_k8s"
        source: "172.16.107.121:/mnt/share/omnia_k8s"
        mount_point: "/opt/omnia/k8s_mount"
        fs_type: "nfs"
        mnt_opts: "nosuid,rw,sync,hard,intr"
        mount_on_oim: true
        functional_group_prefix: ["service_kube"]
    ```

    !!! important
        The `name` value (e.g., `nfs_k8s`) must match the
        `nfs_storage_name` field in `omnia_config.yml`.

3. **Network configuration:** Ensure that the storage and data networks are
   configured correctly via DHCP. The PowerScale endpoint must be reachable
   from both the OIM and the Kubernetes nodes.

4. **DNS resolution:** Upstream DNS resolution must be available from both
   the admin (PXE) and storage networks.

5. **PowerScale system:** Verify that the PowerScale system is operational
   and the OneFS API is accessible on the configured endpoint port.

6. **Enable basic authentication on PowerScale:**

    Omnia uses basic authentication (`isiAuthType: 0`) to connect with
    PowerScale devices. To check and enable it:

    **a.** SSH into the PowerScale node.

    **b.** Check if basic auth is enabled:

    ```bash title="Run on: PowerScale node"
    cat /usr/local/apache2/conf/webui_httpd.conf | grep -A 20 "# Platform API"
    ```

    **c.** If the response shows `IsiAuthTypeBasic Off`, enable it:

    ```bash title="Run on: PowerScale node"
    isi_gconfig -t web-config auth_basic=true
    ```

7. **Configure PowerScale user privileges:**

    !!! note
        This step is required only if you want to collect PowerScale
        telemetry.

    The username in `secret.yaml` must be from the PowerScale authentication
    providers with sufficient privileges. The required privileges are:

    | Privilege               | Type       |
    |-------------------------|------------|
    | ISI_PRIV_LOGIN_PAPI     | Read Only  |
    | ISI_PRIV_NFS            | Read Write |
    | ISI_PRIV_QUOTA          | Read Write |
    | ISI_PRIV_SNAPSHOT        | Read Write |
    | ISI_PRIV_IFS_RESTORE    | Read Only  |
    | ISI_PRIV_NS_IFS_ACCESS  | Read Only  |
    | ISI_PRIV_IFS_BACKUP     | Read Only  |
    | ISI_PRIV_AUTH_ZONES     | Read Only  |
    | ISI_PRIV_SYNCIQ         | Read Write |
    | ISI_PRIV_STATISTICS     | Read Only  |

    For more information, see the
    [CSM Installation Guide](https://dell.github.io/csm-docs/docs/getting-started/installation/kubernetes/powerscale/helm/).

    ??? example "Create group and user for CSM"

        **a.** Create the group and user:

        ```bash title="Run on: PowerScale node"
        isi auth group create csmadmins --zone system
        isi auth user create csmadmin --password "P@ssw0rd123" \
          --password-expires false --primary-group csmadmins --zone system
        ```

        **b.** Create the role and assign permissions:

        ```bash title="Run on: PowerScale node"
        isi auth roles create CSMAdminRole \
          --description "Dell CSM Admin Role" --zone System

        isi auth roles modify CSMAdminRole --zone System \
          --add-priv-read ISI_PRIV_LOGIN_PAPI \
          --add-priv-read ISI_PRIV_IFS_RESTORE \
          --add-priv-read ISI_PRIV_NS_IFS_ACCESS \
          --add-priv-read ISI_PRIV_IFS_BACKUP \
          --add-priv-read ISI_PRIV_AUTH \
          --add-priv-read ISI_PRIV_AUTH_ZONES \
          --add-priv-read ISI_PRIV_STATISTICS

        isi auth roles modify CSMAdminRole --zone System \
          --add-priv-write ISI_PRIV_NFS \
          --add-priv-write ISI_PRIV_QUOTA \
          --add-priv-write ISI_PRIV_SNAPSHOT \
          --add-priv-write ISI_PRIV_SYNCIQ

        isi auth roles modify CSMAdminRole --add-group csmadmins
        ```

        !!! note
            Verify all roles for the user have these privileges:
            `isi auth roles list`

8. **Download and configure `secret.yaml`:**

    ```bash title="Run on: omnia_core"
    wget https://raw.githubusercontent.com/dell/csi-powerscale/refs/heads/release/v2.17.0/samples/secret/secret.yaml
    ```

    Update the following parameters (keep the rest as defaults):

    | Parameter       | Value                                  |
    |-----------------|----------------------------------------|
    | `clusterName`   | Your desired cluster name              |
    | `endpoint`      | PowerScale SmartConnect hostname or IP |
    | `endpointPort`  | Endpoint port (default: `8080`)        |
    | `isDefault`     | `true`                                 |

    !!! important
        Do **not** update the `username` and `password` fields in
        `secret.yaml`. Omnia reads these from the
        `omnia_config_credentials` file and automatically Base64-encodes
        and injects them during deployment.

    !!! note
        If SmartConnect is configured, you can use the PowerScale hostname
        for `endpoint`. Otherwise, use the PowerScale IP address. Ensure
        the endpoint is reachable from the OIM and the Kubernetes nodes.

9. **Download and configure `values.yaml`:**

    ```bash title="Run on: omnia_core"
    wget https://raw.githubusercontent.com/dell/helm-charts/csi-isilon-2.17.0/charts/csi-isilon/values.yaml
    ```

    Update the following parameters (keep the rest as defaults):

    | Parameter                    | Required Value | Description                               |
    |------------------------------|----------------|-------------------------------------------|
    | `controller.controllerCount` | `1`            | Number of CSI controller pods              |
    | `controller.replication.enabled` | `false`    | Replication must be disabled               |
    | `controller.snapshot.enabled` | `true`        | Volume snapshots must be enabled           |
    | `controller.resizer.enabled` | `false`        | Volume expansion is not supported          |
    | `node.dnsPolicy`             | `Default`      | Pod DNS policy for node daemonset          |
    | `skipCertificateValidation`  | `true`         | Skip OneFS API certificate verification    |
    | `endpointPort`               | `8080`         | OneFS API server HTTPS port                |
    | `isiAccessZone`              | `System`       | PowerScale access zone name                |
    | `isiPath`                    | `/ifs/data/csi` | Base path for CSI volumes on PowerScale   |
    | `enableQuota`                | `false`         | Disable SmartQuotas |

    !!! caution
        The `isiPath` and `isiAccessZone` values are used by Omnia to
        generate the `ps01` StorageClass. Ensure the `isiPath` directory
        exists on the PowerScale cluster before deployment.

    !!! warning
        Once the PowerScale CSI driver is deployed, the parameters in
        `values.yaml` **cannot** be changed. To modify them, you must first
        uninstall the driver (see [Uninstallation](#uninstallation)) and then
        manually re-install it.

10. **Set up credentials:** Run the `get_config_credentials.yml` playbook and
    provide the `csi_username` and `csi_password` values when prompted. These
    credentials are stored in the `omnia_config_credentials` vault file.

    ```bash title="Run on: omnia_core"
    ansible-playbook utils/credential_utility/get_config_credentials.yml
    ```


## Procedure

1. **Add the CSI driver entry** to the `softwares` array in
   `/opt/omnia/input/project_default/software_config.json`:

    ```json title="File: /opt/omnia/input/project_default/software_config.json"
    {"name": "csi_driver_powerscale", "version": "v2.17.0", "arch": ["x86_64"]}
    ```

    !!! note
        The `csi_driver_powerscale` entry is **not** present in
        `software_config.json` by default. You must add it manually to the
        `softwares` list.

2. **Download required artifacts** by running the `local_repo.yml` playbook.
   This downloads the CSI PowerScale driver, Helm charts, external-snapshotter,
   and all required container images to the local repository:

    ```bash title="Run on: omnia_core"
    cd /opt/omnia/local_repo
    ansible-playbook local_repo.yml
    ```

3. **Configure the CSI driver file paths** in
   `/opt/omnia/input/project_default/omnia_config.yml` under the
   `service_k8s_cluster` section:

    ```yaml title="File: /opt/omnia/input/project_default/omnia_config.yml"
    service_k8s_cluster:
      - cluster_name: service_cluster
        deployment: true
        k8s_cni: "calico"
        pod_external_ip_range: "172.16.107.170-172.16.107.200"
        k8s_service_addresses: "10.233.0.0/18"
        k8s_pod_network_cidr: "10.233.64.0/18"
        nfs_storage_name: "nfs_k8s"
        k8s_crio_storage_size: "20G"
        csi_powerscale_driver_secret_file_path: "/opt/omnia/input/project_default/secret.yaml"
        csi_powerscale_driver_values_file_path: "/opt/omnia/input/project_default/values.yaml"
    ```

    !!! important
        Both `csi_powerscale_driver_secret_file_path` and
        `csi_powerscale_driver_values_file_path` must be absolute paths to
        the files you downloaded and configured in the prerequisites. If
        either path is empty, the CSI driver will not be deployed.

4. **Build cluster images** by running the `build_image` playbook. This
   bakes the CSI PowerScale driver artifacts and dependencies into the
   cluster node images:

    ```bash title="Run on: omnia_core"
    cd /opt/omnia/build_image_x86_64
    ansible-playbook build_image_x86_64.yml
    ```

    !!! note
        For aarch64 nodes, run the aarch64 variant instead:
        `cd /opt/omnia/build_image_aarch64 && ansible-playbook build_image_aarch64.yml`

5. **Run the provisioning playbook** to deploy Kubernetes and install the
   PowerScale CSI driver on the `service_k8s_cluster`:

    ```bash title="Run on: omnia_core"
    cd /opt/omnia/discovery
    ansible-playbook provision.yml
    ```

    !!! note
        If using OME-based discovery, add the `discovery_mechanism` parameter:
        `ansible-playbook provision.yml -e "discovery_mechanism=ome"`


## Verification

After successful execution of the `provision.yml` playbook, verify the
deployment on the `service_kube_control_plane` node.

1. **Check CSI driver pods** are running in the `isilon` namespace:

    ```bash title="Run on: kube_control_plane"
    kubectl get pods -n isilon
    ```

    ```text title="Expected output"
    NAME                                READY   STATUS    RESTARTS   AGE
    isilon-controller-xxxxxxxxx-xxxxx   5/5     Running   0          5m
    isilon-node-xxxxx                   2/2     Running   0          5m
    ```

2. **Check the snapshot controller** is running:

    ```bash title="Run on: kube_control_plane"
    kubectl get pods -n kube-system | grep snapshot-controller
    ```

3. **Verify the StorageClass** `ps01` is created and set as default:

    ```bash title="Run on: kube_control_plane"
    kubectl get sc
    ```

    ```text title="Expected output"
    NAME            PROVISIONER              RECLAIMPOLICY   VOLUMEBINDINGMODE   ALLOWVOLUMEEXPANSION   AGE
    ps01 (default)  csi-isilon.dellemc.com   Retain          Immediate           true                   5m
    nfs-client      cluster.local/nfs-...    Delete          Immediate           true                   30m
    ```

4. **Verify the isilon-creds secret** exists:

    ```bash title="Run on: kube_control_plane"
    kubectl get secret isilon-creds -n isilon
    ```

The `ps01` StorageClass is automatically generated with the following
configuration derived from your `values.yaml` and `secret.yaml`:

```yaml title="Example: auto-generated ps01 StorageClass"
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ps01
provisioner: csi-isilon.dellemc.com
reclaimPolicy: Retain
allowVolumeExpansion: true
volumeBindingMode: Immediate
parameters:
  AccessZone: System
  AzServiceIP: <endpoint from secret.yaml>
  Isipath: /ifs/data/csi
  RootClientEnabled: "true"
  csi.storage.k8s.io/fstype: "nfs"
```

!!! failure "If installation errors occur"
    Uninstall the CSI driver first (see [Uninstallation](#uninstallation)),
    verify that all prerequisites are met, then manually re-install using
    the following commands:

    ```bash title="Run on: kube_control_plane"
    kubectl create namespace isilon

    kubectl create secret generic isilon-creds -n isilon \
      --from-file=config="/opt/omnia/<csi-powerscale-version>/secret.yaml"

    kubectl apply -f /opt/omnia/<csi-powerscale-version>/empty_isilon-certs.yaml

    kubectl apply -f /opt/omnia/<csi-powerscale-version>/external-snapshotter/client/config/crd/
    kubectl apply -f /opt/omnia/<csi-powerscale-version>/external-snapshotter/deploy/kubernetes/snapshot-controller/

    cd /opt/omnia/<csi-powerscale-version>/dell-csi-helm-installer
    ./csi-install.sh --namespace isilon \
      --values /opt/omnia/<csi-powerscale-version>/values.yaml

    kubectl apply -f /opt/omnia/<csi-powerscale-version>/ps_storage_class.yml
    ```

    Replace `<csi-powerscale-version>` with the versioned directory name
    (e.g., `csi-powerscale-v2.17.0`).


## Post Installation

### Create a Custom Storage Class (Optional)

To create a custom storage class, use the sample
[storage class template](https://github.com/dell/csi-powerscale/blob/main/samples/storageclass/isilon.yaml):

```yaml title="Example: custom StorageClass"
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: <storage class name>
provisioner: csi-isilon.dellemc.com
reclaimPolicy: Retain
allowVolumeExpansion: true
volumeBindingMode: Immediate
parameters:
  clusterName: <powerscale cluster name>
  AccessZone: System
  AzServiceIP: <SmartConnect hostname or IP>
  Isipath: <isipath configured in powerscale>
  RootClientEnabled: "true"
  csi.storage.k8s.io/fstype: "nfs"
```

!!! note
    - If SmartConnect is configured with a delegated host list in the
      external DNS server, you can provide the hostname for `AzServiceIP`.
      Otherwise, use the PowerScale IP address.
    - If storage class parameters change for a PowerScale cluster, update the
      existing storage class or create a new one.

Apply the storage class:

```bash title="Run on: kube_control_plane"
kubectl apply -f <storageclass_file.yaml>
```

### Create a Persistent Volume Claim (PVC)

Once the storage class is created, use it to create a PVC. Below is a sample
deployment with a PVC:

```yaml title="Example: PVC and Deployment manifest"
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pvc-powerscale
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 1Gi
  storageClassName: ps01
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: deploy-busybox-01
spec:
  strategy:
    type: Recreate
  replicas: 1
  selector:
    matchLabels:
      app: deploy-busybox-01
  template:
    metadata:
      labels:
        app: deploy-busybox-01
    spec:
      containers:
        - name: busybox
          image: docker.io/library/busybox:1.36
          command: ["sh", "-c"]
          args:
            - "while true; do touch /data/datafile; rm -f /data/datafile; done"
          volumeMounts:
            - name: data
              mountPath: /data
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: pvc-powerscale
```

Apply the deployment manifest:

```bash title="Run on: kube_control_plane"
kubectl apply -f <manifest_filepath>
```

### Verify the PVC

Check that the PVC is in **Bound** status:

```bash title="Run on: kube_control_plane"
kubectl get pvc -A
```

```text title="Expected output"
NAMESPACE   NAME             STATUS   VOLUME              CAPACITY   ACCESS MODES   STORAGECLASS   AGE
default     pvc-powerscale   Bound    csivol-98d3e7631d   1Gi        RWX            ps01           27h
```

You can also verify the volume from the OneFS portal — it will show a
matching entry for the `VOLUME` name (e.g., `csivol-98d3e7631d`).


## Uninstallation

To uninstall the PowerScale CSI driver manually:

1. **Log in** to the `service_kube_control_plane` node.

2. **Navigate** to the installer directory:

    ```bash title="Run on: kube_control_plane"
    cd /opt/omnia/<csi-powerscale-version>/dell-csi-helm-installer
    ```

3. **Run the uninstall script:**

    ```bash title="Run on: kube_control_plane"
    ./csi-uninstall.sh --namespace isilon
    ```

4. The driver is removed, but **secrets and PVCs are not deleted
   automatically**. Remove them manually from the `isilon` namespace if
   needed.

5. **To fully remove PowerScale resources** (optional):

    **a.** Delete the PowerScale secrets:

    ```bash title="Run on: kube_control_plane"
    kubectl delete secret isilon-creds -n isilon
    kubectl delete secret isilon-certs-0 -n isilon
    ```

    **b.** Remove any custom deployments and PVCs that use the PowerScale
    storage class.

    **c.** Remove the PowerScale storage class:

    ```bash title="Run on: kube_control_plane"
    kubectl delete sc ps01
    ```

    **d.** Delete the snapshot controller deployment:

    ```bash title="Run on: kube_control_plane"
    kubectl delete deployment snapshot-controller -n kube-system
    ```

    **e.** Delete the isilon namespace:

    ```bash title="Run on: kube_control_plane"
    kubectl delete namespace isilon
    ```

!!! note "Updating OneFS credentials"
    If the OneFS portal credentials change, update the `secret.yaml`
    manually:

    1. Update `secret.yaml` with the new credentials.
    2. Copy the updated file to the `kube_control_plane` node.
    3. Delete the existing secret:

        ```bash title="Run on: kube_control_plane"
        kubectl delete secret isilon-creds -n isilon
        ```

    4. Create a new secret:

        ```bash title="Run on: kube_control_plane"
        kubectl create secret generic isilon-creds -n isilon \
          --from-file=config=<updated_secret.yaml_filepath>
        ```


## Troubleshooting

### CSI pods not starting

Run the following command to inspect pod events:

```bash title="Run on: kube_control_plane"
kubectl describe pods -n isilon
```

Common causes:

- PowerScale endpoint is unreachable from the Kubernetes nodes
- `secret.yaml` contains incorrect endpoint or credentials
- NFS share is not mounted on the Kubernetes nodes

### Driver already deployed

If the error message indicates the driver is already deployed, uninstall it
first using the steps in [Uninstallation](#uninstallation) before re-running
the provisioning playbook.

### StorageClass ps01 not created

The `ps01` StorageClass is only created if all CSI pods reach `Running`
state. Check the pod status and logs:

```bash title="Run on: kube_control_plane"
kubectl logs -n isilon deployment/isilon-controller --all-containers
```


## Next Steps

- [Set Up Telemetry](../Telemetry/setup_telemetry.md) -- Deploy telemetry
  with PowerScale-backed persistent storage.
- [Configure NFS](../Storage/configure_nfs.md) -- Configure NFS for Slurm
  compute nodes.
- [Set Up Kubernetes](setup_service_k8s.md) -- Review the Kubernetes cluster
  configuration options.
