# OpenCHAMI issues

Use this page to diagnose the Fabrica-based OpenCHAMI stack deployed by Omnia
2.3. The current stack uses `boot-service`, `metadata-service`, `tokensmith`,
and SMD. Commands for the retired BSS, cloud-init-server, Hydra, and OPAAL
services do not apply to this release.

## Establish a baseline

Run the supported deployment validation first:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM host"
    cd <OMNIA_SOURCE_PATH>/src/main
    source /etc/profile.d/omnia-env.sh
    ./omnia.sh --run orchestrator --tags validate-deployment
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM host"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
    ansible-playbook orchestrator.yml --tags validate-deployment
    ```

If validation fails, inspect the target and its generated dependencies on the
OIM:

```bash title="Run on: OIM"
systemctl status openchami.target --no-pager
systemctl list-dependencies openchami.target --plain
systemctl --failed --no-pager
podman ps -a --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'
```

Use the dependency list rather than a copied list of services. The RPM owns
the Quadlet definitions, so the exact dependency set can change with the
packaged OpenCHAMI version.

For the services checked directly by Orchestrator, collect these journals and
container logs:

```bash title="Run on: OIM"
journalctl -u openchami.target -b -n 100 --no-pager
journalctl -u tokensmith -b -n 100 --no-pager
journalctl -u smd -b -n 100 --no-pager
journalctl -u boot-service -b -n 100 --no-pager
journalctl -u metadata-service -b -n 100 --no-pager
podman logs --tail 100 smd
podman logs --tail 100 haproxy
```

## `openchami.target` is not active

???+ note "Symptom"

    The `prepare`, `provision`, or `validate-deployment` flow reports that
    `openchami.target`, `boot-service`, `tokensmith`, or SMD is unavailable.

??? note "Cause"

    Common causes include an incomplete `prepare` run, a failed Quadlet
    dependency, a port conflict, an unavailable container image, an SMD
    database failure, or an expired OpenCHAMI certificate.

??? note "Resolution"

    1. Identify the first failed dependency:

        ```bash title="Run on: OIM"
        systemctl list-dependencies openchami.target --plain
        systemctl --failed --no-pager
        journalctl -u openchami.target -b --no-pager
        ```

    2. Correct that service's reported cause. If the stack was previously
       healthy, restart the target and recheck it:

        ```bash title="Run on: OIM"
        systemctl restart openchami.target
        systemctl is-active openchami.target
        ```

    3. If deployment did not complete, run the complete preparation flow. It
       collects required credentials, deploys the services, and validates
       readiness:

        === "Using omnia.sh (recommended)"

            ```bash title="Run on: OIM host"
            cd <OMNIA_SOURCE_PATH>/src/main
            ./omnia.sh --run orchestrator --tags prepare
            ```

        === "Using ansible-playbook"

            ```bash title="Run on: OIM host"
            source /opt/omnia/activate-omnia.sh
            cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
            ansible-playbook orchestrator.yml --tags prepare
            ```

    4. Run `validate-deployment` before provisioning nodes again.

## Certificate or authentication failure

???+ note "Symptom"

    OpenCHAMI requests fail with a TLS error or `401 Unauthorized`, token
    generation fails, or SMD becomes unreachable through HAProxy.

??? note "Cause"

    The site certificate may be expired or inconsistent with the configured
    OIM FQDN, `tokensmith` may be unavailable, or the current shell may not
    contain a fresh access token.

??? note "Resolution"

    1. Load the active environment and verify the configured OIM identity:

        ```bash title="Run on: OIM"
        source /etc/profile.d/omnia-env.sh
        printf '%s\n' "$SYSTEM_HOSTNAME.$SYSTEM_DOMAIN_NAME"
        systemctl status tokensmith acme-deploy --no-pager
        ```

    2. Inspect the certificate presented by HAProxy:

        ```bash title="Run on: OIM"
        openssl s_client -connect localhost:8443 -servername "$SYSTEM_HOSTNAME.$SYSTEM_DOMAIN_NAME" \
          </dev/null 2>/dev/null | openssl x509 -noout -subject -issuer -dates
        ```

    3. If the certificate is expired or has the wrong FQDN, regenerate it with
       the same identity and restart the certificate service and target:

        ```bash title="Run on: OIM"
        openchami-certificate-update update "$SYSTEM_HOSTNAME.$SYSTEM_DOMAIN_NAME"
        systemctl restart acme-deploy
        systemctl restart openchami.target
        ```

    4. Prefer rerunning the Orchestrator flow to obtain a fresh token. For a
       one-time CLI diagnostic, generate the token without displaying it:

        ```bash title="Run on: OIM"
        token_name="$(hostname -s | tr '[:lower:]' '[:upper:]')_ACCESS_TOKEN"
        token_value="$(sudo bash -lc 'gen_access_token')"
        export "$token_name=$token_value"
        unset token_value
        ochami smd service status
        ```

       Do not write the token to a file or include it in diagnostic output.

## SMD node discovery fails

???+ note "Symptom"

    The `provision` flow reports `Failed to discover ochami nodes`, or the
    expected nodes are absent from `ochami smd component get`.

??? note "Cause"

    SMD may be unhealthy, the generated node document may not match the
    current PXE mapping, or the mapping may contain invalid or duplicate
    hardware identifiers.

??? note "Resolution"

    1. Check SMD and its backing container:

        ```bash title="Run on: OIM"
        systemctl status smd --no-pager
        podman logs --tail 100 smd
        ochami smd service status
        ```

    2. Review the active project mapping and generated per-category OpenCHAMI
       node files:

        ```bash title="Run on: OIM"
        source /etc/profile.d/omnia-env.sh
        orchestrator_path="${ORCHESTRATOR_DATA_PATH:-${OMNIA_DATA_PATH}/orchestrator}"
        sed -n '1,20p' "$orchestrator_path/input/$OMNIA_PROJECT_NAME/pxe_mapping_file.csv"
        ls -1 "$OMNIA_DATA_PATH/openchami/workdir/nodes"/nodes_*.yaml
        sed -n '1,120p' "$OMNIA_DATA_PATH/openchami/workdir/nodes"/nodes_*.yaml
        ```

    3. Correct the mapping, then run `validate`, `precheck`, and `provision`.
       Do not edit generated files such as `nodes_slurm.yaml`,
       `nodes_kubernetes.yaml`, `nodes_os.yaml`, or `nodes_custom.yaml`;
       Orchestrator replaces them from the mapping.

## Boot configuration is missing or stale

???+ note "Symptom"

    A node boots the wrong functional-group image, or its boot configuration
    has missing kernel, initrd, or rootfs artifacts.

??? note "Cause"

    The functional-group image may be absent from Image Build Manager's
    successful `build_status.yml`, a MAC address may not match the physical
    node, or provisioning may not have refreshed `boot-service` after the
    mapping or image changed.

??? note "Resolution"

    1. Confirm Image Build Manager reports success and contains the affected
       functional group.
    2. Compare the mapping's `ADMIN_MAC` and service tag with the hardware.
    3. With a valid access token, list current boot configurations:

        ```bash title="Run on: OIM"
        ochami boot config list -F json | jq .
        ```

    4. Rebuild the missing image when necessary. Then run Orchestrator
       `precheck` and `provision` to regenerate boot and metadata-service
       configuration.

## Metadata service is not reachable

???+ note "Symptom"

    Orchestrator cannot reach `/metadata-service/health`, or a node boots but
    cloud-init cannot download its NoCloud data.

??? note "Cause"

    `metadata-service` or HAProxy may be down, the OIM FQDN may resolve to the
    wrong address, internal Podman-network traffic to TCP 8080 may be broken,
    or the externally exposed HAProxy endpoint on TCP 8443 may be blocked.
    TCP 8081 belongs to `boot-service`; it is not the metadata-service port.

??? note "Resolution"

    ```bash title="Run on: OIM"
    source /etc/profile.d/omnia-env.sh
    systemctl status metadata-service openchami.target --no-pager
    journalctl -u metadata-service -b -n 100 --no-pager
    podman logs --tail 100 haproxy
    curl --fail --silent --show-error --insecure \
      "https://$SYSTEM_HOSTNAME.$SYSTEM_DOMAIN_NAME:8443/metadata-service/health"
    ```

    Restore DNS, firewall, or service health as indicated, restart
    `openchami.target` if required, and rerun `validate-deployment`.

## Cloud-init fails on a provisioned node

???+ note "Symptom"

    PXE boot succeeds, but `cloud-init status --long` reports an error or the
    expected Slurm/Kubernetes configuration is absent.

??? note "Cause"

    Typical causes are metadata-service connectivity, invalid generated
    user-data, unavailable repositories, certificate trust, or a failed NFS
    mount used by a provisioning script.

??? note "Resolution"

    1. Collect evidence on the node before rebooting or reprovisioning it:

        ```bash title="Run on: affected node"
        cloud-init status --long
        journalctl -u cloud-init -b --no-pager
        tail -n 200 /var/log/cloud-init-output.log
        cloud-init query userdata
        findmnt -t nfs,nfs4
        ```

    2. From the affected node, verify the metadata URL shown in its kernel
       command line is reachable. From the OIM, check `metadata-service` and
       HAProxy logs.
    3. Correct the source input or external dependency and regenerate content
       with `precheck` and `provision`.
    4. PXE boot the reviewed node or subset again. Do not run `cloud-init
       clean` followed by a reboot as a generic recovery step; that can rerun
       destructive initialization against an already configured node.

For a support bundle, use [Collect Cluster Logs](../../Operations/collect_cluster_logs.md).

## Recreate only the OpenCHAMI deployment

Use component cleanup only after collecting logs and confirming that existing
OpenCHAMI state can be removed:

```bash title="Run on: OIM"
source /opt/omnia/activate-omnia.sh
cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks/cleanup
ansible-playbook cleanup_orchestrator.yml --tags openchami
```

After component cleanup completes, rerun the recovery sequence:

=== "Using omnia.sh (recommended)"

    ```bash title="Run on: OIM"
    cd <OMNIA_SOURCE_PATH>/src/main
    ./omnia.sh --run orchestrator --tags prepare
    ./omnia.sh --run orchestrator --tags validate-deployment
    ./omnia.sh --run orchestrator --tags provision
    ```

=== "Using ansible-playbook"

    ```bash title="Run on: OIM"
    source /opt/omnia/activate-omnia.sh
    cd <OMNIA_SOURCE_PATH>/src/orchestrator/playbooks
    ansible-playbook orchestrator.yml --tags prepare
    ansible-playbook orchestrator.yml --tags validate-deployment
    ansible-playbook orchestrator.yml --tags provision
    ```

`prepare` is required in this recovery sequence because it performs credential
handling, deployment, and readiness validation. Running `deploy` followed
directly by `provision` omits those preparation steps.
