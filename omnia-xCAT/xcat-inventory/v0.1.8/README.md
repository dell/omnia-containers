# xcat-inventory - A Infrastructure-as-Code(IaC) cluster management system based on xCAT

[**xcat-inventory**](https://github.com/xcat2/xcat-inventory/wiki/xcat-inventory--Wiki) is an inventory tool for the cluster managed by [**xCAT**](http://xcat.org), the features include:

- an object based view of the cluster inventory, which is flexible, extensible and well formatted

- interfaces to export/import the cluster inventory data in yaml/json format

- inventory templates for typical clusters, which help users to define a cluster easily

- native ability to manage cluster configuration under source control (see [Cookbook](https://github.com/xcat2/xcat-inventory/wiki/How-to-source-control-xCAT-Cluster-configuration-with-%22xcat-inventory%22%3F))

- automatic cluster deployment according to the cluster definition (Coming soon)

- ability to integrate with Ansible (Coming soon)

The typical workflow:

![alt text](https://github.com/xcat2/xcat-inventory/blob/master/workflow.jpg)


## Table of Contents

- [Installing](#installing)
- [Building](#building)
- [Dependencies](#dependency)
- [Platform Restrictions](#platform)
- [Cookbooks](#Cookbooks)
- [Typical use cases](#usecase)
  - [Version control of cluster inventory data](#versioncontrol)
  - [define and create a xCAT cluster inventory](#definecluster)
- [Reporting bugs](#reporting-bugs)


## Installing

Download the "xcat-inventory" package from [xcat-inventory for RHEL 7](https://github.com/xcat2/xcat-inventory/releases/download/v0.1.7/xcat-inventory-0.1.7-1.el7.noarch.rpm) or [xcat-inventory for RHEL 8](https://github.com/xcat2/xcat-inventory/releases/download/v0.1.7/xcat-inventory-0.1.7-1.el8.noarch.rpm) to the xCAT management node, and run `yum install xcat-inventory.rpm` to install it.

## Building

```
[root@boston01 ~]# git clone https://github.com/xcat2/xcat-inventory.git
Cloning into 'xcat-inventory'...
remote: Counting objects: 1844, done.
remote: Compressing objects: 100% (7/7), done.
remote: Total 1844 (delta 0), reused 6 (delta 0), pack-reused 1837
Receiving objects: 100% (1844/1844), 401.48 KiB | 0 bytes/s, done.
Resolving deltas: 100% (1072/1072), done.
```

```
[root@boston01 ~]# cd xcat-inventory
[root@boston01 ~]# git checkout master
Already on 'master'
[root@boston01 ~]# git pull upstream master --tags
From github.com:xcat2/xcat-inventory
 * branch            master     -> FETCH_HEAD
Already up-to-date.
[root@boston01 xcat-inventory]# ./makepythonrpm xcat-inventory
...
Building /root/rpmbuild/RPMS/noarch/xcat-inventory-0.1.7*.noarch.rpm ...
/root/rpmbuild/RPMS/noarch/xcat-inventory-0.1.7-el8.noarch.rpm
```

## Dependency

Several python packages are required:

* Psycopg: PostgreSQL adapter for the Python
* SQLAlchemy(above 0.8.0): Python SQL toolkit and Object Relational Mapper
* PyMySQL(0.7.x): a pure-Python MySQL client library
* PyYAML: YAML parser and emitter for the Python
* Six: a Python 2 and 3 compatibility library
* deepdiff: Deep Difference of dictionaries, iterables, strings and other objects. It will recursively look for all the changes
* configparser: a module working with configuration files
* sh: a full-fledged subprocess replacement for Python 2.6 - 3.6, PyPy and PyPy3 that allows you to call any program as if it were a function

In most cases, these packages will be installed during `xcat-inventory` installation. 

If you are prompted that some of them cannot be found during `xcat-inventory` installation, you can download the package from [dep-url](http://xcat.org/files/xcat/xcat-dep/2.x_Linux/beta/xcat-inventory/) and install it manually. 

If you are prompted `No module named xxx` when you run `xcat-inventory`, you can install the missing package with one of the following way: 

* install the corresponding rpm/deb package
* install the python package with `pip`
* download the python package tarball from PyPi(https://pypi.python.org/pypi), uncompress it and install the package with `python setup.py install`

## Platform Restrictions

The `xcat-inventory` is arch independent, i.e, you can install it on xCAT management nodes with architecture `X86_64`,`ppc64`, or `ppc64le` 

Currently, only rpm package is shipped, which can be installed on Linux distributions like Redhat 7.x, CentOS 7.x and SuSE. 

The installation and function verification was tested on RHEL 7.x and RHEL 8.1. 

For other Linux distributions, you might need to handle the dependency issue by yourself. 


## Cookbooks

See [Cookbooks](https://github.com/xcat2/xcat-inventory/wiki)


## Blueprints

See [Designs](https://github.com/xcat2/xcat-inventory/wiki#mini-designs-of-xcat-inventory-major-features)

## Usecase

This section presents some typical usecases [xcat-inventory usecase](http://xcat-docs.readthedocs.io/en/latest/advanced/xcat-inventory/index.html)

## Reporting bugs

For any bugs or feature request, please open ticket in [issues](https://github.com/xcat2/xcat-inventory/issues)



