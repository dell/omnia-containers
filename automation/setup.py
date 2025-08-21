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
