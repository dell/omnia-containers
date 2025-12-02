#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create host map for ldms config file generation 
"""

import os
import json
import yaml
import time
import shutil
import logging
import argparse
import requests
import urllib3
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def setup_logging(verbose=False):
    """Configure logging facility."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s %(levelname)s: %(message)s')

def load_config(config_path):
    """Load the json config file given a file path."""
    if not os.path.exists(config_path):
        return {}
    with open(config_path, 'r') as f:
        return json.load(f)


class LdmsdManager:
    """Generate ldmsd config and params."""

    def __init__(self, config=None):
        self.config = config
        self.base_dir = os.path.dirname(os.path.realpath(__file__))
        self.out_dir = os.path.join(self.base_dir, "out_dir")

    def main(self):
        """Make host lists for each node type."""
        now = time.strftime("%Y%m%d-%H%M%S", time.localtime())
        logging.info(f"BEGIN LDMS INIT: {now}")

        # Clean out previous
        if os.path.isdir(self.out_dir):
            logging.info(f"Clean out_dir: {self.out_dir}")
            shutil.rmtree(self.out_dir)
        os.makedirs(self.out_dir, exist_ok=True)
   
        # PLACE HOLDER: just copy the example file for now
        shutil.copy("host_map.r7525.json", self.out_dir)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Turn on verbose output"
    )
    parser.add_argument(
        "--config", '-c',
        default='ldms_machine_config.json',
        help="Path to JSON config file"
    )
    args = parser.parse_args()

    config = load_config(args.config)
    verbose = args.verbose if args.verbose is not None else config.get("verbose", False)
    setup_logging(verbose)

    agg = LdmsdManager(config)
    agg.main()

if __name__ == '__main__':
    main()

