
# local_repo_config.yml Reference


File path: `/opt/omnia/input/project_default/local_repo_config.yml`

This file configures the local repository mirror on the OIM. The `local_repo.yml`
playbook uses these settings to synchronize RHEL, third-party, and custom
package repositories to the OIM via Pulp, enabling air-gapped or
bandwidth-efficient deployments.

## Parameter reference


### General settings


| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `repo_store_path` | String | No | `/opt/omnia/repo_store` | Directory on the OIM where mirrored repositories are stored. Must have sufficient disk space (see [Disk Space](../ClusterRequirements/disk_space.md)). |
| `repo_sync_on_run` | Boolean | No | `true` | Synchronize repositories every time `local_repo.yml` is run. Set to `false` to skip sync and use previously cached content. |

### RHEL repository settings


| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `rhel_os_url` | String | Yes | (none) | URL of the RHEL BaseOS repository to mirror (e.g., `https://cdn.redhat.com/content/dist/rhel/server/10/10.0/x86_64/baseos/os` or a local HTTP mirror). |
| `rhel_appstream_url` | String | Yes | (none) | URL of the RHEL AppStream repository. |
| `rhel_crb_url` | String | No | (none) | URL of the CodeReady Builder repository. Required for build dependencies. |
| `rhel_subscription_username` | String | Conditional | (none) | Red Hat subscription username. Required when mirroring from the Red Hat CDN (`cdn.redhat.com`). Not needed for local mirrors. |
| `rhel_subscription_password` | String | Conditional | (vault-managed) | Red Hat subscription password. Set via `credentials_utility.yml`. |

### Third-party repository settings


| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `epel_url` | String | No | Auto-detected | URL for the Extra Packages for Enterprise Linux (EPEL) repository. |
| `nvidia_gpu_repo_url` | String | No | (none) | URL for the NVIDIA CUDA repository. Required when deploying NVIDIA GPU drivers. |
| `amd_gpu_repo_url` | String | No | (none) | URL for the AMD ROCm repository. Required when deploying AMD GPU drivers. |
| `docker_repo_url` | String | No | (none) | URL for the Docker CE repository (used by K8s container runtime if applicable). |
| `kubernetes_repo_url` | String | No | (none) | URL for the Kubernetes package repository. |
| `beegfs_repo_url` | String | No | (none) | URL for the BeeGFS package repository. |

### Custom repositories


| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `custom_repos` | List | No | `[]` | List of additional repository definitions to mirror. |
| `custom_repos[].name` | String | Yes | (none) | Repository identifier (e.g., `my-internal-repo`). |
| `custom_repos[].url` | String | Yes | (none) | Repository base URL. |
| `custom_repos[].gpgcheck` | Boolean | No | `true` | Whether to verify GPG signatures for packages in this repository. |
| `custom_repos[].gpgkey` | String | No | (none) | URL or local path to the GPG public key for signature verification. |

## Usage example


```yaml title="File: /opt/omnia/input/project_default/local_repo_config.yml"
repo_store_path: "/opt/omnia/repo_store"
repo_sync_on_run: true

rhel_os_url: "http://mirror.example.com/rhel/10.0/x86_64/baseos/"
rhel_appstream_url: "http://mirror.example.com/rhel/10.0/x86_64/appstream/"
rhel_crb_url: "http://mirror.example.com/rhel/10.0/x86_64/crb/"

nvidia_gpu_repo_url: "https://developer.download.nvidia.com/compute/cuda/repos/rhel10/x86_64/"
kubernetes_repo_url: "https://pkgs.k8s.io/core:/stable:/v1.29/rpm/"

custom_repos:
  - name: "internal-tools"
    url: "http://repo.internal.example.com/tools/"
    gpgcheck: false
```


!!! info

    - [Playbook Reference](../Playbooks/playbook_reference.md) -- The `local_repo.yml`
      playbook.
    - [Disk Space](../ClusterRequirements/disk_space.md) -- Disk space for the
      repository mirror.
    - [Software Config](software_config.md) -- Which packages are selected for installation.
