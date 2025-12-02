Repo Creds
---

If you are working with a private ldms repo, add git api token to build_auth/.git-credentials

Build image
---

```console
# Script:
build.bash

# List images:
podman --storage-driver vfs --root ${HOME}/.local/share/containers/vfs-storage/  images
```

Test image
---

```
podman --storage-driver vfs --root ${HOME}/.local/share/containers/vfs-storage/ run -it localhost/ubuntu-ldms:<YOUR_NUMBER_HERE> /bin/bash
```
