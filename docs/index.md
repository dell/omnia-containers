# Omnia Documentation

[![Omnia version](https://img.shields.io/github/v/release/dell/omnia?include_prereleases)](https://github.com/dell/omnia/releases)
[![Downloads](https://img.shields.io/github/downloads/dell/omnia/total)](https://github.com/dell/omnia/releases)
[![Last Commit](https://img.shields.io/github/last-commit/dell/omnia)](https://github.com/dell/omnia/commits)
[![Contributors](https://img.shields.io/github/contributors/dell/omnia)](https://github.com/dell/omnia/graphs/contributors)
[![Forks](https://img.shields.io/github/forks/dell/omnia)](https://github.com/dell/omnia/network/members)
[![License](https://img.shields.io/github/license/dell/omnia)](https://github.com/dell/omnia/blob/main/LICENSE)

Omnia is an open-source, Ansible-based toolkit by Dell Technologies that
automates the deployment and management of HPC, AI, and data analytics clusters
on Dell PowerEdge servers. From bare-metal provisioning to job scheduling,
telemetry, and storage configuration, Omnia turns a rack of servers into a
production-ready cluster.

The project is hosted on [GitHub](https://github.com/dell/omnia), where you can:

- Access the source code
- Report issues
- Ask questions
- Contribute to development

## How This Documentation is Organized


<div class="grid cards" markdown>

-   :material-book-open-variant: **[Overview](Overview/index.md)**

    ---

    Architecture, components, network topologies, and design concepts. Start here if you are new to Omnia.

-   :material-book-open-variant: **[Get Started](GetStarted/index.md)**

    ---

    End-to-end tutorials that take you from a bare set of PowerEdge servers to a fully operational cluster. Choose from Slurm-only, full deployment, Kubernetes + telemetry, or BuildStreaM paths.

-   :material-book-open-variant: **[How-to Guides](HowTo/index.md)**

    ---

    Task-oriented procedures for provisioning, configuring Slurm, Kubernetes, storage, networking, authentication, telemetry, and BuildStreaM.

-   :material-book-open-variant: **[Reference](Reference/index.md)**

    ---

    Configuration parameters, support matrices, playbook references, API documentation, and network port listings.

-   :material-book-open-variant: **[Operations & Maintenance](Operations/index.md)**

    ---

    Day-2 operations: adding and removing nodes, re-provisioning, OIM cleanup, log management, security hardening, and best practices.

-   :material-book-open-variant: **[Troubleshooting](Troubleshooting/index.md)**

    ---

    Symptom-driven guides for diagnosing and resolving issues with provisioning, Slurm, Kubernetes, telemetry, authentication, and more.

-   :material-book-open-variant: **[Security Configuration Guide](Overview/security_configuration_guide.md)**

</div>

## Quick Links


| Resource | Description |
| --- | --- |
| [Slurm Quickstart](GetStarted/slurm_quickstart.md) | Fastest path to a working Slurm cluster (~2 hours, 4 nodes). |
| [Full Deployment](GetStarted/full_deployment.md) | Production deployment with Slurm, Kubernetes, telemetry, and LDAP. |
| [Servers](Reference/SupportMatrix/servers.md) | Supported OS versions, hardware, firmware, and software combinations. |
| [Provision Config](Reference/Configuration/provision_config.md) | Complete reference for all Omnia input configuration files. |

## Licensing

Omnia is made available under the [Apache 2.0 license](https://opensource.org/licenses/Apache-2.0).

!!! note
    Omnia playbooks are licensed under the Apache 2.0 license. Once an end-user initiates Omnia, that end-user will deploy other open-source and/or third-party software that is licensed separately by their respective developer communities and/or third parties. For a comprehensive list of software and their licenses, [click here](Reference/SupportMatrix/installed_software.md). Dell (or any other contributors) shall have no liability regarding (and no responsibility to provide support for) an end-user's use of any open-source and/or third-party software and Omnia users are solely responsible for ensuring that they are complying with all such licenses. Omnia is provided "as is" without any warranty, express or implied. Dell (or any other contributors) shall have no liability for any direct, indirect, incidental, punitive, special, or consequential damages for an end-user's use of Omnia.

## Previous Versions

*For a better understanding of what Omnia does, check out the following:*

- [1.x documentation](https://omnia-doc.readthedocs.io/en/latest/index.html): supports diskful provisioning.
- [2.x documentation](https://omnia.readthedocs.io/en/latest/index.html): supports diskless provisioning and containerized deployment.

!!! note
    Upgrade from Omnia 1.x to 2.x is not supported due to architectural changes.

## Omnia Community Members

<div class="community-logos" style="display: flex; flex-wrap: wrap; align-items: center; gap: 2rem; margin: 1rem 0;">
  <a href="https://www.dell.com"><img src="assets/images/delltech.png" alt="Dell Technologies" style="height: 60px;"></a>
  <a href="https://www.intel.com"><img src="https://upload.wikimedia.org/wikipedia/commons/0/0e/Intel_logo_%282020%2C_light_blue%29.svg" alt="Intel" style="height: 40px;"></a>
  <a href="https://www.unipi.it"><img src="assets/images/pisa.png" alt="University of Pisa" style="height: 60px;"></a>
  <img src="https://user-images.githubusercontent.com/83095575/117071024-64956c80-ace3-11eb-9d90-2dac7daef11c.png" alt="Community Member" style="height: 60px;">
  <img src="https://images.squarespace-cdn.com/content/v1/660f1a48587dbb2769709a33/9ac5520f-a308-4751-80f4-415d07a23473/VIZIAS+Blue.png" alt="VIZIAS" style="height: 60px;">
  <img src="https://user-images.githubusercontent.com/5414112/153955170-0a4b199a-54f0-42af-939c-03eac76881c0.png" alt="Community Member" style="height: 60px;">
  <a href="https://www.liqid.com"><img src="assets/images/Liqid.png" alt="Liqid" style="height: 50px;"></a>
</div>

---

*If you have any feedback about Omnia documentation, please reach out at [omnia.readme@dell.com](mailto:omnia.readme@dell.com).*
