
# Deploy GitLab


Deploy and configure GitLab for BuildStreaM CI/CD pipelines that automate
catalog-driven cluster deployment.

## Overview


BuildStreaM uses GitLab as the CI/CD engine to execute catalog-driven
deployment pipelines. GitLab stores:

- The **catalog file** that declaratively defines cluster configuration.
- **Pipeline definitions** (`.gitlab-ci.yml`) that execute Omnia playbooks.
- **Artifacts** (logs, reports) from each pipeline run.

Omnia can deploy GitLab as a Podman container on the OIM or as a Helm
deployment on the K8s service cluster.


## Prerequisites


- The [Prepare Oim](../Setup/prepare_oim.md) procedure is complete.
- At least 8 GB RAM available for the GitLab container (16 GB recommended).
- At least 50 GB disk space for GitLab data.
- A DNS name or IP address for GitLab access.
- The K8s service cluster is deployed (if using Helm deployment).


## Procedure


### Option A: Deploy GitLab on the OIM (Podman)


1. **Create persistent storage directories**:

   ```bash title="Run on: OIM host"
   mkdir -p /opt/gitlab/{config,logs,data}
   ```


2. **Deploy the GitLab container**:

   ```bash title="Run on: OIM host"
   podman run -d \
     --name gitlab \
     --restart=always \
     --hostname gitlab.omnia.local \
     -p 8443:443 \
     -p 8082:80 \
     -p 2222:22 \
     -v /opt/gitlab/config:/etc/gitlab:Z \
     -v /opt/gitlab/logs:/var/log/gitlab:Z \
     -v /opt/gitlab/data:/var/opt/gitlab:Z \
     --shm-size 256m \
     docker.io/gitlab/gitlab-ce:latest
   ```


   !!! note

       GitLab takes **3-5 minutes** to fully initialize after the container
       starts. Wait before proceeding.

3. **Retrieve the initial root password**:

   ```bash title="Run on: OIM host"
   podman exec gitlab cat /etc/gitlab/initial_root_password
   ```


   Save this password; it is only available for 24 hours.

4. **Access GitLab** in a browser: `http://<oim-ip>:8082`

   Log in with:

   - Username: `root`
   - Password: (from step 3)

5. **Create the BuildStreaM project**:

   ```bash title="Run on: OIM host"
   # Using GitLab API
   curl -s -X POST "http://localhost:8082/api/v4/projects" \
     -H "PRIVATE-TOKEN: <your-root-token>" \
     -d "name=buildstream-catalog&visibility=private"
   ```


6. **Register a GitLab Runner** for pipeline execution:

   ```bash title="Run on: OIM host"
   podman run -d \
     --name gitlab-runner \
     --restart=always \
     -v /opt/gitlab-runner:/etc/gitlab-runner:Z \
     -v /var/run/podman/podman.sock:/var/run/docker.sock:Z \
     docker.io/gitlab/gitlab-runner:latest

   podman exec gitlab-runner gitlab-runner register \
     --non-interactive \
     --url "http://<oim-ip>:8082" \
     --token "<runner-registration-token>" \
     --executor "shell" \
     --description "omnia-runner"
   ```



### Option B: Deploy GitLab on K8s (Helm)


7. **(Alternative) Deploy GitLab via Helm**:

   ```bash title="Run on: K8s control plane node"
   helm repo add gitlab https://charts.gitlab.io/
   helm repo update

   helm install gitlab gitlab/gitlab \
     --namespace gitlab \
     --create-namespace \
     --set global.hosts.domain=omnia.local \
     --set global.hosts.externalIP=<metallb-ip> \
     --set certmanager.install=false \
     --set global.ingress.configureCertmanager=false \
     --set gitlab-runner.install=true \
     --set persistence.enabled=true \
     --timeout 600s
   ```



### Configure GitLab for BuildStreaM


8. **Clone the BuildStreaM catalog repository** template:

   ```bash title="Run on: omnia_core container"
   cd /opt/omnia
   git clone http://<oim-ip>:8082/root/buildstream-catalog.git
   cd buildstream-catalog
   ```


9. **Create the pipeline configuration**:

   ```bash title="Run on: omnia_core container"
   cat <<'EOF' > .gitlab-ci.yml
   stages:
     - validate
     - provision
     - configure
     - verify

   validate_catalog:
     stage: validate
     script:
       - cd /omnia
       - ansible-playbook input_validator.yml

   provision_nodes:
     stage: provision
     script:
       - cd /omnia/discovery
       - ansible-playbook discovery.yml --ask-vault-pass
     when: manual

   configure_cluster:
     stage: configure
     script:
       - cd /omnia
       - ansible-playbook omnia.yml --ask-vault-pass
     when: manual

   verify_cluster:
     stage: verify
     script:
       - ansible all -m ping
       - ssh <slurm-control-ip> sinfo
   EOF
   ```


10. **Push the initial configuration**:

    ```bash title="Run on: omnia_core container"
    git add .
    git commit -m "Initial BuildStreaM catalog"
    git push origin main
    ```



## Verification


1. **Verify GitLab is running**:

   ```bash title="Run on: OIM host"
   podman ps --filter name=gitlab
   curl -s http://localhost:8082/users/sign_in | grep "GitLab"
   ```


2. **Verify the runner is registered**:

   ```bash title="Run on: OIM host"
   podman exec gitlab-runner gitlab-runner list
   ```


3. **Trigger a test pipeline** by pushing a commit or via the GitLab UI:

   Navigate to **CI/CD** > **Pipelines** in the GitLab web UI and confirm
   the pipeline stages appear.


## Next Steps


- [Update Catalog Pipeline](update_catalog_pipeline.md) -- Update the catalog and run pipelines.
- [Buildstream Troubleshooting](buildstream_troubleshooting.md) -- Troubleshoot pipeline issues.


## Troubleshooting


**GitLab container takes too long to start**
   Check container logs:

   ```bash title="Run on: OIM host"
   podman logs -f gitlab
   ```


**"502 Bad Gateway" in browser**
   GitLab is still initializing. Wait 3-5 minutes and try again.

**Runner registration fails**
   Verify the registration token from GitLab's admin area:
   **Admin Area** > **CI/CD** > **Runners**

**Insufficient memory**
   GitLab requires at least 8 GB RAM. Check available memory:

   ```bash title="Run on: OIM host"
   free -h
   ```


**Port conflicts**
   Ensure ports 8082, 8443, and 2222 are not in use:

   ```bash title="Run on: OIM host"
   ss -tlnp | grep -E ':(8082|8443|2222)\b'
   ```
