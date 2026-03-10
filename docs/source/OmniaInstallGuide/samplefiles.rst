Sample Files
=============      


Inventory file for PXE Boot Order
---------------------------------

::

    [bmc]
    10.3.0.1
    10.3.0.2

software_config.json for RHEL
-------------------------------------------

::

    {
        "cluster_os_type": "rhel",
        "cluster_os_version": "10.0",
        "repo_config": "always",
        "softwares": [
            {"name": "default_packages", "arch": ["x86_64","aarch64"]},
            {"name": "openldap", "arch": ["x86_64","aarch64"]},
            {"name": "nfs", "arch": ["x86_64","aarch64"]},
            {"name": "service_k8s","version": "1.34.1", "arch": ["x86_64"]},
            {"name": "slurm_custom", "arch": ["x86_64","aarch64"]},
            {"name": "ucx", "version": "1.19.0", "arch": ["x86_64","aarch64"]},
            {"name": "openmpi", "version": "5.0.8", "arch": ["x86_64","aarch64"]},
            {"name": "csi_driver_powerscale", "version":"v2.15.0", "arch": ["x86_64"]},
            {"name": "ldms", "arch": ["x86_64","aarch64"]}
        ],
        "slurm_custom": [
            {"name": "slurm_control_node"},
            {"name": "slurm_node"},
            {"name": "login_node"},
            {"name": "login_compiler_node"}
        ],
        "service_k8s": [
            {"name": "service_kube_control_plane_first"},
            {"name": "service_kube_control_plane"},
            {"name": "service_kube_node"}
        ]

    }
 

pxe_mapping_file.csv
------------------------------------

::

    FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP
    slurm_control_node_x86_64,grp0,ABCD12,,slurm-control-node1,xx:yy:zz:aa:bb:cc,172.16.107.52,xx:yy:zz:aa:bb:dd,172.17.107.52
    slurm_node_x86_64,grp2,ABCD34,ABFL82,slurm-node1,aa:bb:cc:dd:ee:ff,172.16.107.43,aa:bb:cc:dd:ee:aa,172.17.107.43
    slurm_node_x86_64,grp1,ABFG34,ABKD88,slurm-node2,aa:bb:cc:dd:ee:gg,172.16.107.44,aa:bb:cc:dd:ff:bb,172.17.107.44
    slurm_node_x86_64,grp1,BBFG35,ABKD88,slurm-node3,aa:bb:cc:dd:ee:hh,172.16.107.46,aa:bb:cc:dd:ff:cc,172.17.107.46
    login_node_x86_64,grp8,ABCD78,,login-compiler-node1,aa:bb:cc:dd:ee:gg,172.16.107.41,aa:bb:cc:dd:ee:bb,172.17.107.41
    login_compiler_node_x86_64,grp9,ABFG78,,login-compiler-node2,aa:bb:cc:dd:ee:gg,172.16.107.42,aa:bb:cc:dd:ee:bb,172.17.107.42
    service_kube_control_plane_x86_64,grp3,ABFG79,,service-kube-control-plane1,aa:bb:cc:dd:ee:ff,172.16.107.53,xx:yy:zz:aa:bb:ff,172.17.107.53
    service_kube_control_plane_x86_64,grp4,ABFH78,,service-kube-control-plane2,aa:bb:cc:dd:ee:hh,172.16.107.54,xx:yy:zz:aa:bb:hh,172.17.107.54
    service_kube_control_plane_x86_64,grp4,ABFH80,,service-kube-control-plane3,aa:bb:cc:dd:ee:ii,172.16.107.55,xx:yy:zz:aa:bb:ii,172.17.107.55
    service_kube_node_x86_64,grp5,ABFL82,,service-kube-node1,aa:bb:cc:dd:ee:jj,172.16.107.56,xx:yy:zz:aa:bb:jj,172.17.107.56
    service_kube_node_x86_64,grp5,ABKD88,,service-kube-node2,aa:bb:cc:dd:ee:kk,172.16.107.57,xx:yy:zz:aa:bb:ff,172.17.107.57

Slurm configuration files
-------------------------

You can provide custom configurations in ``omnia_config.yml`` > ``slurm_cluster`` > ``config_sources`` as a file path. Omnia merges these custom configuration files with system defaults and existing configurations.