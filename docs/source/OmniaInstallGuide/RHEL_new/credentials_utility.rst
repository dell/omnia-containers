Step 4: Provide Required Credentials for Omnia
================================================

Omnia provides an additional utility playbook called ``get_config_credentials.yml``. When executed, this playbook creates an input file called ``omnia_config_credentials.yml`` and ``build_stream_oauth_credentials.yml`` in the ``/opt/omnia/input/project_default`` folder. The ``build_stream_oauth_credentials.yml`` file is only created if BuildStreaM is enabled in the ``build_stream_config.yml`` file. 
In this input file, you can preemptively provide all types of mandatory and optional credentials required by Omnia during its execution. Otherwise, you'll be prompted to enter them during playbook execution.

Prerequisites
---------------

* Ensure that the ``omnia_core`` container is up and running.
* Ensure that the ``/opt/omnia/input/project_default/software_config.json`` file is updated with the packages that you want on your cluster.
* Ensure that the ``/opt/omnia/input/project_default/build_stream_config.yml`` file is updated with the BuildStreaM configuration.

Task Performed by the Playbook
---------------------------------

Creates an input file called ``omnia_config_credentials.yml`` and ``build_stream_oauth_credentials.yml`` in the ``/opt/omnia/input/project_default`` folder.

Execute the Playbook
----------------------

To execute the playbook, run the following command: ::

    ssh omnia_core
    cd /omnia/utils/credential_utility
    ansible-playbook get_config_credentials.yml



Things to Keep in Mind
------------------------

* While executing any Omnia playbook which requires certain credentials, you'll now see a prompt to enter them during playbook execution.
* Credential fields with the ``mandatory`` tag cannot be left empty. If the ``mandatory`` passwords are not provided or incorrect, the playbook execution will stop and exit while encrypting the credentials file in the background.
* Credential fields with the ``optional`` tag can be skipped. Even if no input is provided, playbook execution will continue.
* Credential fields with the ``conditional mandatory`` tag are only required if the corresponding feature is enabled in the input files. For example, if you want to deploy BuildStreaM on your cluster, you must provide the BuildStreaM credentials.
* Passwords provided by you will be hidden. You must enter the password for a second time to confirm.
* This utility also supports using tags to provide credentials for specific features or packages. For example, you can use ``--tags provision`` while executing the playbook to only bring up the credentials required to provision the cluster nodes.

Post Execution
----------------

After the playbook has been executed, verify if the ``omnia_config_credentials.yml`` and ``build_stream_oauth_credentials.yml`` input files are present in the ``/opt/omnia/input/project_default`` folder.
Provide all required mandatory credentials for the cluster. See the table below to know more:

.. note:: By default, the ``omnia_config_credentials.yml`` input file is encrypted. Use the below command to view the file: 
    ::
        ansible-vault view omnia_config_credentials.yml --vault-password-file .omnia_config_credentials_key

.. note:: If user is decrypting the file, then it must be encrypted again: 
    ::
        ansible-vault encrypt omnia_config_credentials.yml --vault-password-file .omnia_config_credentials_key

.. note:: By default, the ``build_stream_oauth_credentials.yml`` input file is encrypted. Use the below command to view the file: 
    ::
        ansible-vault view build_stream_oauth_credentials.yml --vault-password-file .build_stream_oauth_credentials_key
   
.. csv-table:: Omnia credentials
   :file: ../../Tables/credentials_utility.csv
   :header-rows: 1
   :keepspace:
   

.. caution:: Once the cluster is up and running, you may only modify the ``bmc_username`` and ``bmc_password`` fields in the ``omnia_config_credentials.yml`` input file. To make these changes, use the command provided below. Do not alter any other fields in the file, as this may lead to unexpected failures.
    ::
        ansible-vault edit omnia_config_credentials.yml --vault-password-file .omnia_config_credentials_key


.. csv-table:: BuildStreaM credentials
   :file: ../../Tables/build_stream_credential_utility.csv
   :header-rows: 1
   :keepspace: