# Path D: BuildStreaM Automated Deployment


Deploy an 8+ node cluster using BuildStreaM, Omnia's catalog-driven
automation framework powered by GitLab CI/CD. BuildStreaM reads a
declarative hardware and software catalog, generates the required Omnia
input files, and executes deployment pipelines -- transforming a manual
multi-hour process into a repeatable, version-controlled workflow.

**What you will build:**

| Role | Functional Group | Count | Purpose |
| --- | --- | --- | --- |
| OIM (management) | -- | 1 | Runs `omnia_core` and the GitLab CI/CD runner. |
| Slurm head node | `slurm_control_node` | 1 | Slurm controller. |
| Compute nodes | `slurm_node` | 1+ | Slurm compute workers. |
| Login node | `login_node` | 1 | User-facing SSH gateway. |
| K8s control plane | `service_kube_control_plane` | 3 | HA Kubernetes service cluster. |
| K8s worker node | `service_kube_node` | 1+ | Telemetry stack and GitLab services. |

**What makes BuildStreaM different:**

- **Declarative catalog** -- Define your cluster in a YAML catalog file.
  BuildStreaM translates it into Omnia input files automatically.
- **GitLab CI/CD pipelines** -- Every deployment step (prepare, discover,
  deploy, verify) runs as a CI/CD stage with logs, artifacts, and rollback.
- **Reproducibility** -- The catalog is version-controlled in Git. Rebuild
  an identical cluster from a single `git push`.
- **Scale** -- Designed for environments with 8, 16, 64, or hundreds of
  nodes where manual input-file editing is error-prone.

**Estimated time:** ~6 hours (includes GitLab deployment and pipeline execution).

!!! note

    Complete the [Prerequisites Checklist](prerequisites_checklist.md) before proceeding. In
    addition, BuildStreaM requires:

    - A GitLab instance (deployed in Step 4 below, or an existing one).
    - OAuth application credentials for GitLab integration.
    - Familiarity with Git workflows (clone, push, merge requests).

## Step 1 -- Deploy the omnia_core Container


```shell title="Run on OIM (as root)"
cd /opt
git clone https://github.com/dell/omnia.git
cd omnia

# Build container images
bash build_images.sh

# Install and start the omnia_core container
bash omnia.sh --install

# Verify
systemctl status omnia_core
```


```shell title="Run on OIM (as root)"
ssh omnia_core
exit
```



## Step 2 -- Enable BuildStreaM


Configure BuildStreaM before running the prepare playbooks. This ensures
that all BuildStreaM-specific services and packages are included from the
start.

### **2a. Edit** `build_stream_config.yml`


```shell title="Run on OIM (inside omnia_core container)"
ssh omnia_core
vi /opt/omnia/input/project_default/build_stream_config.yml
```


```yaml title="Example build_stream_config.yml"
# Enable the BuildStreaM catalog-driven deployment framework
build_stream_enabled: true

# GitLab instance URL (will be deployed in Step 4 if not already available)
gitlab_url: "http://10.5.0.10:8080"

# GitLab project path for the catalog repository
catalog_project: "omnia/cluster-catalog"

# CI/CD runner tags (used to route pipeline jobs to the OIM runner)
runner_tags:
  - omnia-oim
  - deployment

# Catalog file path inside the Git repository
catalog_file: "catalog.yml"
```


!!! warning

    If you plan to use an **existing** GitLab instance, set `gitlab_url`
    to its URL and skip Step 4. If you want Omnia to deploy GitLab for
    you on the K8s service cluster, keep the default and proceed through
    all steps.

**2b. Configure OAuth credentials**

BuildStreaM authenticates with GitLab via OAuth. Generate an OAuth
application in GitLab (or prepare to do so after GitLab is deployed in
Step 4).

```shell title="Run on OIM (inside omnia_core container)"
vi /opt/omnia/input/project_default/build_stream_oauth_credentials.yml
```


```yaml title="Example build_stream_oauth_credentials.yml"
# OAuth Application ID from GitLab
oauth_app_id: ""

# OAuth Application Secret from GitLab
oauth_app_secret: ""

# OAuth callback URL (must match GitLab OAuth app configuration)
oauth_callback_url: "http://10.5.0.10:8080/oauth/callback"
```


!!! tip

    Leave `oauth_app_id` and `oauth_app_secret` empty for now if you
    are deploying GitLab in Step 4. You will return to fill these in after
    GitLab is running and you create the OAuth application.

## Step 3 -- Prepare the OIM and Infrastructure


Follow the same infrastructure preparation as Path B. These steps are
identical -- BuildStreaM automates the *deployment* workflow, not the
initial OIM setup.

**3a. Create the mapping file**

```shell title="Run on OIM (as root)"
cat > /opt/omnia/input/project_default/mapping.csv << 'EOF'
FUNCTIONAL_GROUP_NAME,GROUP_NAME,SERVICE_TAG,PARENT_SERVICE_TAG,HOSTNAME,ADMIN_MAC,ADMIN_IP,BMC_MAC,BMC_IP
slurm_control_node,slurm,SVCTAG01,,head01,24:6E:96:CC:01:01,10.5.0.101,,10.3.0.101
slurm_node,slurm,SVCTAG02,,compute01,24:6E:96:CC:01:02,10.5.0.102,,10.3.0.102
login_node,slurm,SVCTAG03,,login01,24:6E:96:CC:01:03,10.5.0.103,,10.3.0.103
service_kube_control_plane,kube,SVCTAG04,,kube-cp01,24:6E:96:CC:02:01,10.5.0.201,,10.3.0.201
service_kube_control_plane,kube,SVCTAG05,,kube-cp02,24:6E:96:CC:02:02,10.5.0.202,,10.3.0.202
service_kube_control_plane,kube,SVCTAG06,,kube-cp03,24:6E:96:CC:02:03,10.5.0.203,,10.3.0.203
service_kube_node,kube,SVCTAG07,,kube-wk01,24:6E:96:CC:02:04,10.5.0.204,,10.3.0.204
EOF
```


!!! warning

    Replace all placeholder values with your actual hardware data.

**3b. Copy input templates**

```shell title="Run on OIM (inside omnia_core container)"
cp -r /opt/omnia/examples/input_template/bare_metal_slurm/x86_64/with_service_k8s/* \
    /opt/omnia/input/project_default/
```


**3c. Edit network and provisioning inputs**

Edit `network_spec.yml`, `provision_config.yml`, and `ha_config.yml`
as described in [Full Deployment](full_deployment.md) Steps 5a--5c.

**3d. Set credentials**

```shell title="Run on OIM (inside omnia_core container)"
cd /opt/omnia
ansible-playbook credentials_utility.yml
```


**3e. Prepare the OIM**

```shell title="Run on OIM (inside omnia_core container)"
ansible-playbook prepare_oim.yml -i /opt/omnia/input/project_default/mapping.csv
```


**3f. Verify OIM services**

```shell title="Run on OIM (inside omnia_core container)"
systemctl list-dependencies omnia.target
```


**3g. Create local repos and build images**

```shell title="Run on OIM (inside omnia_core container)"
ansible-playbook local_repo.yml
ansible-playbook build_image_x86_64.yml

# Verify
s3cmd ls s3://omnia-images/
```


**3h. Discover and provision nodes**

```shell title="Run on OIM (inside omnia_core container)"
ansible-playbook discovery.yml

# Verify
ansible all -m ping -i /opt/omnia/inventories/project_default/inventory
```


**3i. Deploy Kubernetes service cluster**

```shell title="Run on OIM (inside omnia_core container)"
ansible-playbook k8s.yml

# Verify
export KUBECONFIG=/opt/omnia/k8s/admin.conf
kubectl get nodes
```



## Step 4 -- Deploy GitLab on the Service Cluster


If you do not have an existing GitLab instance, Omnia can deploy one on
the K8s service cluster.

```shell title="Run on OIM (inside omnia_core container)"
cd /opt/omnia
ansible-playbook build_stream_gitlab.yml
```


This playbook:

- Deploys GitLab CE as a Kubernetes workload on the service cluster.
- Configures persistent storage for Git repositories and CI/CD artifacts.
- Exposes GitLab on the K8s VIP at the port specified in
  `build_stream_config.yml`.
- Registers a GitLab Runner on the OIM for executing CI/CD pipelines.

```shell title="Run on OIM (inside omnia_core container)"
# Verify GitLab pods
export KUBECONFIG=/opt/omnia/k8s/admin.conf
kubectl get pods -n gitlab

# Get the GitLab service URL
kubectl get svc -n gitlab
```


!!! tip

    GitLab takes 5--10 minutes to fully initialize after the pods are
    `Running`. Wait for the readiness probe to succeed before accessing
    the UI:
    `kubectl wait --for=condition=ready pod -l app=gitlab -n gitlab --timeout=600s`

**4a. Access GitLab and create the OAuth application**

1. Open `http://<k8s_vip>:8080` in a browser.
2. Log in with the root credentials from the deployment output.
3. Navigate to **Admin Area > Applications > New Application**.
4. Fill in:

   - **Name:** `BuildStreaM`
   - **Redirect URI:** `http://10.5.0.10:8080/oauth/callback`
     (match `oauth_callback_url` in `build_stream_oauth_credentials.yml`)
   - **Scopes:** `api`, `read_user`, `read_repository`

5. Click **Save application** and copy the **Application ID** and **Secret**.

**4b. Update OAuth credentials**

```shell title="Run on OIM (inside omnia_core container)"
vi /opt/omnia/input/project_default/build_stream_oauth_credentials.yml
```


```yaml title="Updated build_stream_oauth_credentials.yml"
oauth_app_id: "your-application-id-from-gitlab"
oauth_app_secret: "your-secret-from-gitlab"
oauth_callback_url: "http://10.5.0.10:8080/oauth/callback"
```


!!! warning

    Treat the OAuth secret like a password. Do not commit it to a public
    Git repository. Use GitLab CI/CD variables (masked) for production
    environments.

## Step 5 -- Create the Cluster Catalog


The cluster catalog is a declarative YAML file that describes your entire
cluster: hardware inventory, software stack, network topology, and
deployment parameters. BuildStreaM parses this catalog to generate all
Omnia input files and orchestrate the deployment pipeline.

**5a. Initialize the catalog repository**

```shell title="Run on OIM (inside omnia_core container)"
cd /opt
git clone http://<k8s_vip>:8080/omnia/cluster-catalog.git
cd cluster-catalog
```


If the repository does not exist yet, create it in GitLab first:

1. In GitLab, go to **Projects > New Project > Create Blank Project**.
2. Name: `cluster-catalog`, Group: `omnia`, Visibility: **Private**.

**5b. Create the catalog file**

```shell title="Run on OIM (inside omnia_core container)"
vi /opt/cluster-catalog/catalog.yml
```


```yaml title="Example catalog.yml"
---
# BuildStreaM Cluster Catalog
# This file declaratively defines the target cluster state.

cluster:
  name: "production-hpc"
  domain: "omnia.local"
  timezone: "America/Chicago"

networks:
  admin:
    cidr: "10.5.0.0/16"
    gateway: "10.5.0.1"
    nic: "eno2"
  bmc:
    cidr: "10.3.0.0/16"
    nic: "eno2"

nodes:
  - hostname: head01
    service_tag: SVCTAG01
    role: slurm_control_node
    group: slurm
    admin_mac: "24:6E:96:CC:01:01"
    admin_ip: "10.5.0.101"
    bmc_ip: "10.3.0.101"

  - hostname: compute01
    service_tag: SVCTAG02
    role: slurm_node
    group: slurm
    admin_mac: "24:6E:96:CC:01:02"
    admin_ip: "10.5.0.102"
    bmc_ip: "10.3.0.102"

  - hostname: login01
    service_tag: SVCTAG03
    role: login_node
    group: slurm
    admin_mac: "24:6E:96:CC:01:03"
    admin_ip: "10.5.0.103"
    bmc_ip: "10.3.0.103"

  - hostname: kube-cp01
    service_tag: SVCTAG04
    role: service_kube_control_plane
    group: kube
    admin_mac: "24:6E:96:CC:02:01"
    admin_ip: "10.5.0.201"
    bmc_ip: "10.3.0.201"

  - hostname: kube-cp02
    service_tag: SVCTAG05
    role: service_kube_control_plane
    group: kube
    admin_mac: "24:6E:96:CC:02:02"
    admin_ip: "10.5.0.202"
    bmc_ip: "10.3.0.202"

  - hostname: kube-cp03
    service_tag: SVCTAG06
    role: service_kube_control_plane
    group: kube
    admin_mac: "24:6E:96:CC:02:03"
    admin_ip: "10.5.0.203"
    bmc_ip: "10.3.0.203"

  - hostname: kube-wk01
    service_tag: SVCTAG07
    role: service_kube_node
    group: kube
    admin_mac: "24:6E:96:CC:02:04"
    admin_ip: "10.5.0.204"
    bmc_ip: "10.3.0.204"

software:
  os_iso: "/opt/isos/RHEL-8.8-x86_64-dvd.iso"
  slurm: true
  kubernetes: true
  telemetry: true
  auth_type: "freeipa"
  realm: "OMNIA.LOCAL"

kubernetes:
  ha_vip: "10.5.0.250"
  ha_interface: "eno2"

telemetry:
  idrac_telemetry: true
  ldms_telemetry: true
  grafana_port: 3000
  retention: "30d"
```


!!! tip

    The catalog format is designed to be human-readable and diff-friendly.
    Store it in Git so that every cluster change is tracked as a commit.
    Review changes via merge requests before deploying.

**5c. Create the CI/CD pipeline definition**

```shell title="Run on OIM (inside omnia_core container)"
vi /opt/cluster-catalog/.gitlab-ci.yml
```


```yaml title=".gitlab-ci.yml"
---
stages:
  - validate
  - generate
  - deploy
  - verify

variables:
  OMNIA_HOME: "/opt/omnia"
  INPUT_DIR: "/opt/omnia/input/project_default"
  CATALOG_FILE: "catalog.yml"

validate_catalog:
  stage: validate
  tags:
    - omnia-oim
  script:
    - cd ${OMNIA_HOME}
    - python3 scripts/buildstream/validate_catalog.py ${CI_PROJECT_DIR}/${CATALOG_FILE}
  rules:
    - if: '$CI_PIPELINE_SOURCE == "push"'

generate_inputs:
  stage: generate
  tags:
    - omnia-oim
  script:
    - cd ${OMNIA_HOME}
    - python3 scripts/buildstream/generate_inputs.py ${CI_PROJECT_DIR}/${CATALOG_FILE} ${INPUT_DIR}
  artifacts:
    paths:
      - ${INPUT_DIR}/*.yml
      - ${INPUT_DIR}/*.json
      - ${INPUT_DIR}/*.csv
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'

deploy_cluster:
  stage: deploy
  tags:
    - omnia-oim
  script:
    - cd ${OMNIA_HOME}
    - ansible-playbook omnia.yml
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
    - when: manual

verify_cluster:
  stage: verify
  tags:
    - omnia-oim
  script:
    - cd ${OMNIA_HOME}
    - ansible-playbook verify_cluster.yml
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
```


!!! warning

    The `deploy_cluster` stage is set to `when: manual` on the
    `main` branch by default. This means a human must click **Play** in
    the GitLab pipeline UI to trigger the deployment. Remove the
    `when: manual` rule for fully unattended deployments, but only after
    validating the pipeline on a test cluster.

## Step 6 -- Push the Catalog and Trigger the Pipeline


```shell title="Run on OIM (inside omnia_core container)"
cd /opt/cluster-catalog

git add catalog.yml .gitlab-ci.yml
git commit -m "Initial cluster catalog for production-hpc"
git push origin main
```


This push triggers the BuildStreaM pipeline:

1. **Validate** -- Checks the catalog for syntax errors, missing fields,
   IP conflicts, and role-count constraints (e.g., 3 K8s control-plane
   nodes).
2. **Generate** -- Translates the catalog into Omnia input files
   (`mapping.csv`, `network_spec.yml`, `omnia_config.yml`, etc.) and
   stores them as pipeline artifacts.
3. **Deploy** -- *(Manual trigger)* Runs `omnia.yml` to deploy the
   full cluster.
4. **Verify** -- Runs post-deployment verification (`sinfo`,
   `kubectl get nodes`, telemetry health checks).

**Monitor the pipeline:**

1. Open GitLab at `http://<k8s_vip>:8080`.
2. Navigate to **omnia/cluster-catalog > CI/CD > Pipelines**.
3. Click the pipeline to see per-stage logs in real time.

```shell title="Run on OIM (inside omnia_core container)"
# Alternatively, monitor from the CLI
gitlab-runner status
# Watch the pipeline log from the runner
tail -f /var/log/gitlab-runner/runner.log
```


!!! tip

    If the **Validate** stage fails, read the error output -- it tells you
    exactly which catalog field is invalid (e.g., ``"Node kube-cp04 has
    role service_kube_control_plane but only 4 control-plane nodes are
    defined. Expected odd number (3 or 5)."``). Fix the catalog, commit,
    and push to re-trigger.

## Step 7 -- Verify the Deployment


After the pipeline completes (all stages green), verify the cluster.

**Slurm verification:**

```shell title="Run on head node (head01)"
ssh head01
sinfo
srun -N 1 hostname
sacctmgr show cluster
```


**Kubernetes verification:**

```shell title="Run on OIM (inside omnia_core container)"
export KUBECONFIG=/opt/omnia/k8s/admin.conf
kubectl get nodes
kubectl get pods --all-namespaces | grep -v Running | grep -v Completed
```


**Telemetry verification:**

```shell title="Run on OIM (inside omnia_core container)"
kubectl get pods -n omnia-telemetry
# Open Grafana at http://<k8s_vip>:3000
```


**BuildStreaM pipeline verification:**

```shell title="Run on OIM (inside omnia_core container)"
# Verify the pipeline artifacts were generated correctly
ls -la /opt/omnia/input/project_default/

# Verify the GitLab Runner is registered and online
gitlab-runner list
```



## Day-2 Operations with BuildStreaM


BuildStreaM is designed for ongoing cluster management, not just initial
deployment.

**Scaling out compute nodes**

1. Add new `slurm_node` entries to `catalog.yml`.
2. Commit and push.
3. The pipeline re-validates, regenerates `mapping.csv`, and runs
   discovery + deployment for the new nodes only.

**Changing software configuration**

1. Edit the `software` section of `catalog.yml` (e.g., enable GPU
   drivers, change Slurm version).
2. Commit and push.
3. The pipeline regenerates `software_config.json` and re-runs
   `omnia.yml` (idempotent -- only changed configs are applied).

**Rolling back a change**

1. `git revert HEAD` to undo the last commit.
2. Push. The pipeline redeploys the previous catalog state.

!!! tip

    Use GitLab **merge requests** with required approvals for production
    clusters. This ensures that catalog changes are reviewed by a second
    engineer before being deployed. Set up **protected branches** on
    `main` so that only merged MRs trigger the deploy stage.

**Disaster recovery**

If the cluster needs to be rebuilt from scratch (e.g., after a datacenter
move):

```shell title="Run on OIM (as root)"
# Re-clone the catalog repository
cd /opt
git clone http://<gitlab_url>/omnia/cluster-catalog.git
cd cluster-catalog

# Trigger a full rebuild
git commit --allow-empty -m "Rebuild cluster from catalog"
git push origin main
```


The pipeline will re-provision all nodes and redeploy the entire stack
using the catalog as the single source of truth.


## What's Next?


**Integrate with external CI/CD systems**
   If your organization uses Jenkins, GitHub Actions, or Azure DevOps
   instead of GitLab, you can call BuildStreaM's catalog validation and
   input generation scripts as build steps in those systems.

**Multi-cluster management**
   Create separate catalog repositories for each cluster (dev, staging,
   production). Each repository has its own pipeline and can be deployed
   independently.

**Custom pipeline stages**
   Add stages for workload deployment (e.g., deploying MPI benchmarks,
   AI training frameworks) after the `verify` stage.

**Automated testing**
   Add integration tests to the `verify` stage (e.g., run a small
   Slurm job, verify Grafana data sources, check NFS mounts).

!!! info

    - [Full Deployment](full_deployment.md) -- Manual equivalent of this automated path
    - [Prerequisites Checklist](prerequisites_checklist.md) -- Master checklist
    - [Slurm Quickstart](slurm_quickstart.md) -- Simplified manual deployment for comparison
