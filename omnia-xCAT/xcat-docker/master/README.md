# xCAT Server Container
## Description
xCAT is Extreme Cloud Administration Toolkit, xCAT offers complete management for bare-metal based cluster.
## Building (latest stable version)
#### Build latest stable version xCAT container based on Centos 7.x
```
$ docker build -t xcat .
```
#### Build container based on Ubuntu 16.04 (Xenial)
```
$ docker build -f ubuntu/Dockerfile -t xcat:xenial .
```
#### Build container based on Ubuntu 18.04 (Bionic)
```
$ docker build --build-arg xcat_baseos=bionic -f ubuntu/Dockerfile -t xcat:bionic .
```
## Building (dailybuild)
#### Build dailybuild xCAT container based on Centos 7.x
```
$ docker build --build-arg xcat_version=devel -t xcat-devel .
```

## Launching
#### Using host network
```
docker run -d --name xcatmn --network=host --hostname xcatmn --privileged -v /sys/fs/cgroup:/sys/fs/cgroup:ro xcat
```
**Note**: `sshd` service in container cannot be up when using host network, enter the container with:
```
docker exec -it xcatmn /bin/bash
```
## Volumes
xCAT container will create `/xcatdata` volume to store configuration and OS distro data, do not use bind mode to overide the volume unless you have backup all initial data from the container image.
