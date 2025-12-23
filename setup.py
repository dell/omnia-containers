"""Setup script for omnia_automation package."""

from setuptools import setup, find_packages
import os

# Read requirements
def read_requirements():
    req_file = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if os.path.exists(req_file):
        with open(req_file, "r", encoding="utf-8") as fh:
            # Skip comments, empty lines, and -e . (editable install of self)
            return [line.strip() for line in fh 
                    if line.strip() and not line.startswith("#") and not line.startswith("-e")]
    return []

# Read README
def read_readme():
    readme_file = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_file):
        with open(readme_file, "r", encoding="utf-8") as fh:
            return fh.read()
    return ""

setup(
    name="omnia-automation",
    version="0.1.0",
    author="Omnia Automation Team",
    author_email="",
    description="Automation library for Omnia Infrastructure Manager (OIM) - deployment, configuration, and management",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/dell/omnia",
    packages=find_packages(),
    py_modules=["run_prereq_check"],
    include_package_data=True,
    package_data={
        "automation_library": ["*.yml", "*.yaml"],
        "automation_library.vars": ["*.yml", "*.yaml"],
    },
    python_requires=">=3.12",
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            # Prerequisite check tool
            "oim-prereq-check=run_prereq_check:main",
            "oim-discovery-validate=run_discovery_validation:main",
            # Future tools will be added here:
            # "oim-deploy=automation_library.oim_deploy:main",
            # "oim-configure=automation_library.oim_configure:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
    ],
)
