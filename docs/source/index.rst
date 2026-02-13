.. Omnia documentation master file, created by
   sphinx-quickstart on Thu Jul 28 11:20:32 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Omnia: Everything at once!
----------------------------------

|Omnia version| |Downloads| |Last Commit| |Contributors| |Forks| |License|

Omnia is a containerized, open-source deployment toolkit designed to automate the setup
and management of high-performance computing (HPC) environments on Linux-based servers.
It leverages Ansible playbooks to streamline:

- Operating system provisioning
- Driver installation and configuration
- Deployment of workload schedulers such as Slurm and Kubernetes
- Installation of optimization libraries, machine learning frameworks, and AI models
- Management of compute, storage, and networking resources

Omnia simplifies infrastructure deployment in complex environments, enabling faster setup
and consistent configuration across systems.

The project is hosted on `GitHub <https://github.com/dell/omnia>`_., where you can:

- Access the source code
- Report issues
- Ask questions
- Contribute to development

**Licensing**

Omnia is made available under the `Apache 2.0 license. <https://opensource.org/licenses/Apache-2.0>`_

.. note:: Omnia playbooks are licensed under the Apache 2.0 license. Once an end-user initiates Omnia, that end-user will deploy other open-source and/or third-party software that is licensed separately by their respective developer communities and/or third parties. For a comprehensive list of software and their licenses, `click here <Overview/SupportMatrix/omniainstalledsoftware.html>`_. Dell (or any other contributors) shall have no liability regarding (and no responsibility to provide support for) an end-users use of any open-source and/or third-party software and OMNIA users are solely responsible for ensuring that they are complying with all such licenses. Omnia is provided “as is” without any warranty, express or implied. Dell (or any other contributors) shall have no liability for any direct, indirect, incidental, punitive, special, or consequential damages for an end-user's use of Omnia.

For a better understanding of what Omnia does, check out the following:
    * `1.x documentation <https://omnia-doc.readthedocs.io/en/latest/index.html>`_: supports diskful provisioning.
    * `2.x documentation <https://omnia.readthedocs.io/en/latest/index.html>`_: supports diskless provisioning and containerized deployment.

.. note:: Upgrade from Omnia 1.x to 2.x is not supported due to architectural changes.

**Omnia Community Members**

.. image:: images/logos/delltech.jpg
   :width: 60pt

.. image:: https://upload.wikimedia.org/wikipedia/commons/0/0e/Intel_logo_%282020%2C_light_blue%29.svg
    :width: 60pt

.. image:: images/logos/pisa.png
  :width: 60pt

.. image:: https://user-images.githubusercontent.com/83095575/117071024-64956c80-ace3-11eb-9d90-2dac7daef11c.png
  :width: 60pt

.. image:: https://images.squarespace-cdn.com/content/v1/660f1a48587dbb2769709a33/9ac5520f-a308-4751-80f4-415d07a23473/VIZIAS+Blue.png
    :width: 60pt

.. image:: https://user-images.githubusercontent.com/5414112/153955170-0a4b199a-54f0-42af-939c-03eac76881c0.png
  :width: 60pt

.. image:: images/logos/Liqid.png
   :width: 60pt


**Table Of Contents**

.. toctree::
    :maxdepth: 2

    Overview/index
    bestpractices
    Overview/SupportMatrix/index
    RHEL_prereq
    OmniaInstallGuide/index
    OmniaInstallGuide/ExternalDeploymentGuide/Index
    Utils/index
    Logging/index
    Troubleshooting/index
    SecurityConfigGuide/index
    limitations
    Contributing/index
    appendix

.. |Omnia version| image:: https://img.shields.io/github/v/release/dell/omnia?include_prereleases
.. |Downloads| image:: https://img.shields.io/github/downloads/dell/omnia/total
.. |Last Commit| image:: https://img.shields.io/github/last-commit/dell/omnia/main
.. |Contributors| image:: https://img.shields.io/github/all-contributors/dell/omnia
   :target: docs/CONTRIBUTORS.md
   :alt: Contributors
.. |Forks| image:: https://img.shields.io/github/forks/dell/omnia
.. |License| image:: https://img.shields.io/github/license/dell/omnia
   :target: LICENSE
   :alt: Repository License


