# Build Telemetry Container Images

## Overview

Omnia provides `src/telemetry/containers/build_images.sh` as the entry point for
building the telemetry container images maintained in the Telemetry source
tree. The script can build all four images or a selected comma-separated set:

This image-build utility is independent of Telemetry domain initialization.
It does not create project inputs, run `omnia.sh --setup-venv`, or deploy the
Telemetry stack.

| Build selector | Image produced | Default tag | Build source |
|----------------|----------------|-------------|--------------|
| `kafkapump` | `kafkapump` | `1.4` | Dell iDRAC Telemetry Reference Tools |
| `victoriapump` | `victoriapump` | `1.4` | Dell iDRAC Telemetry Reference Tools |
| `telemetry-receiver` | `idrac_telemetry_receiver` | `1.4` | Dell iDRAC Telemetry Reference Tools |
| `ldms` | `ldms` | `1.2` | The LDMS Containerfile in the Telemetry source tree |

The three iDRAC images use a shared checkout of
`https://github.com/dell/iDRAC-Telemetry-Reference-Tools.git` at commit
`d9890c54a333cdb5dae05ed45a7f1a0f2bac781f`. The script creates this checkout
as `src/telemetry/containers/.idrac-telemetry-tools` when it is not already
present.

The LDMS image uses a multi-stage build based on Ubuntu 26.04. It builds
`libserdes` and OVIS LDMS `v4.5.2`, installs LDMS under `/opt/ovis-ldms`, and
copies the prepared runner filesystem into the final image.

The builder loads images into the local Podman image store by default. It can
instead use Docker Buildx to load images locally or push them to a registry.

## Prerequisites

- Run the procedure from an Omnia source checkout that contains
  `src/telemetry/containers/build_images.sh` and the
  `src/telemetry/containers/ldms` build context.
- Install one of the build tools accepted by the script:

    - Podman for the default local build.
    - Docker with Buildx for a Docker local build or registry push.

- Make `git` available when building any iDRAC image. The script uses it to
  clone and check out the pinned iDRAC Telemetry Reference Tools revision.
- Provide access to the sources used by the selected build. The iDRAC builds
  clone from GitHub. The LDMS Containerfile pulls `ubuntu:26.04`, installs
  Ubuntu and Python packages, and clones the `libserdes` and OVIS repositories
  from GitHub.
- For a registry build, use Docker and select a registry location to which the
  Docker build can push. The script rejects `build_action=push` with Podman.

### Input contract

The command syntax is:

```text
./build_images.sh [container] [parameters]
```

The first argument is the container selector. If it is omitted, the script
uses `all`.

| Selector | Result |
|----------|--------|
| `all` | Build `kafkapump`, `victoriapump`, `telemetry-receiver`, and `ldms`, in that order. |
| `kafkapump` | Build only the Kafka pump image. |
| `victoriapump` | Build only the VictoriaMetrics pump image. |
| `telemetry-receiver` | Build only the iDRAC telemetry receiver image. |
| `ldms` | Build only the LDMS image. |
| Comma-separated selectors | Build each selected image; for example, `kafkapump,ldms`. |

Parameters follow the selector and use `key=value` syntax:

| Parameter | Accepted value | Default | Effect |
|-----------|----------------|---------|--------|
| `build_tool` | `podman` or `docker` | `podman` | Selects the container build tool. |
| `build_action` | `load` or `push` | `load` | Loads the image into the local image store or pushes it. `push` requires Docker. |
| `registry` | Registry and optional namespace | `docker.io/dellhpcomniaaisolution` | Prefix used for images pushed with Docker. |
| `kafkapump_tag` | Image tag | `1.4` | Sets the Kafka pump tag. |
| `victoriapump_tag` | Image tag | `1.4` | Sets the VictoriaMetrics pump tag. |
| `telemetry_receiver_tag` | Image tag | `1.4` | Sets the iDRAC telemetry receiver tag. |
| `ldms_tag` | Image tag | `1.2` | Sets the LDMS tag. |

Docker builds target `linux/amd64`. With `build_action=load`, Docker uses
`docker buildx build --no-cache --load`. With `build_action=push`, it uses
`docker buildx build --no-cache --provenance=true --sbom=true --push`.

## Procedure

1. Change to the telemetry container directory:

    ```bash title="Run on: image build host"
    cd src/telemetry/containers
    ```

2. Choose one of the following build commands.

    To build all four images with Podman and load them locally, run:

    ```bash title="Run on: image build host"
    ./build_images.sh
    ```

    To build one image or a comma-separated set, provide the selector first:

    ```bash title="Run on: image build host"
    ./build_images.sh ldms
    ./build_images.sh kafkapump,ldms
    ```

    To build all four images with Docker and load them locally, run:

    ```bash title="Run on: image build host"
    ./build_images.sh all build_tool=docker
    ```

    To build all four images and push them to the default registry, run:

    ```bash title="Run on: image build host"
    ./build_images.sh all build_tool=docker build_action=push
    ```

    To push to another registry location, set `registry`:

    ```bash title="Run on: image build host"
    ./build_images.sh all build_tool=docker build_action=push \
      registry=registry.example.com/omnia
    ```

3. When required, override the tag for each selected image. For example:

    ```bash title="Run on: image build host"
    ./build_images.sh kafkapump kafkapump_tag=1.5
    ./build_images.sh ldms ldms_tag=1.3
    ```

## Verification

1. **Output contract:** Verify the build result and image destination.

    A successful default `all` build exits successfully and ends with a build
    summary containing these image names:

    ```text
    Successfully built: kafkapump victoriapump idrac_telemetry_receiver ldms
    All telemetry containers built successfully.
    ```

    The image destination depends on the selected build mode:

    | Build mode | Expected images with default values |
    |------------|-------------------------------------|
    | Podman or Docker with `build_action=load` | `kafkapump:1.4`, `victoriapump:1.4`, `idrac_telemetry_receiver:1.4`, and `ldms:1.2` in the selected local image store |
    | Docker with `build_action=push` | `docker.io/dellhpcomniaaisolution/kafkapump:1.4`, `docker.io/dellhpcomniaaisolution/victoriapump:1.4`, `docker.io/dellhpcomniaaisolution/idrac_telemetry_receiver:1.4`, and `docker.io/dellhpcomniaaisolution/ldms:1.2` in the registry |

    A custom `registry` replaces the default registry prefix, and a custom tag
    replaces the corresponding default tag. The push flow also publishes
    provenance and an SBOM through Docker Buildx.

    The image builder does not write a YAML status file. The Telemetry module's
    `telemetry_status.yml` output is written by the deployment workflow, not by
    `build_images.sh`.

2. For a local Podman build, inspect the images that were selected:

    ```bash title="Run on: image build host"
    podman image inspect \
      kafkapump:1.4 \
      victoriapump:1.4 \
      idrac_telemetry_receiver:1.4 \
      ldms:1.2
    ```

    For a local Docker build, use the same image names with Docker:

    ```bash title="Run on: image build host"
    docker image inspect \
      kafkapump:1.4 \
      victoriapump:1.4 \
      idrac_telemetry_receiver:1.4 \
      ldms:1.2
    ```

    When only a subset was built or tags were overridden, inspect only those
    images and use their configured tags.

3. When an iDRAC image was built, verify the revision in the shared source
   checkout:

    ```bash title="Run on: image build host"
    git -C .idrac-telemetry-tools rev-parse HEAD
    ```

    The expected revision is:

    ```text
    d9890c54a333cdb5dae05ed45a7f1a0f2bac781f
    ```

## Next steps

- Record the registry and tags used for the build. The Telemetry input manifest
  represents the three iDRAC images with
  `images.idrac.telemetry_receiver`, `images.idrac.kafka_pump`, and
  `images.idrac.victoria_pump` in `telemetry_packages.yml`.
- Be aware of the current LDMS naming difference in the source. The builder
  produces `ldms:<tag>`, while `telemetry_packages.yml` identifies the LDMS
  sampler as `ubuntu-ldms:1.2` and the LDMS chart values request
  `docker.io/dellhpcomniaaisolution/ubuntu-ldms:1.2`. The source does not
  automatically retag or substitute the newly built `ldms` image. Ensure that
  the published image name and the LDMS deployment reference are aligned before
  deploying LDMS.
- Configure the required Telemetry inputs, then run the validation and
  deployment workflow described in [Deploy the Telemetry Stack](deploy_telemetry.md).

## Troubleshooting

- **`build_action=push requires build_tool=docker`**: Rerun the build with
  `build_tool=docker`, or use the default `build_action=load` with Podman.
- **`Invalid build_tool` or `Invalid build_action`**: Use `podman` or `docker`
  for `build_tool`, and `load` or `push` for `build_action`.
- **`Unknown container`**: Use `all`, `kafkapump`, `victoriapump`,
  `telemetry-receiver`, or `ldms`. Separate multiple selectors with commas and
  do not include spaces.
- **`Unknown parameter`**: Use only `build_tool`, `build_action`, `registry`,
  `kafkapump_tag`, `victoriapump_tag`, `telemetry_receiver_tag`, or `ldms_tag`
  in `key=value` form after the selector.
- **Help is treated as a container name**: `--help` is parsed as a parameter,
  not as the first positional selector. Run `./build_images.sh all --help` to
  display the script's help.
- **The iDRAC checkout is not refreshed**: If
  `.idrac-telemetry-tools` already exists, the script reports that it is already
  cloned and reuses it without fetching or checking out the pinned revision.
  Use the revision verification command above to confirm the checkout before
  relying on a reproducible build.
- **An image build stops while downloading content**: Confirm access to the
  applicable source listed in Prerequisites. The script and LDMS Containerfile
  obtain Git repositories, base images, Ubuntu packages, and Python packages
  during the build.
