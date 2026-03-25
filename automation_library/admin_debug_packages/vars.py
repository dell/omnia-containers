# Copyright 2026 Dell Inc. or its subsidiaries. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Admin Debug Packages Variables.

Contains constants and configuration for admin debug packages verification.
"""

# Container name
CONTAINER_NAME = "omnia_core"

# Path to software_config.json inside container
SOFTWARE_CONFIG_PATH = "/opt/omnia/input/project_default/software_config.json"

# Path to admin_debug_packages.json inside omnia_core container
ADMIN_DEBUG_PACKAGES_JSON = (
    "/opt/omnia/input/project_default/config"
    "/x86_64/rhel/10.0/admin_debug_packages.json"
)

# SSH timeout for remote commands
SSH_TIMEOUT = 10

# Default list of debug packages from admin_debug_packages.json
# This is the complete list of packages that should be installed on cluster nodes
DEBUG_PACKAGES_LIST = [
    "which",
    "tcpdump",
    "traceroute",
    "iperf3",
    "fping",
    "dmidecode",
    "hwloc",
    "hwloc-libs",
    "pciutils",
    "vim-enhanced",
    "emacs",
    "zsh",
    "openssh",
    "openssh-server",
    "openssh-clients",
    "rsync",
    "file",
    "libcurl",
    "tar",
    "bzip2",
    "man-db",
    "man-pages",
    "strace",
    "kexec-tools",
    "openssl-devel",
    "ipmitool",
    "gdb",
    "gdb-gdbserver",
    "lldb",
    "lldb-devel",
    "valgrind",
    "valgrind-devel",
    "ltrace",
    "kernel-tools",
    "perf",
    "papi",
    "papi-devel",
    "papi-libs",
    "cmake",
    "make",
    "autoconf",
    "automake",
    "libtool",
    "gcc",
    "gcc-c++",
    "gcc-gfortran",
    "binutils",
    "binutils-devel",
    "clustershell",
    "bash-completion",
]

__all__ = [
    "CONTAINER_NAME",
    "SOFTWARE_CONFIG_PATH",
    "ADMIN_DEBUG_PACKAGES_JSON",
    "SSH_TIMEOUT",
    "DEBUG_PACKAGES_LIST",
]
