
# user_registry_credential.yml Reference

File path: `/opt/omnia/input/user_registry_credential.yml`

This file provides authentication credentials for user-defined container or
package registries referenced in `local_repo_config.yml`.

## Parameters

--8<-- "html/user_registry_credential.html"

## Usage example
```yaml title="File: /opt/omnia/input/user_registry_credential.yml"
---
user_registry_credential:
  - {name: "my_private_registry", username: "admin", password: "secret123"}
  - {name: "docker_hub", username: "user", password: "token"}
```

!!! note

    - The `name` field must match the exact registry name provided in `local_repo_config.yml`.
    - Leave `username` and `password` empty if the registry does not require authentication.
