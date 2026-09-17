# Configure Catalog Content

## Overview

Repository Manager uses the external catalog selected by `CATALOG_FILE_PATH`
to determine which content must be available. The catalog is not staged by
`domain-init.sh`. Its root `catalog` object contains catalog metadata and three
connected collections:

For selecting the deployment catalog and configuring `CATALOG_FILE_PATH`, see
[Select or update the catalog](../main/update_catalog.md).

Repository Manager synchronizes catalog-selected content into Pulp and
publishes it through `repo_status.yml`. It does not install packages on cluster
nodes. Image Build Manager consumes the successful Repository Manager contract
when it builds images.

- `functionallayer` defines the functional roles used to build images. Each
  functional layer lists group keys in `components`.
- `groups` organizes related content. Each group lists package keys in
  `components`.
- `packages` defines the content to obtain. Each package specifies its `name`,
  `packagetype`, and one or more `sources`; a container image also specifies a
  `tag`.

The `components` values connect these collections by name. The following
abbreviated example shows how Repository Manager follows the catalog hierarchy
and resolves a selected package source:

```text
catalog
|-- name / version / identifier / description
|-- functionallayer
|   `-- slurm_control_node_rhel_10_0_x86_64
|       `-- components: baseos_group_10.0
|-- groups
|   `-- baseos_group_10.0
|       `-- components: systemd
`-- packages
    `-- systemd
        |-- packagetype: rpm
        `-- source: name=rhel, version=[10.0], architecture=x86_64, reponame=baseos
```

In this example, the Slurm control-node functional layer references
`baseos_group_10.0`, which references the `systemd` RPM package that Repository
Manager resolves for RHEL 10.0 on `x86_64`.

Use the `catalog_add` operation to add or update RPM packages, RPM repository
packages, tarballs, container images, Git repositories, manifest files, or
pip modules. The operation uses upsert semantics: it creates missing groups,
updates existing package definitions, and avoids duplicate component
references.

## Prerequisites

- Create and synchronize the local repositories as described in
  [Create Local Repositories](configure_repos.md).
- Set the required `SYSTEM_ADMIN_NIC_IPV4` environment variable and follow
  [Select or update the catalog](../main/update_catalog.md) to configure
  `CATALOG_FILE_PATH`.
- Edit `repo_manager_config.yml` and `repo_manager_endpoint_config.yml` in
  `$OMNIA_DATA_PATH/repo_manager/input/$OMNIA_PROJECT_NAME/`
  (default `/opt/omnia/repo_manager/input/project_default/`). If the staged
  files do not exist, run `domain-init.sh` from `src/repo_manager/` first.
- Identify the existing catalog functional layer and group that should own the
  package.
- Ensure each referenced RPM repository resolves under the matching catalog
  minor version and architecture. Without subscription access, every
  referenced RPM repository requires an explicit non-empty URL.
- Have credentials available for Docker Hub and private registries when
  required. These credentials are collected into the encrypted project
  credential file rather than stored in the catalog or normal configuration
  files.

## Procedure

1. Create an INI-like additions file. The following example adds RPM packages, a
   tarball, a container image, a Git repository, a manifest, and a pip module,
   and references each group in an existing functional layer:

    ~~~ini
    [defaults]
    arch=x86_64, os=rhel, os_version=10.0

    [openldap_group | description=OpenLDAP packages]
    openldap, rpm, openldap, baseos
    openldap_clients, rpm, openldap-clients, baseos

    [custom_tarball_group | description=Custom tarball artifacts]
    helm_amd64, tarball, helm-v3.17.3-linux-amd64, https://get.helm.sh/helm-v3.17.3-linux-amd64.tar.gz

    [custom_container_group | description=Custom container images]
    docker.io/library/alpine, image, docker.io/library/alpine, docker.io, 3.21
    ubuntu_2204, image, <registry_host>:443/library/ubuntu, private_registry, 22.04

    [custom_git_group | description=Custom Git repositories]
    external_snapshotter, git, external-snapshotter, https://github.com/kubernetes-csi/external-snapshotter.git, v8.5.0

    [custom_manifest_group | description=Custom manifest files]
    calico_manifest, manifest, calico-manifest, https://raw.githubusercontent.com/projectcalico/calico/v3.32.1/manifests/calico.yaml

    [custom_pip_group | description=Custom pip modules]
    prettytable==3_12_0, pip_module, prettytable==3.12.0

    [slurm_control_node_rhel_10_0_x86_64 | type=functional_layer]
    "openldap_group"
    "custom_tarball_group"
    "custom_container_group"
    "custom_git_group"
    "custom_manifest_group"
    "custom_pip_group"
    ~~~

    Replace `slurm_control_node_rhel_10_0_x86_64` with the exact existing
    functional-layer name from your catalog.

    Supported input-line formats for `catalog_add` are:

    | Content | Format |
    |---|---|
    | RPM | `key, rpm, package_name, reponame` |
    | RPM repository | `key, rpm_repo, package_name, reponame` |
    | Tarball | `key, tarball, artifact_name, https_url` |
    | Container image | `key, image, registry/image_path, registry, tag` |
    | Git repository | `key, git, package_name, url, version` |
    | Manifest | `key, manifest, package_name, url` |
    | Pip module | `key, pip_module, package_name` |

    Each line is comma-separated. The fields are:

    - `key` — the package identifier in the catalog.
    - `type` — `rpm`, `rpm_repo`, `tarball`, `image`, `git`, `manifest`, or
      `pip_module`.
    - RPM / RPM repository: `package_name` is the RPM name and `reponame` is
      the catalog source repository key.
    - Tarball: `artifact_name` is the artifact key and `https_url` is the
      download URL.
    - Container image: `registry/image_path` is the full image reference,
      `registry` is the registry key, and `tag` is the image tag. Known
      public registries (`docker.io`, `ghcr.io`, `quay.io`, `registry.k8s.io`)
      do not require an entry in `repo_manager_config.yml`. Private registries
      must be configured under `registries` in `repo_manager_config.yml`.
      Each `key` must be unique. When adding the same image with multiple
      tags, use a distinct key for each tag (e.g. `ubuntu_22_04` and
      `ubuntu_24_04` for two tags of the same image).
    - Git repository: `package_name` is the repository identifier, `url` is
      the Git clone URL, and `version` is the branch or tag to clone.
    - Manifest: `package_name` is the manifest identifier and `url` is the
      download URL.
    - Pip module: `package_name` is the Python package name with version pin
      (e.g. `prettytable==3.12.0`). The `key` uses underscores in place of dots
      (e.g. `prettytable==3_12_0`). The source `name` defaults to the `os` value
      from `[defaults]`; set `os=pypi` in `[defaults]` or use a trailing
      `os=pypi` override if the catalog uses `pypi` as the source name.

    A line can end with `arch=`, `os=`, or `os_version=` overrides.

2. Add the entries to the configured catalog:

    ~~~bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/repo_manager/playbooks
    ansible-playbook repo_manager.yml --tags catalog_add \
      -e "input_file=/absolute/path/to/additions.txt"
    ~~~

    By default, the command reads and writes the catalog selected by
    `CATALOG_FILE_PATH` and validates the result. Use `catalog_input` and
    `output_file` extra variables when the change must be reviewed in a
    separate output file.

3. Validate the selected catalog and its source mappings:

    ~~~bash title="Run on: OIM host"
    ansible-playbook repo_manager.yml --tags catalog_validate
    ansible-playbook repo_manager.yml --tags precheck
    ~~~

4. Synchronize the changed catalog and regenerate the consumer contract:

    ~~~bash title="Run on: OIM host"
    ansible-playbook repo_manager.yml --tags "download,status"
    ~~~

For RPM packages, the catalog source resolves to the matching repository in
`repo_manager_config.yml`:

```text
source version + architecture + reponame
  → repositories.<version>.<architecture>.<reponame>
```

The catalog example for `systemd` resolves against this repository entry:

```yaml
repositories:
  "10.0":
    x86_64:
      baseos:
        url: ""  # Subscription-provided; otherwise an explicit URL is required.
        policy: "partial"
```

The `systemd` source uses `version=[10.0]`, `architecture=x86_64`, and
`reponame=baseos`, so Repository Manager resolves it to
`repositories."10.0".x86_64.baseos`.

Repository names may be defined directly under the architecture or inside its
`user_repos` section. Repository Manager resolves both locations as one lookup
map while preserving their runtime behavior. For the
detailed repository procedure, see
[Add an RPM Repository and Packages](adding_additional_repositories.md).

## Verification

Check that the new package is present in the catalog, then review its group
status:

~~~bash title="Run on: OIM host"
python3 -m json.tool "$CATALOG_FILE_PATH"
sed -n '1,240p' \
  /opt/omnia/repo_manager/output/project_default/repo_status.yml
~~~

Per-package results are written to
`<REPO_MANAGER_DATA_PATH>/log/<os>/<version>/<architecture>/<group>/status.csv`.
Also review
`<REPO_MANAGER_DATA_PATH>/log/<os>/<version>/<architecture>/groups_status.csv`
and the corresponding Pulp repository, publication, and distribution state.
Confirm that the added entries report `Success` and that `repo_status.yml` has
`overall_status: success`. A required missing distribution produces a failed
status instead of publishing an unusable URL.

## Removing packages from the catalog

Use `catalog_delete` to remove package references from the catalog. The
delete input file lists package keys under their group headers:

~~~ini
[openldap_group]
openldap
openldap_clients

[custom_tarball_group]
helm_amd64

[custom_container_group]
docker.io/library/alpine
ubuntu_2204

[custom_git_group]
external_snapshotter

[custom_manifest_group]
calico_manifest

[custom_pip_group]
prettytable==3_12_0
~~~

Each `[group_key]` must match an existing group in the catalog. Package keys
listed under the group are removed from that group's components. A package
object is deleted from the catalog only when no other group references it. If
all packages are removed from a group, the group itself is removed and its
reference is deleted from any functional layer.

Run the delete operation:

~~~bash title="Run on: OIM host"
cd <OMNIA_SOURCE_PATH>/src/repo_manager/playbooks
ansible-playbook repo_manager.yml --tags catalog_delete \
  -e "input_file=/absolute/path/to/deletions.txt"
~~~

Validate the catalog after deletion and resynchronize:

~~~bash title="Run on: OIM host"
ansible-playbook repo_manager.yml --tags catalog_validate
ansible-playbook repo_manager.yml --tags "download,status"
~~~

## Next steps

- [Build Cluster Images](../image_build_manager/build_images.md).
- [Add a repository mapping](adding_additional_repositories.md) for a new RPM
  source.
- [Update Local Repositories](../../Operations/repo_manager/updating_local_repositories.md)
  after changing an existing catalog definition.
- Run the standard `prepare,precheck,download,status` workflow to publish the
  verified `repo_status.yml` for downstream consumers.

## Troubleshooting

- **The additions file fails to parse**: Use one supported positional format,
  put package lines below a group header, and put group references below a
  `type=functional_layer` header.
- **The updated catalog fails validation**: Check that all group and package
  references exist.
- **An RPM mapping is missing**: Match the source version, architecture, and
  `reponame` in `repo_manager_config.yml`.
- **A private registry mapping is missing**: Match the catalog source
  `registry` exactly to a key under `registries`, and ensure that the image
  name starts with the configured registry host and optional port.
- **An `rpm_repo` entry is rejected**: Its repository must retain content;
  change the effective policy so it does not resolve to `streamed`.
- **A source is not selected**: Provide a source for the active OS version and
  architecture, or use a supported `noarch` source.
- **The package is not processed**: Ensure its group is referenced by a
  selected functional layer. Orphan groups and packages are not selected.
- **A Repository Manager run fails**: Locate the failed OS, version,
  architecture, and group. Review `standard.log`, `groups_status.csv`, the
  corresponding `status.csv`, and the package-status log. Correct the
  configuration, source, or runtime issue, then rerun `precheck`, `download`,
  and `status`.
- **Status does not reflect the expected result**: Do not edit mirror indexes,
  status CSV files, or execution summaries to force success. Use the earliest
  detailed repository or package log to identify the actionable cause.
