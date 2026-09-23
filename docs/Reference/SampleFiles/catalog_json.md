# Catalog JSON reference

The catalog JSON defines the functional layers, software packages, and
artifact sources used across the Omnia deployment workflow. Repository Manager uses
the catalog to prepare software repositories, while Image Build Manager and
Orchestrator use it to build images and provision the cluster.

By default, Omnia uses the following catalog:

```text
${OMNIA_DATA_PATH}/catalog/catalog_rhel.json
```

When `OMNIA_DATA_PATH` is not customized, the catalog is available at
`/opt/omnia/catalog/catalog_rhel.json`.

The source copy of the default catalog is available at:

```text
src/main/samples/catalog_rhel.json
```

Additional catalog samples are available under `src/main/samples`.
