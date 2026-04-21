Best Practices
==============

* Ensure that PowerCap policy is disabled and the BIOS system profile is set to 'Performance' on the OIM.
* Always run playbooks inside the Omnia core container from the directory where they are located. Use the ``cd`` command to navigate to the playbook's directory before executing it.
* If telemetry is enabled, ensure sufficient storage is available in NFS as specified in the ``storage_config.yml`` file.
* When using PowerScale as an NFS server, integrate it using the Dell CSI PowerScale driver instead of configuring it as an external NFS server.
* Ensure that the NFS defined in ``storage_config.yml`` is accessible by all nodes intended to be booted. 
* Avoid rebooting the OIM as much as possible to prevent disruptions to the network configuration.
* Review all the prerequisites and input files before running Omnia playbooks.
* Ensure that the Firefox version being used on the RHEL OIM is the latest available. This can be achieved using ``dnf update firefox -y``
* Run ``yum update --security`` routinely on the RHEL OIM to get the latest security updates.
