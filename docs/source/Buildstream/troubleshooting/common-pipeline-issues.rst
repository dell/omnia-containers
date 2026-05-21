Troubleshooting BuildStreaM Pipeline Issues
===============================================

This section provides troubleshooting guidance for common BuildStreaM pipeline issues.

Stage: Health Check
-------------------

**Issue**: Health Check stage is failing.

**Possible Cause**: This issue indicates one of the following problems:
- GitLab target IP and host IP of the BuildStream API server should be reachable from each other.
- BuildStream containers are not running properly.

**Resolution**:

1. Ensure the GitLab target IP and BuildStream API server are in the same subnet.

2. Verify that the ``omnia_build_stream`` container and the ``omnia_postgres`` and ``playbook_watcher`` services are running on the OIM node. To check the status of the containers, run the following command:
 
   .. code-block:: bash
   
      systemctl status omnia_build_stream.service
      systemctl status omnia_postgres.service
      systemctl status playbook_watcher.service

3. If there are failures in any of the containers, capture and verify the logs from journalctl using the following command:
   
   .. code-block:: bash
   
      journalctl -u omnia_build_stream --no-pager
      journalctl -u omnia_postgres --no-pager

Stage: API Registration
-----------------------

**Issue**: API-Registration stage is failing.

**Possible Cause**: This issue indicates one of the following problems:
- Maximum client limit reached for BuildStreaM API server registration.
- Other API registration errors.

.. note:: Currently, only one client can be registered with the BuildStreaM API server.

**Resolution**:

1. If you encounter the ``max_clients_limit_reached`` error, do the following:
   - Either run the pipeline from the already registered client.
   - Or perform the ``gitlab_cleanup`` and reconfigure GitLab using the playbook.

2. For other non-successful API responses, on the Omnia Infrastructure Manager (OIM), check the authentication logs at ``/<nfs-dir>/omnia/log/build_stream/auth.log`` for detailed error information.

Stage: Token Generation
-----------------------

**Issue**: Token-Generation stage is failing.

**Possible Cause**: This issue indicates one of the following problems:
- Token generation failed due to authentication issues.
- Token generation failed due to network issues.

**Resolution**:

On the OIM, check the authentication logs at ``/<nfs-dir>/omnia/log/build_stream/auth.log`` for detailed error information.

Stage: Parse Catalog
--------------------

**Issue**: Parse-Catalog stage is failing.

**Possible Cause**: This issue indicates one of the following problems:
- Invalid JSON schema format.
- The ``catalog_rhel.json`` structure does not match the expected catalog schema.

**Resolution**:

* Ensure the JSON is aligned with the schema as shown in the reference examples available at:
   - https://github.com/dell/omnia/tree/pub/build_stream/examples/catalog

* If the issue persists, on the OIM, check the job-specific logs at ``/<nfs-dir>/omnia/log/build_stream/<job-id>/<jobid>.log``


Stage: Create Local Repo
------------------------

**Issue**: Create-Local-Repo stage is failing.

**Possible Cause**: This issue indicates one of the following problems:
- Playbook execution failed.
- Configuration issues in ``local_repo_config.yml``.

**Resolution**:

1.  If there are issues with playbook execution, the log path is available from the API response. Check the logs at the path specified in the ``log_file_path`` field.
   
    **Example API response format**:

        .. code-block:: json
        
            {
                "stage_name": "create-local-repository",
                "stage_state": "FAILED",
                "started_at": "2026-03-11T10:07:58.906785+00:00Z",
                "ended_at": "2026-03-11T10:49:20.639894+00:00Z",
                "error_code": "PLAYBOOK_EXECUTION_FAILED",
                "error_summary": "Playbook exited with code 2",
                "log_file_path": "/nfs/omnia/log/build_stream/5a4f69f4-44df-42eb-b88b-1583ea2610a8/local_repo.yml_20260311_171630.log"
            }

2. Verify the configuration settings in ``local_repo_config.yml``.

3. After fixing the configuration issues, re-run the pipeline.

Stage: Build Images
-------------------

**Issue**: Build Images stage is failing.

**Possible Cause**: This issue indicates one of the following problems:
- Playbook execution failed.
- Catalog does not have predefined functional groups.

**Resolution**:

1. Ensure the catalog has the predefined functional groups. For the supported functional groups, see :ref:`functional-groups-section`.

2. If changes are required in the catalog, make the necessary modifications to the catalog.

3. After fixing catalog issues, re-run the pipeline.

Stage: Deploy Images
--------------------

**Issue**: Deploy Images stage is failing.

**Possible Cause**: This issue indicates one of the following problems:
- Playbook execution failed.
- The functional groups listed in the PXE mapping file do not adhere to functional groups in the ``catalog_rhel.json``.

**Resolution**:

1. Check the log path from the API response for detailed error information.

2. Ensure the functional groups listed in the PXE mapping file matches the functional groups defined in the ``catalog_rhel.json``.

3. After making necessary modifications to the PXE mapping, re-run the pipeline manually.