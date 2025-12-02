Sample Ansible for Configuring a Node 
---

This Ansible playbook requires access to HashiCorp Vault and the following Ansible facts: vault_token, vault_url, and auth_node_type.

LDMS configuration files are generated from templates, with specific sections enabled based on the PCI devices detected on the booting node:

Nvidia GPU present: The DCGM plugin is added to the LDMS configuration.

CXI NIC present: The Slingshot sampler is enabled.

Finally, the LDMS service is enabled and restarted to apply the new configuration.
