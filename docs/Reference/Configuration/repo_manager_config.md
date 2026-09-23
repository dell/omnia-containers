# repo_manager_config.yml

This file defines Repository Manager synchronization policy, RPM repository mappings,
and optional container registry endpoints.

## Location

```text
$OMNIA_DATA_PATH/repo_manager/input/$OMNIA_PROJECT_NAME/repo_manager_config.yml
```

The default location is
`/opt/omnia/repo_manager/input/project_default/repo_manager_config.yml`.

## Top-level parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `catalog_config` | object | No | Compatibility catalog reference used only when `CATALOG_FILE_PATH` is unset. |
| `repo_config` | string | Yes | Global RPM policy: `always` or `partial`. |
| `caching_policy` | boolean | No | Global Pulp caching behavior. The source value is `true`. |
| `standard` | boolean | No | Selects standard-only subscription repositories when `true`; defaults to EUS-first resolution with standard fallback. The default is `false`. |
| `repositories` | object | Yes | Repository definitions organized by OS version and architecture. |
| `registries` | object or null | No | Container registries keyed by registry name. |

Unknown top-level and nested properties are rejected.

## Catalog selection compatibility

`CATALOG_FILE_PATH` is the preferred catalog-selection interface and takes
precedence when it is populated. The optional `catalog_config` object is a
compatibility fallback:

```yaml
catalog_config:
  catalog: catalog_rhel.json
```

The `catalog` child is required when `catalog_config` is supplied. An absolute
path is used directly; a relative path is resolved from the directory that
contains `repo_manager_config.yml`. Catalog resolution fails when neither
`CATALOG_FILE_PATH` nor `catalog_config.catalog` supplies a value.

## Repository entries

Each version can contain `x86_64` and `aarch64` mappings. A repository entry
supports the following fields:

| Field | Type | Values or constraint |
|---|---|---|
| `url` | string or null | Repository URL; may be empty for subscription-provided RHEL repositories. |
| `gpgkey` | string or null | GPG key URL. |
| `policy` | string | `always`, `partial`, or `never`. |
| `caching` | boolean | Per-repository caching override. |
| `standard` | boolean | Per-repository override for standard-only versus EUS-first subscription discovery. |
| `priority` | integer | DNF priority from 1 through 100. |
| `sslcacert` | string or null | CA certificate path. |
| `sslclientkey` | string or null | mTLS client-key path. |
| `sslclientcert` | string or null | mTLS client-certificate path. |

`user_repos` and `additional_repos` contain named repository entries using the
same fields. Repository names may contain letters, numbers, underscores,
periods, and hyphens.

### Subscription channel selection

The effective subscription channel is selected in this order:

1. A nonempty repository `url` takes precedence over subscription discovery.
2. A repository-level `standard` value overrides the global `standard` value.
3. The global `standard` value applies when no repository override exists.
4. `standard: false` prefers EUS and falls back to the standard channel.
5. `standard: true` accepts only the standard channel.

### Additional repositories

Place `additional_repos` below the applicable operating-system version and
architecture. Packages in the selected catalog must reference the same
repository names. Repository Manager publishes all selected `additional_repos` for
one architecture through one aggregated Pulp repository, so they must resolve
to one effective priority. For this comparison, an omitted `priority` is
treated as `99`. In contrast, repositories under `user_repos` remain
independent and may use different priorities.

```yaml
repositories:
  "10.0":
    x86_64:
      additional_repos:
        rhel-10-for-x86_64-highavailability-rpms:
          url: ""
          standard: true
          policy: partial
          caching: true
          priority: 99
        internal_tools:
          url: "https://repo.example.com/internal-tools/"
          policy: partial
          caching: true
          priority: 99
```

## Registry entries

A registry requires `base_url`, `port`, and `auth`. `auth.type` is `none` or
`basic`. Basic authentication also requires
`auth.credentials.vault_path`, which selects an entry from the encrypted Repo
Manager credential file. The optional `tls` mapping supports `ca_path`,
`client_cert_path`, `client_key_path`, and `insecure`.

A catalog image source that uses the `registry` field must have a `name` that
starts with the configured registry authority, i.e. `<host>[:<port>]/<image_path>`.

## Usage example

```yaml title="File: /opt/omnia/repo_manager/input/project_default/repo_manager_config.yml"
repo_config: "partial"
caching_policy: true
standard: false

registries:

repositories:
  "10.0":
    x86_64:
      baseos: {}
      appstream:
        standard: true
      codeready-builder: {}
      epel:
        url: "https://dl.fedoraproject.org/pub/epel/10/Everything/x86_64/"
        gpgkey: "https://dl.fedoraproject.org/pub/epel/RPM-GPG-KEY-EPEL-10"
        policy: "partial"
        caching: true
        priority: 99
      additional_repos:
        internal_tools:
          url: "https://repo.example.com/internal-tools/"
          policy: "partial"
          caching: true
          priority: 99
```

Credentials are collected by the Repository Manager credential workflow and stored
in `repo_manager_config_credentials.yml` with the matching
`.repo_manager_config_credentials_key`; do not place passwords in this file.

## Related configuration

- [Repository Manager endpoint](repo_manager_endpoint_config.md)
- [Repository Manager contract](../domain_contracts/repo_manager_contract.md)
