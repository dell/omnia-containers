# Copyright 2025 Dell Inc. or its subsidiaries. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""
Setup script for the automation_library package.

This script configures the packaging and distribution of the reusable
automation library used in the Omnia project. It uses setuptools to
define metadata such as the package name, version, and description,
and automatically discovers all sub-packages.
"""

from setuptools import setup, find_packages

setup(
    name="automation_library",
    version="0.1",
    description="A reusable automation library for Omnia project",
    packages=find_packages(),
)
