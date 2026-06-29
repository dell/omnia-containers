
# BuildStreaM Issues


Issues related to the BuildStreaM catalog-driven CI/CD deployment workflow,
including GitLab pipelines, container registry operations, catalog parsing, and
OAuth credentials.

## GitLab pipeline failures


???+ note "Symptom"

    A BuildStreaM pipeline in GitLab fails with a red status indicator. The
    pipeline log shows errors in one or more stages (build, deploy, test).

??? note "Cause"

    - The GitLab Runner is not registered or is offline.
    - Pipeline variables (credentials, URLs) are missing or incorrect.
    - The runner does not have network access to the OIM or cluster nodes.
    - A previous pipeline left stale state that conflicts with the current run.

??? note "Resolution"

    1. Check the pipeline log in GitLab:

       - Navigate to **CI/CD > Pipelines** in the BuildStreaM project.
       - Click the failed pipeline, then click the failed job to see its log.

    2. Verify the GitLab Runner is registered and online:

       ```bash
       gitlab-runner list
       gitlab-runner verify
       ```


    3. Check pipeline variables:

       - Navigate to **Settings > CI/CD > Variables** in the GitLab project.
       - Verify all required variables are set (OIM IP, credentials, registry
         URL).

    4. Test network connectivity from the runner to the OIM:

       ```bash
       # From the GitLab Runner host
       ping <oim_ip>
       ssh root@<oim_ip> hostname
       ```


    5. If stale state is the issue, clean up and retry:

       ```bash
       # Clear the runner's build cache
       gitlab-runner clear-cache

       # Retry the pipeline from GitLab UI
       ```


## Registry push failures


???+ note "Symptom"

    The BuildStreaM pipeline fails during the image push stage with errors such
    as:

    ```text
    Error: failed to push image: authentication required
    Error: failed to push image: denied: requested access to the resource is denied
    ```


??? note "Cause"

    - Container registry credentials are incorrect or expired.
    - The registry URL in the pipeline configuration is wrong.
    - The registry's TLS certificate is not trusted by the runner.
    - The registry storage is full.

??? note "Resolution"

    1. Verify registry credentials:

       ```bash
       podman login <registry_url>
       ```


    2. Check that the registry URL matches the pipeline configuration:

       ```bash
       grep -i registry .gitlab-ci.yml
       ```


    3. If TLS is the issue, add the registry's CA certificate:

       ```bash
       cp <registry_ca.crt> /etc/pki/ca-trust/source/anchors/
       update-ca-trust
       ```


       Or configure Podman to trust the registry:

       ```bash
       # /etc/containers/registries.conf.d/buildstream.conf
       [[registry]]
       location = "<registry_url>"
       insecure = true    # Not recommended for production
       ```


    4. Check registry storage:

       ```bash
       df -h <registry_data_dir>
       ```


## Catalog parse errors


???+ note "Symptom"

    The BuildStreaM pipeline fails during the catalog parsing stage with errors
    such as:

    ```text
    Error: Failed to parse catalog: invalid YAML syntax at line 42
    Error: Unknown component type 'slurm_cluser' in catalog entry
    ```


??? note "Cause"

    - The catalog YAML file has syntax errors (indentation, missing colons,
      invalid characters).
    - A catalog entry references a component type that does not exist (typo).
    - Required fields are missing from a catalog entry.

??? note "Resolution"

    1. Validate the catalog file syntax:

       ```bash
       python3 -c "import yaml; yaml.safe_load(open('catalog.yml'))"
       ```


    2. Use a YAML linter for more detailed error reporting:

       ```bash
       pip install yamllint
       yamllint catalog.yml
       ```


    3. Check for typos in component types. Valid types include:

       - `slurm_cluster`
       - `kubernetes_cluster`
       - `telemetry`
       - `authentication`
       - `storage`

    4. Verify all required fields are present in each catalog entry. Refer to
       the [Update Catalog Pipeline](../HowTo/BuildStreaM/update_catalog_pipeline.md) guide for the
       catalog schema.

    5. After fixing errors, commit and push to trigger a new pipeline:

       ```bash
       git add catalog.yml
       git commit -m "Fix catalog syntax errors"
       git push
       ```


## OAuth credential issues


???+ note "Symptom"

    BuildStreaM operations fail with OAuth authentication errors when
    communicating with GitLab or external services:

    ```text
    Error: OAuth token expired or revoked
    Error: 401 Unauthorized: invalid_token
    ```


??? note "Cause"

    - The OAuth token has expired.
    - The OAuth application was deleted or its secret was rotated in GitLab.
    - The token scope does not include the required permissions (`api`,
      `read_registry`, `write_registry`).

??? note "Resolution"

    1. Check the current token status:

       ```bash
       curl -H "Authorization: Bearer <token>" \
         https://<gitlab_url>/api/v4/user
       ```


       A `401` response confirms the token is invalid.

    2. Generate a new personal access token in GitLab:

       - Navigate to **User Settings > Access Tokens**.
       - Create a new token with scopes: `api`, `read_registry`,
         `write_registry`.

    3. Update the token in pipeline variables:

       - Navigate to **Settings > CI/CD > Variables**.
       - Update the `GITLAB_TOKEN` (or equivalent) variable with the new
         token.

    4. If using an OAuth application (rather than personal token):

       - Navigate to **Admin Area > Applications** (or **User Settings >
         Applications**).
       - Verify the application exists and note the Application ID and Secret.
       - Update the pipeline variables with the new credentials.

    5. Re-run the failed pipeline from the GitLab UI.

!!! info

    - [Deploy Gitlab](../HowTo/BuildStreaM/deploy_gitlab.md) -- GitLab deployment guide.
    - [Update Catalog Pipeline](../HowTo/BuildStreaM/update_catalog_pipeline.md) -- Catalog and pipeline
      configuration.
    - [Buildstream Deployment](../GetStarted/buildstream_deployment.md) -- BuildStreaM deployment
      tutorial.
