xCAT Terraform Provider
==================

[xCAT](http://xcat.org) is an opensource automating deployment, scaling, and management of bare metal servers and virtual machines developed by IBM. It has been widely used in top tier super computers in the world. 

With Terraform, xCAT can provide a self-serving way for the cluster user to apply compute resources, no need to go though xCAT documentation and follow the complex steps to finish jobs like node provision, hardware control, etc.    


Requirements
------------

-	[Terraform](https://www.terraform.io/downloads.html) v0.11.13

Build
-----
## clone terraform-provider-xcat repo

```sh
mkdir -p /git/
cd /git/
git clone git@github.com:xcat2/terraform-provider-xcat.git
``` 

## housekeeping the "vendor" directory

```sh
glide up --strip-vendor
```

## build terraform-provider-xcat 

```sh
make
```
then you can find the built `terraform-provider-xcat` binary in `$GOROOT/bin` directory 

or leverage the xCAT terraform builder docker image on https://cloud.docker.com/u/xcat/repository/docker/xcat/tfpbuilder

Installation
------------

## Download and install Terraform on xCAT MN

Download Terraform binary from https://github.com/xcat2/terraform-provider-xcat/releases

```sh
$ wget [Terraform Binary URL] -O /usr/bin/terraform
$ chmod +x /usr/bin/terraform
```

## Download and install xCAT Terraform Provider on xCAT MN
Download xCAT Terraform provider binary from https://github.com/xcat2/terraform-provider-xcat/releases

```sh
$ wget [xCAT Terraform Provider URL] -O ~/.terraform.d/plugins/terraform-provider-xcat
$ chmod +x ~/.terraform.d/plugins/terraform-provider-xcat 
```

Creat node resource pool on xCAT MN
------------------------------------

```sh
$ chdef <xCAT nodes to be added into the pool> groups=free usercomment=","
```

Label the nodes in the resource pool on xCAT MN
-----------------------------------------------

Label the nodes with IB

```sh
$ chdef <xCAT nodes with IB> usercomment=",ib=1,"
```

Label the nodes with GPU

```sh
$ chdef <xCAT nodes with IB> usercomment=",gpu=1,"
```

Create Terraform working directory
----------------------------------

```sh
$ mkdir -p ~/mycluster/
$ cd ~/mycluster/
$ terraform init
```

Compose the cluster TF files
----------------------------

An example cluster TF files can be found in https://github.com/xcat2/terraform-provider-xcat/tree/master/templates/devcluster. Modify the TF files according to your need

Refer https://www.terraform.io/docs/configuration/index.html for the Terraform HCL syntax

Resource operation
------------------
1. plan:

```sh
$ cd ~/mycluster/
$ terraform plan
```
 
2. resource apply:

```sh
$ terraform apply
```

3. resource update:

modify the tf file and run
```sh
$ terraform apply
```

4. resource release:

```sh
$ terraform destroy
```
