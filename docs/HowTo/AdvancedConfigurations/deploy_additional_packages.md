
# Deploy Additional Packages


This section explains how to download and deploy additional software packages
and container images on the cluster nodes using Omnia local repositories.


## Overview


Omnia supports deploying additional packages and container images at two
stages:

1. **During first-time deployment** -- Packages are included in the cluster
   node images before provisioning.
2. **After cluster provisioning** -- Packages are added to running nodes
   post-deployment.

For adding extra RPM repositories (not individual packages), see
[Deploy Additional Repositories](deploy_additional_repos.md).


## Prerequisites


Configure additional container images from a user registry to the local
repository. Omnia supports configuring additional container images from
specified user registries to the Omnia Local Repository, so that these images
are available and can be pulled by Service Kubernetes Cluster nodes as per
requirement. User registries may be hosted either on OIM or on an external
server, and both HTTP and HTTPS registries are supported.

- To view the steps to set up an HTTP user registry, see
  [Set Up an HTTP User Registry](../../html/setup_http_user_registry.html).
- To view the steps to set up an HTTPS user registry, see
  [Set Up an HTTPS User Registry](../../html/setup_https_user_registry.html).

After the registry is ready, mention the inputs in `local_repo_config.yml`.
See [Local Repo Config](../../Reference/Configuration/local_repo_config.md).


## Steps


### Step 1: Add additional_packages to software_config.json

Open `/opt/omnia/input/project_default/software_config.json` and add the
`additional_packages` entry under the `softwares` list. Also define the
`additional_packages` section to specify which node roles should receive the
additional packages.Save the `software_config.json` file.

Sample `software_config.json` with `additional_packages` enabled:

```json
{
  "cluster_os_type": "rhel",
  "cluster_os_version": "10.0",
  "repo_config": "partial",
  "softwares": [
    {"name": "default_packages", "arch": ["x86_64","aarch64"]},
    {"name": "additional_packages", "arch": ["x86_64","aarch64"]}
  ],
  "additional_packages": [
    {"name": "slurm_control_node"},
    {"name": "slurm_node"},
    {"name": "login_node"},
    {"name": "login_compiler_node"},
    {"name": "service_kube_control_plane"},
    {"name": "service_kube_node"},
    {"name": "os"}
  ]
}
```

!!! note

    - Ensure the `arch` list matches your cluster architecture(s).
    - To install debug packages, also add:
      `{"name": "admin_debug_packages", "arch": ["x86_64", "aarch64"]}`


### Step 2: Configure additional_packages.json

Update the `additional_packages.json` file at
`/opt/omnia/input/project_default/config/<architecture>/rhel/10.0/` with the
required packages and images.Save the `additional_packages.json` file.

Each entry needs:

- For **RPM packages**: `package`, `type: "rpm"`, and `repo_name`
- For **container images**: `package`, `type: "image"`, and `tag` or `digest`

Sample `additional_packages.json`:

```json
{
  "additional_packages": {
    "cluster": [
      {
        "package": "fuse-overlayfs",
        "type": "rpm",
        "repo_name": "appstream"
      },
      {
        "package": "sssd",
        "type": "rpm",
        "repo_name": "baseos"
      },
      {
        "package": "quay.io/strimzi/kafka-bridge",
        "type": "image",
        "tag": "0.33.1"
      },
      {
        "package": "172.16.0.254:7000/ubuntu/squid",
        "type": "image",
        "tag": "latest"
      }
    ]
  },
  "os": {
    "cluster": [
      {
        "package": "podman",
        "type": "rpm",
        "repo_name": "appstream"
      },
      {
        "package": "curl",
        "type": "rpm",
        "repo_name": "baseos"
      }
    ]
  }
}
```

!!! note

    All container images specified in `additional_packages.json` are
    configured in the Omnia local repository and can be pulled on all Service
    Kubernetes Cluster nodes.


### Architecture-Specific Guidelines

The `additional_packages` feature has architecture-specific functional group
support:

- **x86_64**: `slurm_control_node`, `slurm_node`, `login_node`,
  `login_compiler_node`, `service_kube_control_plane`,
  `service_kube_control_plane_first`, `service_kube_node`, `os`
- **aarch64**: `slurm_node`, `login_node`, `login_compiler_node`, `os`

Architecture-specific JSON files are located at:

- `/opt/omnia/input/<project_name>/config/x86_64/rhel/<version>/additional_packages.json`
- `/opt/omnia/input/<project_name>/config/aarch64/rhel/<version>/additional_packages.json`

!!! warning

    - Kubernetes-related groups (`service_kube_*`) and `slurm_control_node`
      are **only** supported on x86_64.
    - Include only supported functional groups for each architecture.
    - Review validation logs at
      `/opt/omnia/log/core/playbooks/validation_omnia_<project_name>.log`
      for warnings.


## Deploy Additional Packages During First-Time Deployment


1. Configure `software_config.json` and `additional_packages.json` as
   described above.

2. After the local repositories are created, build the cluster node images
   and PXE boot the nodes using the images:

   - **Build images**: [Build Cluster Images](../Setup/build_cluster_images.md)
   - **Discover nodes and PXE boot**: [Discover Nodes](../Setup/discover_nodes.md)


## Deploy Additional Packages After Cluster Provisioning


1. Configure `software_config.json` and `additional_packages.json` as
   described above.

2. Re-run the `local_repo.yml` playbook to download the new packages/images
   to the Pulp container.

3. After the local repositories are updated:

   - **Install RPM packages** on the required nodes:

      ```bash title="Run on: compute node"
      dnf install <package-name>
      ```

   - **Pull container images** on the required nodes (see
     [Pulling images from a user registry via Pulp](#pulling-images-from-a-user-registry-via-pulp-on-a-service-kubernetes-cluster)
     below).

   - **Verify** the installed packages/images:

      ```bash title="Run on: compute node"
      dnf list installed <package-name>
      crictl images
      ```


### Pulling Images from a User Registry via Pulp on a Service Kubernetes Cluster


When the container images from a user registry are specified in the
`additional_packages.json`, running `local_repo.yml` thereafter uploads those
images to the configured Pulp registry.

After this synchronization:

- All cluster nodes must pull images from Pulp, not directly from the user registry.
- This enables centralized image management and supports offline or air-gapped
  environments.

**Example:** Image defined in `additional_packages.json`:

```json
"additional_packages": {
  "cluster": [
    {
      "package": "100.10.0.76:3445/library/nginx",
      "type": "image",
      "tag": "1.25.2-alpine-slim"
    }
  ]
}
```

In this example, `100.10.0.76:3445` is the user registry. Omnia syncs the
image to the Pulp registry. Cluster nodes must subsequently pull the image
from Pulp.

#### Retrieve the Pulp Registry Endpoint

On the Omnia Core container, run:

```bash title="Run on: omnia_core container"
pulp status | jq -r '.content_settings.content_origin'
```

Sample output: `https://172.16.255.254:2225`

Remove the `https://` prefix and use only `172.16.255.254:2225`.

#### Configure Compute Nodes to Pull from Pulp

On each Kubernetes compute node:

1. Edit the CRI-O configuration file:

   ```bash title="Run on: compute node"
   vi /etc/containers/registries.conf.d/crio.conf
   ```

2. Append this configuration at the end of the file:

   ```toml
   [[registry]]
   prefix = "100.10.0.76:3445"
   location = "100.10.0.76:3445"

   [[registry.mirror]]
   location = "172.16.255.254:2225"
   ```

3. Reload and restart CRI-O:

   ```bash title="Run on: compute node"
   systemctl daemon-reload
   systemctl restart crio
   ```

#### Pull the Image

Pull the image using the original registry reference (CRI-O transparently
redirects to Pulp):

```bash title="Run on: compute node"
crictl pull 100.10.0.76:3445/library/nginx:1.25.2-alpine-slim
```

The image will be retrieved from the Pulp mirror automatically.


## Next Steps


- [Deploy Additional Repositories](deploy_additional_repos.md) -- Add extra RPM repositories for ad-hoc package installation.
- [Apptainer](use_apptainer.md) -- Pull and run container images using Apptainer.
