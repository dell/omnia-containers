Miscellaneous Configuration and Management Elements
====================================================

Licensing
---------

Omnia is licensed under the Apache License 2.0. A permissive license whose main conditions require preservation of copyright and license notices. Contributors provide an express grant of patent rights. Licensed works, modifications, and larger works may be distributed under different terms and without source code.


Protect Authenticity
---------------------

Every GitHub push requires a sign-off and a moderator is required to approve pull requests. All contributions have to be certified using the Developer Certificate of Origin (DCO):


 ::


    Developer Certificate of Origin
    Version 1.1

    Copyright (C) 2004, 2006 The Linux Foundation and its contributors.
    1 Letterman Drive
    Suite D4700
    San Francisco, CA, 94129

    Everyone is permitted to copy and distribute verbatim copies of this
    license document, but changing it is not allowed.


    Developer's Certificate of Origin 1.1

    By making a contribution to this project, I certify that:

    (a) The contribution was created in whole or in part by me and I
        have the right to submit it under the open source license
        indicated in the file; or

    (b) The contribution is based upon previous work that, to the best
        of my knowledge, is covered under an appropriate open source
        license and I have the right under that license to submit that
        work with modifications, whether created in whole or in part
        by me, under the same open source license (unless I am
        permitted to submit under a different license), as indicated
        in the file; or

    (c) The contribution was provided directly to me by some other
        person who certified (a), (b) or (c) and I have not modified
        it.

    (d) I understand and agree that this project and the contribution
        are public and that a record of the contribution (including all
        personal information I submit with it, including my sign-off) is
        maintained indefinitely and may be redistributed consistent with
        this project or the open source license(s) involved.


Ansible Security
-----------------

For the security guidelines of Ansible modules, go to `Developing Modules Best Practices: Module Security <https://docs.ansible.com/ansible/latest/dev_guide/developing_modules_best_practices.html#module-security>`_.

Ansible Vault
-------------

Ansible vault enables encryption of variables and files to protect sensitive content such as passwords or keys rather than leaving it visible as plaintext in playbooks or roles. Please refer `Ansible Vault guidelines <https://docs.ansible.com/ansible/latest/vault_guide/index.html>`_ for more information.

Encrypted Parameters Management
--------------------------------

To view encrypted parameters:

.. code-block:: bash

   ansible-vault view omnia_config_credentials.yml --vault-password-file .omnia_config_credentials_key

To edit encrypted parameters:

.. code-block:: bash

   ansible-vault edit omnia_config_credentials.yml --vault-password-file .omnia_config_credentials_key