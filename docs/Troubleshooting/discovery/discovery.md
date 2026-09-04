# Discovery Issues

Issues related to node discovery, OME integration, and PXE mapping file generation.

## PXE Mapping File Generation Fails

???+ note "Symptom"

    PXE mapping file generation fails or contains incorrect information.

??? note "Cause"

    - OME connection issues
    - Incorrect OME credentials
    - Missing or incorrect node information in OME inventory
    - PXE mapping file format errors

??? note "Resolution"

    1. Verify OME connectivity and credentials
    2. Check OME inventory contains required node information
    3. Validate PXE mapping file format
    4. Re-run discovery playbook

!!! info
    - [Discover Nodes Using OME](../../HowTo/discovery/discover_nodes.md) -- Discovery guide
    - [PXE Mapping File](../../Reference/SampleFiles/pxe_mapping_file.md) -- PXE mapping file format reference
