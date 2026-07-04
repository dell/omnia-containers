# Contributing to Omnia

We encourage everyone to help us improve Omnia by contributing to the project. Contributions can be as small as documentation updates or adding example use cases, to adding commenting and properly styling code segments, all the way up to full feature contributions. We ask that contributors follow our established guidelines for contributing to the project.

This document will evolve as the project matures. Refer back regularly to stay in line with the latest contribution guidelines.

## Become a contributor

You can contribute to Omnia in several ways:

- **Code contributions** -- Fix bugs or implement features. See [Pull Request Guidelines](pull_requests.md) for the submission process.
- **Documentation** -- Improve existing documentation or add examples.
- **Bug reports** -- Report issues you encounter. See [Submitting issues](#submitting-issues) below.
- **Feature requests** -- Propose new features or enhancements.
- **Testing** -- Test Omnia on different hardware configurations, OS versions, or network topologies and report your findings.

## Submitting issues

All issues should be submitted on the [Omnia GitHub Issues](https://github.com/dell/omnia/issues) page. Before submitting a new issue, search the existing issues to ensure the problem has not already been reported.

### Report bugs

Report a bug by submitting a bug report with the following information:

1. Version of relevant software: Omnia version and Python version
2. Details of the issue explaining the problem.
3. Steps to reproduce the issue.
4. The expected outcome that was not met.
5. Supporting troubleshooting information such as log output and error messages.

### Feature requests

If you have an idea for how to improve Omnia, submit a feature request issue with:

- A description of the proposed functionality.
- The use case and expected behavior.
- Any design considerations or implementation suggestions.

## Getting started

1. **Fork the repository** on GitHub:

    [https://github.com/dell/omnia](https://github.com/dell/omnia)

2. **Clone your fork** locally:

    ```bash
    git clone https://github.com/<your_username>/omnia.git
    cd omnia
    ```

3. **Add the upstream remote:**

    ```bash
    git remote add upstream https://github.com/dell/omnia.git
    ```

4. **Create a branch** from `devel`. All contributions should be branched from `devel`. Use the naming pattern `issue-xxxx` based on the issue you are addressing (e.g., `issue-1023`):

    ```bash
    git checkout devel
    git checkout -b issue-<issue_number>
    ```

5. **Make your changes**, commit with sign-off, and push:

    ```bash
    git add .
    git commit -s -m "Brief description of the change"
    git push origin issue-<issue_number>
    ```

6. **Open a pull request** on GitHub from your branch to the `devel` branch of the upstream repository. See [Pull Request Guidelines](pull_requests.md) for detailed requirements.


## Signing your commits

All contributors must sign off on their commits to certify that they have permission to contribute the code. This is commonly known as the [Developer Certificate of Origin (DCO)](https://developercertificate.org/), which is reproduced below.

Use the `--signoff` or `-s` option when committing:

### Developer's Certificate of Origin 1.1
```bash
Developer Certificate of Origin
Version 1.1

Copyright (C) 2004, 2006 The Linux Foundation and its contributors.

Everyone is permitted to copy and distribute verbatim copies of this
license document, but changing it is not allowed.

Developer's Certificate of Origin 1.1

By making a contribution to this project, I certify that:

(a) The contribution was created in whole or in part by me and I
    have the right to submit it under the open source license
    indicated in the file; or

(b) The contribution is based upon previous work that, to the best
    of my knowledge, is covered under an appropriate open source
    license and I have the right under that license to submit that
    work with modifications, whether created in whole or in part
    by me, under the same open source license (unless I am
    permitted to submit under a different license), as indicated
    in the file; or

(c) The contribution was provided directly to me by some other
    person who certified (a), (b) or (c) and I have not modified
    it.

(d) I understand and agree that this project and the contribution
    are public and that a record of the contribution (including all
    personal information I submit with it, including my sign-off) is
    maintained indefinitely and may be redistributed consistent with
    this project or the open source license(s) involved.
```
## Code style

- **Ansible playbooks and roles** -- Follow [Ansible best practices](https://docs.ansible.com/ansible/latest/tips_tricks/ansible_tips_tricks.html). Use YAML syntax (not inline JSON), descriptive task names, and meaningful variable names.
- **Python scripts** -- Follow [PEP 8](https://peps.python.org/pep-0008/). Use `black` for formatting and `flake8` for linting.
- **Shell scripts** -- Use `shellcheck` to validate shell scripts.
- **Tests** -- Include test scripts for your changes. Add or update Molecule tests for any new or modified Ansible roles.

## Code of conduct

All contributors are expected to adhere to the project's Code of Conduct. We strive to build a welcoming and open community for anyone who wants to use the project or contribute to it. Be respectful, constructive, and collaborative in all interactions.

!!! info

    - [Pull Request Guidelines](pull_requests.md) -- Detailed PR submission and review process.
    - [GitHub Issues](https://github.com/dell/omnia/issues) -- Report bugs and request features.
