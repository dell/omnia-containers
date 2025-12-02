Files
---

```console
build_ldms.rockylinux8.9.bash             Build ldms
build_ldms.ubuntu22.04.bash               Build ldms
configure.sh*                             Configure ldms
rpm_postuninstall.txt                     For RPM post uninstall
start_build_container.rockylinux8.9.bash  Start build container
start_build_container.ubuntu22.04.bash    Start build container
```

Build Steps
---

1. Set path to the ovis source

```console
export LDMS_REPO=<PATH_TO_OVIS_CLONE>
```

2. Start the build container, which mounts the ovis source and build script dir

```console
start_build_container.rockylinux8.9.bash
```

3. Change to source directory and run the build scrpt

```console
pushd /builds/ovis/
./build_ldms.rockylinux8.9.bash
```

4. The build product and tar bundle will be in the top of the ovis source directory



