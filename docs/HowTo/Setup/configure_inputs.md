
# Configure Inputs


Configure Omnia's input files to define your cluster topology, software stack,
and deployment preferences. Input files are YAML and JSON templates located at
`/opt/omnia/input/project_default/` inside the `omnia_core` container.

## Overview


Omnia uses a set of input files to drive every playbook. Before running any
provisioning or deployment playbook, you must:

1. Copy the example templates from `/omnia/examples/input_template/` to the
   working input directory.
2. Edit each file to match your environment (network ranges, software
   selections, cluster layout).
3. Optionally run the `input_validator` to catch configuration errors early.

The most important input files are:

- `software_config.json` -- Defines which software stacks to deploy.
- `network_spec.yml` -- Network configuration for admin, BMC, and compute
  networks.
- `provision_config.yml` -- Provisioning parameters (OS image, language,
  kernel options).
- `omnia_config.yml` -- Cluster-level configuration (Slurm, K8s, storage).


## Prerequisites


- The [Deploy Omnia Core](deploy_omnia_core.md) procedure is complete and `omnia_core` is
  running.
- You have planned your network topology (IP ranges, VLANs, subnets).
- You know which software stacks you want to deploy (Slurm, Kubernetes,
  telemetry, etc.).


## Procedure


1. **Enter the omnia_core container**:

   ```bash title="Run on: OIM host"
   ssh omnia_core
   ```


2. **Copy the example templates** to the input directory:

   ```bash title="Run on: omnia_core container"
   cp /omnia/examples/input_template/* /opt/omnia/input/project_default/
   ```


   !!! note

       If files already exist in the destination, this command will overwrite
       them. Back up any previously customized files before copying.

3. **Edit the software configuration**:

   ```bash title="Run on: omnia_core container"
   vi /opt/omnia/input/project_default/software_config.json
   ```


   Example `software_config.json`:

   ```json title="File: /opt/omnia/input/project_default/software_config.json"
   {
       "cluster_os_type": "rhel",
       "cluster_os_version": "8.8",
       "repo_config": "partial",
       "softwares": [
           {"name": "slurm"},
           {"name": "openldap"},
           {"name": "cuda", "version": "12.2"},
           {"name": "apptainer"}
       ]
   }
   ```


   Key parameters:

   .. list-table::
      :header-rows: 1
      :widths: 30 70

      * - Parameter
        - Description
      * - `cluster_os_type`
        - Target OS: `rhel` or `rocky`
      * - `cluster_os_version`
        - OS version for provisioned nodes (e.g., `8.8`, `9.2`)
      * - `repo_config`
        - Repository strategy: `partial` (Omnia-managed repos only),
          `always` (sync all repos), `never` (skip repo config)
      * - `softwares`
        - List of software stacks to install on compute nodes

4. **Edit the network specification**:

   ```bash title="Run on: omnia_core container"
   vi /opt/omnia/input/project_default/network_spec.yml
   ```


   Example `network_spec.yml`:

   ```yaml title="File: /opt/omnia/input/project_default/network_spec.yml"
   ---
   admin_network:
     nic_name: "eno1"
     static_range: "10.5.0.100-10.5.0.200"
     dynamic_range: "10.5.0.201-10.5.0.254"
     subnet: "10.5.0.0"
     netmask: "255.255.255.0"
     gateway: "10.5.0.1"

   bmc_network:
     nic_name: "eno2"
     static_range: "10.3.0.100-10.3.0.200"
     dynamic_range: "10.3.0.201-10.3.0.254"
     subnet: "10.3.0.0"
     netmask: "255.255.255.0"
   ```


5. **Edit the provision configuration**:

   ```bash title="Run on: omnia_core container"
   vi /opt/omnia/input/project_default/provision_config.yml
   ```


   Example `provision_config.yml`:

   ```yaml title="File: /opt/omnia/input/project_default/provision_config.yml"
   ---
   language: "en-US"
   iso_file_path: "/opt/omnia/iso/RHEL-8.8-x86_64-dvd.iso"
   default_lease_time: 86400
   pxe_mapping_file_path: "/opt/omnia/input/project_default/pxe_mapping_file.csv"
   ```


6. **Edit the Omnia configuration** (for Slurm/K8s parameters):

   ```bash title="Run on: omnia_core container"
   vi /opt/omnia/input/project_default/omnia_config.yml
   ```


   Example `omnia_config.yml`:

   ```yaml title="File: /opt/omnia/input/project_default/omnia_config.yml"
   ---
   mariadb_password: ""
   k8s_version: "1.28"
   k8s_cni: "calico"
   slurm_installation_type: "nfs_share"
   enable_omnia_nfs: true
   ```


7. **(Optional) Run the input validator** to check your configuration:

   ```bash title="Run on: omnia_core container"
   cd /omnia
   ansible-playbook input_validator.yml
   ```


   The validator checks for:

   - Missing required fields.
   - IP address format and range conflicts.
   - Valid software names and versions.
   - Consistent network configuration.


## Verification


1. **List all input files** and confirm they are populated:

   ```bash title="Run on: omnia_core container"
   ls -la /opt/omnia/input/project_default/
   ```


2. **Review the software configuration**:

   ```bash title="Run on: omnia_core container"
   cat /opt/omnia/input/project_default/software_config.json | python3 -m json.tool
   ```


3. **Validate YAML syntax** for each YAML input file:

   ```bash title="Run on: omnia_core container"
   python3 -c "import yaml; yaml.safe_load(open('/opt/omnia/input/project_default/network_spec.yml'))"
   ```


   No output means the YAML is syntactically valid.


## Next Steps


- [Configure Credentials](configure_credentials.md) -- Set up encrypted credentials for provisioning.
- [Prepare Oim](prepare_oim.md) -- Prepare OIM services (OpenCHAMI, Pulp, etc.).


## Troubleshooting


**input_validator fails with "missing required field"**
   Open the indicated file and ensure all required fields are present. Refer to
   the example templates in `/omnia/examples/input_template/` for the complete
   list of required fields.

**JSON syntax error in software_config.json**
   Validate JSON syntax:

   ```bash title="Run on: omnia_core container"
   python3 -m json.tool /opt/omnia/input/project_default/software_config.json
   ```


**Network range overlap**
   Ensure `admin_network` and `bmc_network` use different subnets.
   Static and dynamic ranges within each network must not overlap.

**Template files not found in /omnia/examples/input_template/**
   Verify the Omnia repository version. Templates are available in v2.1.0.0
   and later. Pull the latest code if necessary:

   ```bash title="Run on: OIM host"
   cd /opt/omnia && git pull
   ```
