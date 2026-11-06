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
| `catalog_config` | object | No | Accepted for backward compatibility only (see [Catalog selection](#catalog-selection)). It does not select the catalog at runtime; `CATALOG_FILE_PATH` is always required. If this object is present, `catalog` must be a non-empty string. |
| `repo_config` | string | Yes | Global RPM policy: `always` or `partial`. |
| `caching_policy` | boolean | No | Global Pulp caching behavior. The source value is `true`. |
| `standard` | boolean | No | Selects standard-only subscription repositories when `true`; defaults to EUS-first resolution with standard fallback. The default is `false`. |
| `repositories` | object | Yes | Repository definitions organized by OS version and architecture. |
| `registries` | object or null | No | Container registries keyed by registry name. |

Unknown top-level and nested properties are rejected.

## Catalog selection

Repository Manager always selects the catalog through the `CATALOG_FILE_PATH`
environment variable. Set it to the absolute path of an existing catalog file
that ends in `.json` before you run Repository Manager. If `CATALOG_FILE_PATH`
is not set, the environment precheck stops the run with an error.

The optional `catalog_config` object is accepted by the schema for backward
compatibility only:

```yaml
catalog_config:
  catalog: catalog_rhel.json
```

If you supply `catalog_config`, the `catalog` child is required and must not be
empty. Repository Manager does not use this value to select the catalog, and
it does not replace `CATALOG_FILE_PATH`. Omit `catalog_config` unless you must
keep an existing file unchanged. For information about setting
`CATALOG_FILE_PATH`, see
[Select or update the catalog](../../HowTo/main/update_catalog.md).

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

Repository Manager evaluates only the OS-version, architecture, and repository
combinations referenced by the active catalog. For a multi-version catalog,
provide a matching section under `repositories` for every selected version.
The channel-selection algorithm does not establish that an EUS channel exists
or is supported for every RHEL minor version.

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
  "10.2":
    x86_64:
      baseos:
        standard: true
      appstream:
        standard: true
      codeready-builder:
        standard: true
      epel:
        url: "https://dl.fedoraproject.org/pub/epel/10/Everything/x86_64/"
        gpgkey: "https://dl.fedoraproject.org/pub/epel/RPM-GPG-KEY-EPEL-10"
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
