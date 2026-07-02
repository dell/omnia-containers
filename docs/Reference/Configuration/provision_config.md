
# provision_config.yml Reference


File path: `/opt/omnia/input/project_default/provision_config.yml`

This file controls the provisioning behavior of the OIM, including PXE boot
mapping, domain name, and OS image settings.

## Parameter reference

--8<-- "html/provision_config.html"

## Usage example


```yaml title="File: /opt/omnia/input/project_default/provision_config.yml"
---
pxe_mapping_file_path: "/opt/omnia/input/project_default/pxe_mapping_file.csv"
language: "en_US.UTF-8"
default_lease_time: "86400"
dns_enabled: false
kernel_version_override: ""
additional_cloud_init_config_file: ""
```


!!! note

    The `provision_password` parameter is prompted during runtime. It is stored
    in an Ansible vault and is never written to `provision_config.yml` in plain text.

!!! info

    - [PXE Mapping File](../SampleFiles/pxe_mapping_file.md) -- PXE mapping CSV format.
    - [Timezones](../Appendices/timezones.md) -- Valid timezone values.
    - [Network Spec](network_spec.md) -- Network configuration that complements provisioning.
