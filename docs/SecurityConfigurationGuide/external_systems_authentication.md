# Authentication to External Systems

Omnia connects to external systems only when the corresponding domain or
feature is enabled. The table describes the RC1 implementation boundary. It
does not replace the external system's account, certificate, rotation, audit,
or retention policy.

| External system | When used and connection direction | Authentication and secret source | TLS and server trust | Secret handling boundary |
|---|---|---|---|---|
| OpenManage Enterprise (OME) | Discovery connects from the OIM to the OME HTTPS API. OME Telemetry can also send events through the Telemetry Kafka external listener. | Discovery uses `ome_username` and `ome_password` from `discovery_credentials.yml` and exchanges them for an OME session token. OME Telemetry uses generated Kafka client certificate material. | The Discovery HTTPS client currently disables server-certificate verification. The Telemetry Kafka external listener uses mTLS. | Protect the Discovery Vault file and the exported Kafka client key. Rotate the OME credentials or client certificate according to the corresponding external-system procedure. |
| iDRAC/BMC | Discovery, Orchestrator, unattended OS installation, and iDRAC Telemetry connect from the OIM or Telemetry services to Redfish/iDRAC endpoints. | Each owning domain uses its own `bmc_username` and `bmc_password` Vault entries; values with the same names are not shared automatically across domains. | HTTPS is used, but the current Redfish workflows disable server-certificate validation. Isolate the BMC network and do not treat HTTPS alone as verified server identity. | Credentials begin in the owning domain's Vault file and are supplied to the workflow that contacts the BMC. Telemetry can copy required values into Kubernetes Secrets. |
| Managed GitLab | The OIM configures the GitLab host and calls its HTTPS API; the GitLab runner connects to GitLab and the BuildStreaM API. The OIM also uses SSH to administer the GitLab host. | `gitlab_root_password`, the derived root access token, runner/project tokens, and `gitlab_ssh_password` originate from the BuildStreaM credential workflow. Initial host access uses the SSH password; the role installs an SSH public key. | GitLab uses an Omnia-generated HTTPS certificate. The deployment's GitLab API calls currently disable certificate verification. The runner is supplied with the generated CA material. | The Vault file protects source credentials. GitLab tokens and BuildStreaM values are also installed as GitLab CI/CD variables; masked variables reduce display but remain accessible to authorized jobs and administrators. |
| Container registries, including Docker Hub | Repo Manager connects to configured upstream registries; Image Build Manager and BuildStreaM pull or push images when required. | A registry can use no authentication or basic authentication. Usernames, passwords, or tokens referenced by `vault_path`, and optional Docker Hub credentials, are stored in the Repo Manager Vault file. | Private registries can use a CA file or an mTLS client certificate and key. `tls.insecure: true` disables verification and is intended only for controlled testing. Plain HTTP is schema-compatible but is not recommended for production. | Registry credentials are supplied to the Pulp remote or container client. Do not place them in catalog, status, or log output. External registry access and rotation remain the registry administrator's responsibility. |
| Pulp | The OIM and local consumers connect to the Pulp service deployed by Repo Manager. | The Pulp administrator username and password are stored in `repo_manager_config_credentials.yml`; Pulp API and CLI access uses those credentials. | Pulp is exposed through HTTPS with an Omnia-generated CA and server certificate. Managed CLI paths use that CA for verification. | Pulp credentials remain in the Repo Manager Vault file, while Pulp maintains its own database and service state under the configured Pulp storage paths. |
| MinIO or external PowerScale S3 | Image Build Manager and BuildStreaM use the selected S3-compatible object store. | `s3_access_id` and `s3_secret_key` are stored in `image_build_credentials.yml`. | The locally managed MinIO connection is HTTP. An external PowerScale endpoint can be HTTP or HTTPS, but the generated S3 client configuration currently disables certificate and hostname verification. Use a trusted management network until verification is enforced. | Access keys are rendered into the service/client configuration that requires them. Storage-side account permissions, rotation, object retention, and encryption remain external responsibilities. |
| PowerScale CSI | The Kubernetes CSI driver connects from the service cluster to the configured PowerScale endpoint. | Orchestrator or Telemetry obtains `csi_username` and `csi_password` from its domain Vault file and creates a Kubernetes Secret for the driver. | Transport behavior follows the configured endpoint and CSI settings. Validate the array certificate and network design for the selected deployment. | Kubernetes Secret data is base64-encoded, not encrypted at rest unless Kubernetes encryption is configured separately. Apply Kubernetes RBAC and secret-encryption controls. |
| UFM | When UFM metrics or events are enabled, Telemetry collectors connect from the service Kubernetes cluster to the configured UFM endpoint. | `auth_mode: basic` uses `ufm_username` and `ufm_password` from `telemetry_credentials.yml`; `auth_mode: none` sends no credentials. | `tls_mode: ca_signed` uses the configured CA. `tls_mode: self_signed` skips server-certificate verification. | Telemetry renders the selected credentials into Kubernetes Secret data for the collector. Limit Secret access and rotate the UFM account externally. |
| VAST | When VAST metrics or logs are enabled, Telemetry collectors connect from the service Kubernetes cluster to VAST Prometheus and syslog endpoints. | `auth_mode: basic` uses `vast_username` and `vast_password` from `telemetry_credentials.yml`; `auth_mode: none` sends no credentials. | CA-signed mode uses the configured CA. Self-signed mode skips verification. Syslog TLS requires the selected VAST and VLAgent certificate configuration. | Telemetry renders credentials and certificate material into Kubernetes resources. VAST owns the endpoint account, certificate, and server-side retention policy. |
| LDAP/OpenLDAP | When the catalog enables OpenLDAP, Omnia deploys the authentication service on the OIM and configures supported Slurm nodes as clients. | `openldap_db_username` and `openldap_db_password` are stored in `orchestrator_credentials.yml`. LDAP users and groups are created and maintained by the site administrator, not by Omnia. | `security_config.yml` selects LDAP with StartTLS or LDAPS. Clients must trust the certificate configured for that selection. | Protect the Orchestrator Vault file, LDAP database, and generated client configuration. LDAP account lifecycle and password policy are administrator responsibilities. |
| Additional Telemetry sinks | VMagent or VLAgent sends data from the service Kubernetes cluster to configured external VictoriaMetrics, VictoriaLogs, or syslog destinations. | The generic remote-write sink configuration does not define an authentication-secret contract. Configure access at the destination or network boundary when authentication is required. | Remote-write endpoints support TLS with an `insecureSkipVerify` choice; keep verification enabled and provide trusted certificates. Syslog can use plaintext or TLS according to its configuration. | Do not assume that an external sink is authenticated or that its data is encrypted at rest. The destination administrator owns access, certificate, retention, and backup policy. |

Credential YAML files are encrypted with Ansible Vault and assigned restrictive
permissions, but this protection does not automatically extend to every runtime
copy. Service units, application configuration, GitLab variables, and Kubernetes
Secrets rely on the access controls of their destination platform. Restrict
administrator access, avoid logging secrets, and rotate a credential after any
suspected disclosure.

See [Product and Subsystem Security](product_subsystem_security.md#login-security-settings)
for the credential-file inventory and [Network Security](network_security.md)
for ports and exposure guidance.

















