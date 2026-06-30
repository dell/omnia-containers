
# Configure Credentials


Create encrypted credentials for Omnia provisioning using the
`credentials_utility` playbook. Credentials are stored in an Ansible
Vault-encrypted file, ensuring sensitive data (passwords, tokens) is never
stored in plain text.

## Overview


Omnia requires credentials for:

- **Provisioning** -- BMC/iDRAC access, OS root password, and SNMP community
  strings.
- **Software stacks** -- MariaDB passwords, LDAP admin credentials, Kubernetes
  secrets.

The `get_config_credentials.yml` playbook interactively prompts for these
credentials and stores them in an encrypted `omnia_config_credentials.yml`
file. This file is consumed by subsequent playbooks (`prepare_oim.yml`,
`discovery.yml`, `omnia.yml`) automatically.


## Prerequisites


- The [Deploy Omnia Core](deploy_omnia_core.md) procedure is complete.
- The [Configure Inputs](configure_inputs.md) procedure is complete (input files populated).
- You have the BMC/iDRAC administrator username and password for target
  servers.
- You have decided on a root password for provisioned nodes.


## Procedure


1. **Enter the omnia_core container**:

   ```bash title="Run on: OIM host"
   ssh omnia_core
   ```


2. **Navigate to the credential utility directory**:

   ```bash title="Run on: omnia_core container"
   cd /omnia/utils/credential_utility
   ```


3. **Run the credential configuration playbook** with the `provision` tag:

   ```bash title="Run on: omnia_core container"
   ansible-playbook get_config_credentials.yml --tags provision
   ```


   The playbook will prompt you for:

   .. list-table::
      :header-rows: 1
      :widths: 35 65

      * - Prompt
        - Description
      * - `Vault password`
        - Master password to encrypt the credentials file. **Remember this
          password** -- you will need it for all subsequent playbook runs.
      * - `BMC username`
        - iDRAC administrator username (typically `root`)
      * - `BMC password`
        - iDRAC administrator password
      * - `Provision OS password`
        - Root password for provisioned nodes
      * - `SNMP community string`
        - SNMP community string for hardware monitoring (optional)

   !!! warning

       The Vault password is the **only** way to decrypt the credentials file.
       If you lose it, you must re-run this playbook and re-enter all
       credentials.

4. **Verify the encrypted file was created**:

   ```bash title="Run on: omnia_core container"
   ls -la /opt/omnia/input/project_default/omnia_config_credentials.yml
   ```


5. **(Optional) View the encrypted credentials** to confirm values:

   ```bash title="Run on: omnia_core container"
   ansible-vault view /opt/omnia/input/project_default/omnia_config_credentials.yml
   ```


   Enter the Vault password when prompted. The decrypted content will display
   temporarily in the terminal.


## Verification


1. **Confirm the file is Ansible Vault encrypted**:

   ```bash title="Run on: omnia_core container"
   head -1 /opt/omnia/input/project_default/omnia_config_credentials.yml
   ```


   Expected output:

   ```text title="Expected output on: omnia_core container"
   $ANSIBLE_VAULT;1.1;AES256
   ```


2. **Test decryption** with the Vault password:

   ```bash title="Run on: omnia_core container"
   ansible-vault view /opt/omnia/input/project_default/omnia_config_credentials.yml
   ```


   If the password is correct, you will see the decrypted YAML content. If
   incorrect, Ansible will report a decryption error.

3. **Verify credential completeness** by checking that all required keys are
   present in the decrypted output:

   - `bmc_username`
   - `bmc_password`
   - `provision_os_password`


## Next Steps


- [Prepare Oim](prepare_oim.md) -- Prepare OIM services using the configured credentials.
- [Discover Nodes](discover_nodes.md) -- Run node discovery (requires BMC credentials).


## Troubleshooting


**"Vault password incorrect" when viewing credentials**
   Ensure you are entering the exact password used during creation. The password
   is case-sensitive.

**Need to update a single credential**
   Edit the encrypted file directly:

   ```bash title="Run on: omnia_core container"
   ansible-vault edit /opt/omnia/input/project_default/omnia_config_credentials.yml
   ```


   This opens the decrypted file in your default editor. Save and exit to
   re-encrypt.

**Need to change the Vault password**
   Re-key the encrypted file:

   ```bash title="Run on: omnia_core container"
   ansible-vault rekey /opt/omnia/input/project_default/omnia_config_credentials.yml
   ```


**Playbook prompts are not appearing**
   Ensure you are running the playbook interactively (not piped or redirected).
   The `--tags provision` flag limits the prompts to provisioning-related
   credentials only.

**Credentials file already exists**
   Re-running the playbook will overwrite the existing file. Back up the
   current file if needed:

   ```bash title="Run on: omnia_core container"
   cp /opt/omnia/input/project_default/omnia_config_credentials.yml \
      /opt/omnia/input/project_default/omnia_config_credentials.yml.bak
   ```
