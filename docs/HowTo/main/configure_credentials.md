
# Provide Required Credentials for Omnia

## Overview

Omnia provides an additional utility playbook called `get_config_credentials.yml`. When executed, this playbook creates an input file called `omnia_config_credentials.yml` in the `/opt/omnia/input/project_default` folder. Additionally, the `build_stream_oauth_credentials.yml` file is created in the same folder only when the `enable_build_stream` parameter is set to `true` in the `/opt/omnia/input/project_default/build_stream_config.yml` input file.
In these input files, you can preemptively provide all types of mandatory and optional credentials required by Omnia during its execution. Otherwise, you'll be prompted to enter them during playbook execution.


## Prerequisites


- Ensure that the `omnia_core` container is up and running.
- Ensure that the `/opt/omnia/input/project_default/software_config.json` file is updated with the packages that you want on your cluster.
- Ensure that the `/opt/omnia/input/project_default/build_stream_config.yml` file is updated with the BuildStreaM configuration.


## Procedure


To execute the playbook, run the following commands:

```bash title="Run on: OIM host"
ssh omnia_core
```

```bash title="Run on: omnia_core container"
cd /omnia/utils/credential_utility
ansible-playbook get_config_credentials.yml
```

### Task Performed by the Playbook


Creates an input file called `omnia_config_credentials.yml` in the `/opt/omnia/input/project_default` folder. The `build_stream_oauth_credentials.yml` file is also created in the same folder only when `enable_build_stream` is set to `true` in `/opt/omnia/input/project_default/build_stream_config.yml`.

### Things to Keep in Mind


- While executing any Omnia playbook which requires certain credentials, you'll now see a prompt to enter them during playbook execution.
- Credential fields with the **mandatory** tag cannot be left empty. If the **mandatory** passwords are not provided or incorrect, the playbook execution will stop and exit while encrypting the credentials file in the background.
- Credential fields with the **optional** tag can be skipped. Even if no input is provided, playbook execution will continue.
- Credential fields with the **conditional mandatory** tag are only required if the corresponding feature is enabled in the input files. For example, if you want to deploy BuildStreaM on your cluster, you must provide the BuildStreaM credentials.
- Passwords provided by you will be hidden. You must enter the password for a second time to confirm.
- This utility also supports using tags to provide credentials for specific features or packages. For example, you can use `--tags provision` while executing the playbook to only bring up the credentials required to provision the cluster nodes.


## Verification


After the playbook has been executed, verify if the `omnia_config_credentials.yml` input file is present in the `/opt/omnia/input/project_default` folder. If `enable_build_stream` is set to `true` in `build_stream_config.yml`, also verify that the `build_stream_oauth_credentials.yml` file is present in the same folder.
Provide all required mandatory credentials for the cluster. See the tables below to know more.

!!! note

    By default, the `omnia_config_credentials.yml` input file is encrypted. Use the below command to view the file:

    ```bash
    ansible-vault view omnia_config_credentials.yml --vault-password-file .omnia_config_credentials_key
    ```

!!! note

    If user is decrypting the file, then it must be encrypted again:

    ```bash
    ansible-vault encrypt omnia_config_credentials.yml --vault-password-file .omnia_config_credentials_key
    ```

!!! note

    By default, the `build_stream_oauth_credentials.yml` input file is encrypted. This file is only created when `enable_build_stream` is set to `true` in `build_stream_config.yml`. Use the below command to view the file:

    ```bash
    ansible-vault view build_stream_oauth_credentials.yml --vault-password-file .build_stream_oauth_credentials_key
    ```

### Omnia Credentials

| Credential Name | Mandatory or Optional | Parameter | Details |
|---|---|---|---|
| Provision password | Mandatory | `provision_password` | Password required for root users during OS provisioning on cluster nodes. Length must be at least 8 characters and must not contain commas (`,`), hyphens (`-`), single quotes (`'`), double quotes (`"`), or backslashes (`\`). |
| BMC (iDRAC) username | Mandatory | `bmc_username` | Username for BMC (iDRAC) access. The same credentials must be used across all servers. |
| BMC (iDRAC) password | Mandatory | `bmc_password` | Password required for BMC (iDRAC) access. Length must be at least 3 characters and must not contain commas (`,`), hyphens (`-`), single quotes (`'`), double quotes (`"`), or backslashes (`\`). |
| Pulp container password | Mandatory | `pulp_password` | Password required for setting up the Pulp container. Length must be at least 8 characters and must not contain commas (`,`), hyphens (`-`), single quotes (`'`), double quotes (`"`), or backslashes (`\`). |
| MySQL DB username | Mandatory | `mysqldb_user` | Username of the MySQL user. This parameter is mandatory in order to set up iDRAC telemetry services. |
| MySQL DB password | Mandatory | `mysqldb_password` | Password of the MySQL user. This parameter is mandatory in order to set up iDRAC telemetry services. |
| MySQL DB root password | Mandatory | `mysqldb_root_password` | Root password of the MySQL database (DB). This parameter is mandatory in order to set up iDRAC telemetry services. |
| Docker username | Optional | `docker_username` | Username for the Dockerhub account. This is used to log in to Docker and pull required packages to the cluster. |
| Docker password | Optional | `docker_password` | Password for Dockerhub account. Must be at least 8 characters long and can contain letters, numbers, and special characters. |
| Slurm database password | Optional | `slurm_db_password` | Password for the Slurm database. **Mandatory** if you want to deploy Slurm on your cluster. SlurmDB password must not contain special characters like hyphens (`-`), single quotes (`'`), double quotes (`"`), or backslashes (`\`). |
| OpenLDAP database username | Optional | `openldap_db_username` | Username for OpenLDAP database admin. **Mandatory** if you want to set up OpenLDAP authentication on your cluster. Must not contain semicolons (`;`), square brackets (`[]`), or backticks (`` ` ``). |
| OpenLDAP database password | Optional | `openldap_db_password` | Password for OpenLDAP database admin. **Mandatory** if you want to set up OpenLDAP authentication on your cluster. Must not contain hyphens (`-`), single quotes (`'`), double quotes (`"`), at symbols (`@`), or backslashes (`\`). |
| Minio S3 bucket password | Mandatory | `minio_s3_password` | Password for Minio S3 bucket. Should not be set to admin. Length must be between 5 and 128 characters and must not contain backslashes (`\`), hyphens (`-`), single quotes (`'`), or double quotes (`"`). |
| PowerScale S3 Access ID | Conditional Mandatory | `s3_access_id` | S3 Access ID for PowerScale S3 storage authentication. Mandatory only when provider is set to `powerscale` in `storage_config.yml`. |
| PowerScale S3 Secret Key | Conditional Mandatory | `s3_secret_key` | S3 Secret Key for PowerScale S3 storage authentication. Mandatory only when provider is set to `powerscale` in `storage_config.yml`. |
| Postgres DB username | Conditional Mandatory | `postgres_db_username` | Enter the username to connect to the Postgres DB. Mandatory only if BuildStreamM is enabled in the `build_stream_config.yml` file. |
| Postgres DB password | Conditional Mandatory | `postgres_db_password` | Enter the password to connect to the Postgres DB. Mandatory only if BuildStreamM is enabled in the `build_stream_config.yml` file. |

!!! caution

    Once the cluster is up and running, you may only modify the `bmc_username` and `bmc_password` fields in the `omnia_config_credentials.yml` input file. To make these changes, use the command provided below. Do not alter any other fields in the file, as this may lead to unexpected failures.

    ```bash
    ansible-vault edit omnia_config_credentials.yml --vault-password-file .omnia_config_credentials_key
    ```

### BuildStreaM Credentials

The following credentials are prompted only when `enable_build_stream` is set to `true` in `/opt/omnia/input/project_default/build_stream_config.yml`.

| Credential Name | Mandatory or Optional | Parameter | Details |
|---|---|---|---|
| Build StreaM username | Conditional Mandatory | `build_stream_oauth_username` | Enter the username for the BuildStreamM pipeline. Mandatory only if `enable_build_stream` is set to `true` in `build_stream_config.yml`. |
| Build StreaM password | Conditional Mandatory | `build_stream_oauth_password` | Enter the password for the BuildStreamM pipeline. Mandatory only if `enable_build_stream` is set to `true` in `build_stream_config.yml`. |

## Next Steps

- [Prepare OIM](../main/setup_oim.md) -- Prepare the Omnia Infrastructure Manager for deployment.

## Troubleshooting

No troubleshooting information is currently available for this procedure.



















