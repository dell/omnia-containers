# Omnia Automation Framework

An automation framework for managing and deploying Omnia environments using Ansible and Jenkins.

## Project Overview

This project provides automated deployment and management capabilities for Omnia environments. It leverages Ansible for configuration management and Jenkins for CI/CD pipeline orchestration.

## Setup

1. Clone the repository:
```bash

cd omnia_automation/ && git clone [automation-repository-url]
```

2. Install prerequisites:
```bash
cd automation && ./prerequisites.sh
```

3. Configure environment settings:
- Edit `config.py` to set up environment-specific configurations
- Review and modify Jenkins pipeline settings in `jenkinsfile`

## Usage

### Running Automation Tests

The automation framework uses Molecule for testing Ansible roles. Test scenarios are defined in `scenario_order.txt`.

To run tests sequentially:
```bash
cd automation && ./molecule.sh all
```

To run tests scenario by scenario:

```bash
cd automation && ./molecule.sh test scenario_name 
```

ex:- 
```bash
cd automation && ./molecule.sh test prepare_oim 
```

To only verify scenario by scenario:

```bash
cd automation && ./molecule.sh verify scenario_name 
```

ex:- 
```bash
cd automation && ./molecule.sh verify prepare_oim 
```

### Jenkins Integration

The project includes a Jenkinsfile for CI/CD pipeline integration. The pipeline handles:
- Code validation
- Test execution
- Deployment orchestration

### Recovery Procedures

In case of failed deployments or container issues, the framework includes recovery procedures:
- SSH into the omnia_core container
- Execute cleanup playbook: `ansible-playbook oim_cleanup.yml`
- Follow up with container cleanup if necessary

## Support

For support, please open an issue in the repository or contact the project maintainers.
