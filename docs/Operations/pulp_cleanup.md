
# Cleanup Local Pulp Repositories


The `pulp_cleanup.yml` playbook removes unused content from the Pulp container
to free up disk space. This includes RPM repositories, files (tarball, git, pip,
manifest), and container images. Active repositories and their associated
content are preserved during the cleanup process.

## When to Use Pulp Cleanup


- Disk space on the NFS share or OIM is running low due to accumulated
  repository content.
- Old or unused RPM repositories, files, or container images need to be removed.
- You want to clean up artifacts from a previous deployment before starting fresh.

!!! danger

    `pulp_cleanup.yml` permanently removes the specified content from the Pulp
    container. This operation cannot be reversed. If deleted artifacts are
    required by any software, you must rerun `local_repo.yml` to sync them
    again. Subsequent playbooks with dependencies on missing artifacts may fail.

## Prerequisites


- You are logged in to the `omnia_core` container.
- The Pulp container is running and accessible.
- You have identified the specific repositories, files, or container images
  to clean up (or intend to clean all content).

## Tasks Performed by the Playbook


The `pulp_cleanup.yml` playbook performs the following tasks:

- Removes specified RPM repositories from the Pulp container.
- Removes specified files (tarball, git, pip, manifest) from the Pulp container.
- Removes specified container images from the Pulp container.
- Preserves active repositories and their associated content.


## Steps


1. Enter the `omnia_core` container:

   ```bash title="Run on: OIM host"
   ssh omnia_core
   ```

2. Navigate to the local repo directory:

   ```bash title="Run on: omnia_core container"
   cd /omnia/local_repo
   ```

3. Run one of the following cleanup commands based on your requirement:

   Cleanup a specific RPM repository:

   ```bash title="Run on: omnia_core container"
   ansible-playbook pulp_cleanup.yml -e cleanup_repos=x86_64_rhel_10.0_appstream
   ```

   Cleanup a specific file:

   ```bash title="Run on: omnia_core container"
   ansible-playbook pulp_cleanup.yml -e cleanup_files=calico-v3.30.3
   ```

   Cleanup a specific container image (force cleanup):

   ```bash title="Run on: omnia_core container"
   ansible-playbook pulp_cleanup.yml -e cleanup_containers=docker.io/library/busybox -e force=true
   ```

   Cleanup all content:

   ```bash title="Run on: omnia_core container"
   ansible-playbook pulp_cleanup.yml -e cleanup_repos=all -e cleanup_files=all -e cleanup_containers=all
   ```

!!! warning

    The `force=true` option forces the cleanup operation to proceed even if the
    repository or content is currently referenced by older metadata or
    publications. Use this option with caution, as the cleanup process
    permanently removes the specified content and cannot be reversed.

## Logs


Cleanup logs are generated in a version-aware directory structure under
`/opt/omnia/log/local_repo/`.

```
/opt/omnia/log/local_repo/
└── rhel/
    ├── 10.0/cleanup/
    │   ├── standard.log
    │   └── cleanup_status.csv
    └── 10.1/cleanup/
        ├── standard.log
        └── cleanup_status.csv
```

- `standard.log` -- Contains detailed execution logs of the cleanup operation.
- `cleanup_status.csv` -- Provides a summary of cleanup actions and their status.
