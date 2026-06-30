
# BuildStreaM Troubleshooting


Diagnose and resolve common BuildStreaM issues including pipeline failures,
registry problems, GitLab errors, and runner configuration issues.

## Overview


BuildStreaM integrates multiple components: GitLab, GitLab Runner, the local
container registry, and the Omnia playbook engine. Failures can occur at any
stage. This guide provides systematic troubleshooting for each component.


## Prerequisites


- GitLab is deployed (see [Deploy Gitlab](deploy_gitlab.md)).
- A BuildStreaM catalog is configured (see [Update Catalog Pipeline](update_catalog_pipeline.md)).
- `root` or `sudo` access to the OIM host and the omnia_core container.


## Procedure


### Pipeline Failures


1. **View pipeline logs** in GitLab:

   Navigate to **CI/CD** > **Pipelines** > click the failed pipeline > click
   the failed job. Read the job output from bottom to top for the error.

2. **Common validation-stage failures**:

   ```bash title="Run on: omnia_core container"
   # Manually re-run validation to see errors
   cd /omnia
   ansible-playbook input_validator.yml -v
   ```


   Common causes:

   - `catalog.yml` YAML syntax error
   - Missing required fields
   - IP address outside configured range
   - Duplicate service tags or MAC addresses

3. **Common provision-stage failures**:

   ```bash title="Run on: omnia_core container"
   # Test BMC connectivity for a specific node
   curl -sk https://<bmc-ip>/redfish/v1/ -u root:<password>
   ```


   Common causes:

   - BMC unreachable (network or credential issue)
   - PXE boot failure (check DHCP and TFTP services)
   - Vault password not available to runner

4. **Common configure-stage failures**:

   ```bash title="Run on: omnia_core container"
   # Test node connectivity
   ansible all -m ping -v
   ```


   Common causes:

   - Node not reachable (provisioning incomplete)
   - Package installation failure (repo sync issue)
   - Service startup failure on target node


### GitLab Issues


5. **GitLab is unresponsive or slow**:

   ```bash title="Run on: OIM host"
   podman stats gitlab --no-stream
   podman logs gitlab --tail=30
   ```


   If memory is exhausted, increase the container memory limit or add swap:

   ```bash title="Run on: OIM host"
   # Check available memory
   free -h

   # Restart GitLab with more memory
   podman stop gitlab
   podman rm gitlab
   # Re-create with --memory=16g flag
   ```


6. **GitLab "502 Bad Gateway"**:

   ```bash title="Run on: OIM host"
   # GitLab internal services may be restarting
   podman exec gitlab gitlab-ctl status

   # Restart GitLab services
   podman exec gitlab gitlab-ctl restart
   ```


7. **GitLab database migration errors**:

   ```bash title="Run on: OIM host"
   podman exec gitlab gitlab-rake db:migrate
   podman exec gitlab gitlab-ctl reconfigure
   ```



### Runner Issues


8. **Runner is offline or not picking up jobs**:

   ```bash title="Run on: OIM host"
   podman exec gitlab-runner gitlab-runner list
   podman exec gitlab-runner gitlab-runner verify
   ```


   If the runner is stale, re-register it:

   ```bash title="Run on: OIM host"
   podman exec gitlab-runner gitlab-runner unregister --all-runners
   podman exec gitlab-runner gitlab-runner register \
     --non-interactive \
     --url "http://<oim-ip>:8082" \
     --token "<new-registration-token>" \
     --executor "shell" \
     --description "omnia-runner"
   ```


9. **Runner fails with "permission denied"**:

   Ensure the runner has access to the omnia_core container and playbooks:

   ```bash title="Run on: OIM host"
   podman exec gitlab-runner ls /omnia/
   # If not mounted, add a volume mount when re-creating the runner container
   ```


10. **Runner jobs time out**:

    Increase the job timeout in GitLab:

    - Navigate to **Settings** > **CI/CD** > **General pipelines** > **Timeout**.
    - Set to `2 hours` or longer for provisioning jobs.


### Registry Issues


11. **Container registry is unreachable**:

    ```bash title="Run on: OIM host"
    systemctl status registry.service
    podman logs registry
    ```


    Restart the registry:

    ```bash title="Run on: OIM host"
    systemctl restart registry.service
    ```


12. **Image push/pull fails**:

    ```bash title="Run on: OIM host"
    # Test registry connectivity
    curl -s http://localhost:5000/v2/_catalog
    ```


    If using HTTPS with self-signed certificates, add the registry to the
    insecure registries list:

    ```bash title="Run on: OIM host"
    cat /etc/containers/registries.conf | grep insecure
    ```



### General Debugging


13. **Enable verbose Ansible output** in pipelines:

    Edit `.gitlab-ci.yml` to add `-vvv` to playbook commands:

    ```yaml title="File: .gitlab-ci.yml"
    configure_cluster:
      stage: configure
      script:
        - cd /omnia
        - ansible-playbook omnia.yml --ask-vault-pass -vvv
    ```


14. **Check system resources** on the OIM:

    ```bash title="Run on: OIM host"
    # Check disk space
    df -h

    # Check memory
    free -h

    # Check running containers
    podman ps -a

    # Check container resource usage
    podman stats --no-stream
    ```



## Verification


After resolving issues, verify the pipeline works end-to-end:

1. **Make a trivial change** to the catalog (e.g., add a comment).
2. **Push the change** and verify the validation stage passes.
3. **Trigger the full pipeline** and confirm all stages complete.

```bash title="Run on: omnia_core container"
cd /opt/omnia/buildstream-catalog
echo "# Test commit $(date)" >> catalog.yml
git add catalog.yml
git commit -m "Test pipeline trigger"
git push origin main
```



## Next Steps


- [Update Catalog Pipeline](update_catalog_pipeline.md) -- Resume catalog-driven deployments.
- [Deploy Gitlab](deploy_gitlab.md) -- Reconfigure GitLab if needed.


## Troubleshooting


!!! note

    This page **is** the troubleshooting reference for BuildStreaM. For
    issues not covered here:

    - Check GitLab logs: `podman logs gitlab`
    - Check runner logs: `podman logs gitlab-runner`
    - Check Omnia playbook logs inside the omnia_core container.
    - Refer to the [GitLab documentation](https://docs.gitlab.com/) for
      GitLab-specific issues.
    - Open an issue on the `Omnia GitHub repository
      <https://github.com/dell/omnia/issues>`_ for Omnia-specific issues.
