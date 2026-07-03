
# Configure Vast


This section describes the steps to build the Vast repository and install the
Vast client on the cluster nodes.

!!! note

    The Vast repository must be hosted on an HTTP server (such as Apache)
    before it can be used as a user repository in Omnia.


## VAST Storage Prerequisites


Configure the following settings on the VAST Storage appliance before building
the Vast repository:

1. **Login to VAST Dashboard** -- Login to the VAST dashboard and click on
   Element Store.

2. **Configure Tenant** -- Ensure that the tenant is configured on the VAST
   Storage appliance.

3. **Configure Policies** -- Ensure that the policies are configured.

4. **Create New Configuration** -- Right-click on the empty space and the
   Create option will appear. Click on the Create button to complete the
   configuration.


## Step 1: Download Vast


Download the Vast package using the following command:

```bash title="Run on: OIM host"
curl -sSf https://vast-nfs.s3.amazonaws.com/download.sh | bash -s -- --version 4.5.5
```


## Step 2: Extract the Package


Extract the downloaded tarball:

```bash title="Run on: OIM host"
tar -xf vastnfs-4.5.5.tar.xz vastnfs-4.5.5/
```


## Step 3: Build the Vast Repository


Navigate to the extracted directory and build the repository:

```bash title="Run on: OIM host"
cd vastnfs-4.5.5/
./build.sh bin
```

Once the build is complete, you will see a message indicating that the RPM
files have been created and are ready to be hosted as a user repository.
The Vast RPMs will be located in the `dist/` directory within `vastnfs-4.5.5/`.

```
========== Vast repo build completed ==========
```


## Step 4: Host the RPMs on an HTTP Server


Host the RPMs on an HTTP server (such as Apache) or any other server that will
serve as your user repository.

For example, you can use the OIM as an HTTP server. Follow the steps provided
in the documentation for hosting Slurm repositories on the Apache server
(refer to [Configuring Specific Local Repositories](https://omnia.readthedocs.io/en/v2.2.0.0-rc1/OmniaInstallGuide/RHEL_new/CreateLocalRepo/localrepos.html)).

```
========== Vast rpms hosted for user_Repo ==========
```


## Step 5: Configure the User Repository in local_repo_config.yml


Add the user repository URL to the `local_repo_config.yml` file.


## Step 6: Run Omnia Playbooks


Run the following playbooks in order:

1. `local_repo` playbook
2. `build_image` playbook
3. `provision` playbook

The Vast client will be installed on the nodes successfully after the
`provision` playbook completes.


## Next Steps


- [Configure NFS](configure_nfs.md) -- Configure NFS for shared storage across compute
  nodes.
- [Configure PowerVault](configure_powervault.md) -- Configure block storage for additional
  performance.
