.. _buildstream-index:

BuildStreaM Documentation
==========================

.. note::
   This topic is pending SME validation. Content may change before publication.

BuildStreaM is a build and validation automation solution that provides catalog-driven, policy-enforced lifecycle to build and validate Omnia-compatible images. This documentation covers BuildStreaM setup, configuration, GitLab integration, and operational procedures.

.. contents:: On This Page
   :local:
   :depth: 2

Overview
--------

BuildStreaM automates the build and validation process for HPC cluster images using a catalog-driven approach. You define your build requirements in structured catalog files, and BuildStreaM executes automated pipelines through GitLab to create and validate images according to your specifications.

Key Features
------------

**Automation**
- Catalog-driven build definitions
- Automatic pipeline triggering from catalog changes
- GitLab-based workflow orchestration

**Integration**
- Seamless integration with existing Omnia deployments
- GitLab repository management and version control
- REST API for build management

**Validation**
- Automated testing and validation procedures
- Comprehensive build artifact tracking
- Pipeline monitoring and status reporting

**Scalability**
- Support for multiple build environments
- Automated artifact repository management
- Consistent build procedures across deployments

Getting Started
---------------

To start using BuildStreaM:

1. **Review the BuildStreaM Overview** to understand capabilities and limitations
2. **Prepare BuildStreaM Configuration** to set up services and credentials
3. **Deploy GitLab** for pipeline execution and repository management
4. **Update Catalogs** to define your build requirements
5. **Monitor Pipelines** to track build progress and results

BuildStreaM represents a separate workflow from traditional Omnia deployment, focusing on automated image build and validation rather than manual cluster provisioning.

Documentation Structure
-----------------------

The BuildStreaM documentation is organized into the following topics:

**Concept Topics**
- BuildStreaM Overview - High-level introduction to BuildStreaM functionality

**Procedural Topics**
- Prepare BuildStreaM Configuration and Pipeline - Setup and configuration procedures
- GitLab Deployment - GitLab installation and integration
- Update Catalog and Check Pipeline - Catalog management and pipeline monitoring

Current Limitations
-------------------

BuildStreaM 1.0 has the following limitations:

- **Promote and validate images** are not yet implemented
- **Single-user support** - only one client/user at a time
- **No existing GitLab support** - Omnia does not support existing customer GitLab instances
- **No high availability** - no disaster recovery guarantees

.. important::
   Future releases will address these limitations and add additional features.

BuildStreaM Topics
------------------

.. toctree::
   :maxdepth: 2
   
   concept-overview
   how-to-prepare-buildstream
   how-to-gitlab-deployment
   how-to-update-catalog-pipeline

Support and Troubleshooting
--------------------------

For help with BuildStreaM:

**Documentation**
- Review the procedural guides for step-by-step instructions
- Check the BuildStreaM Overview for conceptual understanding

**Pipeline Issues**
- Monitor GitLab pipeline status through Build > Pipeline interface
- Review job logs through Build > Jobs interface
- Check GitLab runner status in Settings > CI/CD > Runners

**Configuration Problems**
- Verify BuildStreaM service status
- Check database connectivity
- Validate configuration file syntax

**Common Solutions**
- Restart GitLab runner if it shows offline status
- Verify network connectivity between services
- Check catalog file syntax for JSON errors

For additional assistance, consult the Omnia documentation and support channels.

Related Topics
--------------

* :doc:`../upgrade/index`
* :doc:`../OmniaInstallGuide/index`
