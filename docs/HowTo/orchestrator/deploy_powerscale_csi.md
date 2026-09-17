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
      `src/orchestrator/examples/powerscale_reference_files/CSI_driver/` for reference
      only. Always download the actual files from the links provided in the
      prerequisite steps below.
    - Ensure that NFSv4 is enabled on the PowerScale cluster before deploying and configuring the CSI driver. NFSv4 helps prevent stale file locks and improves pod recovery after node reboot events. Omnia does not enable or modify NFS protocol settings on the PowerScale storage system.


## Overview

Omnia automates the following steps when the CSI PowerScale driver is enabled:

- Creates the `isilon` namespace on the Kubernetes cluster
- Creates and patches the `isilon-creds` secret with Base64-encoded credentials from `orchestrator_credentials.yml`
- Applies the empty certificate secret (`isilon-certs-0`)
- Deploys the external-snapshotter CRDs and snapshot controller (v8.5.0)
- Installs the CSI PowerScale driver via the `csi-install.sh` Helm installer
- Creates the `ps01` StorageClass and sets it as the default (demoting `nfs-client` if present)


### PowerScale SmartConnect (Optional)

To use the PowerScale SmartConnect hostname, you need an upstream DNS server
that includes delegation mappings of hostname to PowerScale IP addresses.

**During provisioning:** Specify the upstream DNS server IP in
`network_spec.yml` in the active project's Orchestrator input directory:

```yaml title="File: network_spec.yml"
---
Networks:
  - admin_network:
      oim_nic_name: <network name>
      subnet: "172.16.107.0"
      netmask_bits: "24"
      primary_oim_admin_ip: "172.16.107.254"
      primary_oim_bmc_ip: ""
      router: "172.16.107.254"
      dynamic_range: "172.16.107.201-172.16.107.250"
      dns: ["10.x.x.x", "11.x.x.x"]
```

**After provisioning:** If the upstream DNS server was not specified during
provisioning, add the DNS server IP to `network_spec.yml` and re-run the
Orchestrator `provision` workflow to regenerate cloud-init. Then PXE boot or
otherwise reprovision the affected Kubernetes nodes so they consume the new
metadata. Running `provision` alone does not update an already provisioned
node.


## Prerequisites

1. **Kubernetes cluster configured:** A `service_k8s_cluster` must be defined
   in `omnia_config.yml` with `deployment: true` and
   `enable_powerscale_csi: true`. See
   [Set Up Kubernetes](deploy_kubernetes.md) for details.

2. **NFS share for Kubernetes:** An NFS mount entry named to match the
   `nfs_storage_name` in your `service_k8s_cluster` must exist in
   `storage_config.yml`. This NFS share stores the CSI driver artifacts,
   Helm charts, and deployment scripts for the cluster nodes.

    ```yaml title="File: storage_config.yml"
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

    Omnia uses basic authentication (`isiAuthType: 0`) to connect to
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
        The example role below grants the privileges listed in this section
        for PowerScale API, NFS, quota, snapshot, and access-zone operations.
        Confirm the required privileges against the installation guide for
        the deployed CSI driver version. PowerScale telemetry can require
        additional read privileges; review its separate telemetry guide when
        that source is enabled.

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
    | ISI_PRIV_AUTH           | Read Only  |
    | ISI_PRIV_AUTH_ZONES     | Read Only  |
    | ISI_PRIV_SYNCIQ         | Read Write |
    | ISI_PRIV_STATISTICS     | Read Only  |

    For more information, see the
    [CSM Installation Guide](https://dell.github.io/csm-docs/docs/getting-started/installation/kubernetes/powerscale/helm/).

    ??? example "Create group and user for CSM"

        **a.** Create the group and user:

        ```bash title="Run on: PowerScale node"
        isi auth group create csmadmins --zone system
        isi auth user create csmadmin --password "<secure-password>" \
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

        isi auth roles modify CSMAdminRole --zone System --add-group csmadmins
        ```

        !!! note
            Verify all roles for the user have these privileges:
            `isi auth roles list`

8. **Download and configure `secret.yaml`:**

    ```bash title="Run on: OIM"
    wget https://raw.githubusercontent.com/dell/csi-powerscale/refs/heads/release/v2.17.0/samples/secret/secret.yaml
    ```

    Keep `isilonClusters` as a non-empty list of mappings. Every entry must
    define `clusterName` and `endpoint` as non-empty strings, `username` and
    `password` as strings, and `isDefault` as a Boolean. Exactly one entry must
    set `isDefault: true`. The validator also checks the optional fields shown
    below when they are present:

    | Parameter | Requirement |
    | --- | --- |
    | `endpointPort` | Integer from 1 through 65535 |
    | `skipCertificateValidation` | Boolean |
    | `isiPath` | Absolute path when provided |
    | `isiVolumePathPermissions` | Three- or four-digit octal string when provided |

    !!! important
        Do **not** update the `username` and `password` fields in
        `secret.yaml`. Omnia reads these from the
        `orchestrator_credentials.yml` file and automatically Base64-encodes
        and injects them during deployment.

        A plaintext `secret.yaml` is accepted. If you encrypt it before
        validation, place the matching Vault password file at
        `.csi_powerscale_secret_vault` in the active Orchestrator project input
        directory. An encrypted file without that exact key file, or one that
        cannot be decrypted and parsed, fails validation.

    !!! note
        If SmartConnect is configured, you can use the PowerScale hostname
        for `endpoint`. Otherwise, use the PowerScale IP address. Ensure
        the endpoint is reachable from the OIM and the Kubernetes nodes.

9. **Download and configure `values.yaml`:**

    ```bash title="Run on: OIM"
    wget https://raw.githubusercontent.com/dell/helm-charts/csi-isilon-2.17.0/charts/csi-isilon/values.yaml
    ```

    `values.yaml` must be a readable, non-empty, plaintext YAML mapping. The
    validator requires the following values; an Ansible Vault-encrypted values
    file is not accepted:

    | Parameter | Required value or constraint | Description |
    | --- | --- | --- |
    | `controller.controllerCount` | `1` | Number of CSI controller pods |
    | `controller.replication.enabled` | `false` | Replication sidecar is disabled |
    | `controller.snapshot.enabled` | `true` | Volume snapshot sidecar is enabled |
    | `controller.resizer.enabled` | Boolean | Enables or disables the volume expansion sidecar |
    | `skipCertificateValidation` | Boolean | Controls OneFS API certificate verification |
    | `isiAuthType` | `0` or `1` | Authentication type accepted by the driver |
    | `endpointPort` | Integer from 1 through 65535 | OneFS API server port |
    | `isiAccessZone` | Non-empty string | PowerScale access zone used by `ps01` |
    | `isiPath` | Absolute path | Base path used by `ps01` for CSI volumes |
    | `isiVolumePathPermissions` | Three- or four-digit octal string | Permissions for created volume paths |

    !!! caution
        The top-level `isiPath` and `isiAccessZone` keys are required because
        Omnia reads them to generate the `ps01` StorageClass. Ensure the
        `isiPath` directory exists on the PowerScale cluster before
        deployment. Omnia also reads the `endpoint` from the first
        `isilonClusters` entry in `secret.yaml`.

    !!! warning "Protect staged credentials"
        Ansible Vault protects `orchestrator_credentials.yml`, but Base64 in
        `secret.yaml` and the Kubernetes Secret is encoding, not encryption.
        During staging, the current workflow decrypts the configured source
        `secret.yaml` when necessary, injects the encoded credentials, and
        copies it with mode `0600`; it does not re-encrypt that source file
        afterward. Restrict access to the project input directory and the
        Kubernetes NFS staging share.

    !!! warning
        Omnia does not reconcile `values.yaml` changes into an existing CSI
        deployment. The generated deployment script skips installation when
        it detects existing `isilon` driver pods. Apply changes through a
        driver-supported maintenance procedure, or uninstall and redeploy the
        driver as described in [Uninstallation](#uninstallation).

10. **Set up credentials:** After setting `enable_powerscale_csi: true` on the
    deployed `service_k8s_cluster`, run the Orchestrator credential workflow.
    It prompts for `csi_username` and `csi_password` and stores them in the
    encrypted Orchestrator credential file.

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run orchestrator --tags credentials
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/orchestrator
        ansible-playbook playbooks/orchestrator.yml --tags credentials
        ```


## Procedure

1. **Select the CSI driver catalog content.** Ensure that the catalog selected
   by `CATALOG_FILE_PATH` includes the catalog group `powerscale_csi_group` for
   `x86_64`, so Repo Manager can publish the required driver, Helm chart,
   snapshotter, and image dependencies. Catalog content does not enable the
   driver.

2. **Synchronize the required artifacts** by following
   [Configure Repositories](../repo_manager/configure_repos.md). Repo Manager
   publishes the CSI PowerScale driver, Helm charts, external-snapshotter, and
   required images in `repo_status.yml` for Orchestrator.

3. **Enable and configure the CSI driver** in `omnia_config.yml` in the active
   project's Orchestrator input directory, under the `service_k8s_cluster`
   section. Resolve the project directory in the current shell before editing
   the file:

    ```bash title="Run on: OIM"
    source /etc/profile.d/omnia-env.sh
    orchestrator_path="${ORCHESTRATOR_DATA_PATH:-${OMNIA_DATA_PATH}/orchestrator}"
    source "$OMNIA_DATA_PATH/activate-omnia.sh"
    printf '%s\n' "$orchestrator_path/input/$OMNIA_PROJECT_NAME"
    ```

    ```yaml title="File: omnia_config.yml"
    service_k8s_cluster:
      - cluster_name: service_cluster
        deployment: true
        etcd_on_local_disk: false
        enable_powerscale_csi: true
        k8s_cni: "calico"
        pod_external_ip_range: "172.16.107.170-172.16.107.200"
        k8s_service_addresses: "10.233.0.0/18"
        k8s_pod_network_cidr: "10.233.64.0/18"
        nfs_storage_name: "nfs_k8s"
        k8s_crio_storage_size: "20G"
        csi_powerscale_driver_secret_file_path: "/absolute/path/to/orchestrator/input/project/secret.yaml"
        csi_powerscale_driver_values_file_path: "/absolute/path/to/orchestrator/input/project/values.yaml"
    ```

    !!! important
        `enable_powerscale_csi` is the only setting that enables PowerScale
        CSI. Omitting it or setting it to `false` disables CSI even when the
        catalog contains CSI content or the file paths are populated.

        Both `csi_powerscale_driver_secret_file_path` and
        `csi_powerscale_driver_values_file_path` must be absolute paths to
        existing regular files when `enable_powerscale_csi` is `true`. An
        empty, relative, missing, or non-file path causes validation to fail.
        Set them to absolute paths beneath the project directory printed by
        the command above; shell-variable expressions are not expanded inside
        YAML values.

4. **Build the service Kubernetes images** by following
   [Build Images](../image_build_manager/build_images.md).

5. **Run the provisioning playbook** to deploy Kubernetes and install the
   PowerScale CSI driver on the `service_k8s_cluster`:

    === "Using omnia.sh (recommended)"

        ```bash title="Run on: OIM"
        cd <OMNIA_SOURCE_PATH>/src/main
        ./omnia.sh --run orchestrator --tags provision
        ```

    === "Using ansible-playbook"

        ```bash title="Run on: OIM"
        source /opt/omnia/activate-omnia.sh
        cd <OMNIA_SOURCE_PATH>/src/orchestrator
        ansible-playbook playbooks/orchestrator.yml --tags provision
        ```

    The `provision` phase generates the first control-plane node's cloud-init
    metadata, including the CSI deployment script. The driver is installed
    when that node boots and consumes the metadata. Running `provision` alone
    does not install or update the driver on an already provisioned node; PXE
    boot or otherwise reprovision the node for an initial automated install.

## Verification

After the first `service_kube_control_plane` node has consumed its generated
cloud-init metadata, verify the deployment on that node.

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

!!! important "Volume expansion is not enabled"
    The generated StorageClass currently advertises
    `allowVolumeExpansion: true`, but the required deployment values disable
    `controller.resizer`. Therefore, PVC expansion is not supported by this
    Omnia deployment. Do not resize a PowerScale-backed PVC unless the resizer
    is enabled and that workflow has been validated for the deployed driver.

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


### Post Installation

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
allowVolumeExpansion: false
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
    - Keep `allowVolumeExpansion: false` while
      `controller.resizer.enabled` is `false` in the deployed driver values.

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


### Uninstallation

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
    The encrypted Orchestrator credential file is the authoritative source for
    `csi_username` and `csi_password`. Updating only the live Kubernetes secret
    leaves the stored input out of sync.

    The current Orchestrator deployment script skips CSI installation when it
    detects existing `isilon` driver pods, so rerunning `provision` does not
    perform an in-place credential rotation. To change the OneFS credentials:

    1. Quiesce PowerScale-backed workloads and plan a maintenance window.
    2. Edit the encrypted credentials on the OIM:

        ```bash title="Run on: OIM"
        source /etc/profile.d/omnia-env.sh
        orchestrator_path="${ORCHESTRATOR_DATA_PATH:-${OMNIA_DATA_PATH}/orchestrator}"
        source "$OMNIA_DATA_PATH/activate-omnia.sh"
        ansible-vault edit \
          "$orchestrator_path/input/$OMNIA_PROJECT_NAME/orchestrator_credentials.yml" \
          --vault-password-file \
          "$orchestrator_path/input/$OMNIA_PROJECT_NAME/.orchestrator_credentials_key"
        ```

       Update `csi_username` and `csi_password`, save the file, and exit the
       editor. Do not place either value on the command line.

    3. Apply the new credentials through an approved CSI maintenance
       procedure. The current Omnia workflow does not automate live rotation:
       `provision` stages updated configuration for future node cloud-init, but
       it does not replace the live `isilon-creds` secret on an already running
       cluster. Either follow the CSI driver's supported live-rotation
       procedure, or uninstall and redeploy the driver during the maintenance
       window. A redeployment that depends on Omnia cloud-init also requires
       the affected control-plane node to be reprovisioned; running the
       `provision` tag alone is insufficient.

    4. Verify the `isilon-creds` secret exists and that the CSI controller and
       node pods return to `Running` before restoring workloads.

## Next steps

- [Set Up Telemetry](../Telemetry/setup_telemetry.md) -- Deploy telemetry
  with PowerScale-backed persistent storage.
- [Configure Mounts](configure_storage.md) -- Configure NFS and other storage mounts for Slurm
  compute nodes.
- [Set Up Kubernetes](deploy_kubernetes.md) -- Review the Kubernetes cluster
  configuration options.


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
