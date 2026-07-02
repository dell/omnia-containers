# local_repo_config.yml Reference

File path: `/opt/omnia/input/project_default/local_repo_config.yml`

This file configures the local repository mirror on the OIM. The `local_repo.yml`
playbook uses these settings to synchronize RHEL, third-party, and custom
package repositories to the OIM via Pulp, enabling air-gapped or
bandwidth-efficient deployments.

## Local Repo configuration parameters

--8<-- "html/local_repo_config.html"

## Usage example
```yaml title="File: /opt/omnia/input/project_default/local_repo_config.yml"
---
user_registry:  

user_repo_url_x86_64:
user_repo_url_aarch64:

rhel_os_url_x86_64:
rhel_os_url_aarch64:

rhel_subscription_repo_config_x86_64:
 - { url: "https://cdn.redhat.com/content/dist/rhel10/10.0/x86_64/baseos/os/", name: "baseos" }
 - { url: "https://cdn.redhat.com/content/dist/rhel10/10.0/x86_64/appstream/os/", name: "appstream", policy: "always" }
 - { url: "https://cdn.redhat.com/content/dist/rhel10/10.0/x86_64/supplementary/os/", name: "supplementary", policy: "always", caching: false }

rhel_subscription_repo_config_aarch64:

omnia_repo_url_rhel_x86_64:
  - { url: "https://download.docker.com/linux/centos/10/x86_64/stable/", gpgkey: "https://download.docker.com/linux/centos/gpg", name: "docker-ce"}
  - { url: "https://dl.fedoraproject.org/pub/epel/10/Everything/x86_64/", gpgkey: "https://dl.fedoraproject.org/pub/epel/RPM-GPG-KEY-EPEL-10", name: "epel"}
  - { url: "https://pkgs.k8s.io/core:/stable:/v1.35/rpm/", gpgkey: "https://pkgs.k8s.io/core:/stable:/v1.35/rpm/repodata/repomd.xml.key", name: "kubernetes-v1-35"}
  - { url: "https://download.opensuse.org/repositories/isv:/cri-o:/stable:/v1.35/rpm/", gpgkey: "https://download.opensuse.org/repositories/isv:/cri-o:/stable:/v1.35/rpm/repodata/repomd.xml.key", name: "cri-o-v1-35"}
  - { url: "https://linux.mellanox.com/public/repo/doca/3.2.1/rhel10/x86_64/", gpgkey: "https://linux.mellanox.com/public/repo/doca/3.2.1/rhel10/x86_64/repodata/repomd.xml.key", name: "doca"}
  - { url: "https://developer.download.nvidia.com/compute/cuda/repos/rhel10/x86_64/", gpgkey: "https://developer.download.nvidia.com/compute/cuda/repos/rhel10/x86_64/repodata/repomd.xml.key", name: "cuda"}
  - { url: "https://developer.download.nvidia.com/hpc-sdk/rhel/x86_64", gpgkey: "https://developer.download.nvidia.com/hpc-sdk/rhel/RPM-GPG-KEY-NVIDIA-HPC-SDK", name: "nvidia-hpc-sdk"}
omnia_repo_url_rhel_aarch64:
  - { url: "https://download.docker.com/linux/centos/10/aarch64/stable/", gpgkey: "https://download.docker.com/linux/centos/gpg", name: "docker-ce"}
  - { url: "https://dl.fedoraproject.org/pub/epel/10/Everything/aarch64/", gpgkey: "https://dl.fedoraproject.org/pub/epel/RPM-GPG-KEY-EPEL-10", name: "epel"}
  - { url: "https://linux.mellanox.com/public/repo/doca/3.2.1/rhel10/arm64-sbsa/", gpgkey: "https://linux.mellanox.com/public/repo/doca/3.2.1/rhel10/arm64-sbsa/repodata/repomd.xml.key", name: "doca"}
  - { url: "https://developer.download.nvidia.com/compute/cuda/repos/rhel10/sbsa/", gpgkey: "https://developer.download.nvidia.com/compute/cuda/repos/rhel10/sbsa/repodata/repomd.xml.key", name: "cuda"}
  - { url: "https://developer.download.nvidia.com/hpc-sdk/rhel/aarch64", gpgkey: "https://developer.download.nvidia.com/hpc-sdk/rhel/RPM-GPG-KEY-NVIDIA-HPC-SDK", name: "nvidia-hpc-sdk"}

additional_repos_x86_64:
additional_repos_aarch64:
```


!!! info

    - [Playbook Reference](../Playbooks/playbook_reference.md) -- The `local_repo.yml`
      playbook.
    - [Disk Space](../ClusterRequirements/disk_space.md) -- Disk space for the
      repository mirror.
    - [Software Config](software_config.md) -- Which packages are selected for installation.
