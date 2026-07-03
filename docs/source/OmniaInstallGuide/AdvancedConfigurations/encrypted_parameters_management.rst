Encrypted Parameters Management
================================

Omnia uses Ansible Vault to encrypt sensitive configuration parameters such as passwords, API keys, and other credentials. These encrypted parameters are stored in ``omnia_config_credentials.yml`` and protected using a vault password file.

To view encrypted parameters:

.. code-block:: bash

   ansible-vault view omnia_config_credentials.yml --vault-password-file .omnia_config_credentials_key

To edit encrypted parameters:

.. code-block:: bash

   ansible-vault edit omnia_config_credentials.yml --vault-password-file .omnia_config_credentials_key

.. note:: The vault password file ``.omnia_config_credentials_key`` must be kept secure and should not be committed to version control.
