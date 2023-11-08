#!/usr/bin/python2
###############################################################################
# IBM(c) 2007 EPL license http://www.eclipse.org/legal/epl-v10.html
###############################################################################
# -*- coding: utf-8 -*-
#

import sys
from xcclient import shell

class ExampleCLIShell(shell.ClusterShell):
    def add_subcommands(self, subparsers, revision):
        pass

    @shell.arg('command', metavar='<subcommand>', nargs='?',
               help='Display help for <subcommand>.')
    def do_info(self, args):
        """Display welcome messages."""
        print("welcome to use the CLI framework")

    @shell.arg('--adapter', metavar='<adapter>', help='Name or ID of adapter to display.')
    def do_list(self, args):
        """Display role details."""
        print(args)

def main():
    try:
        ExampleCLIShell('xcat-example').run(sys.argv[1:], '1.0', "This is for a CLI example testing")
    except KeyboardInterrupt:
        print("... terminating xcat-example command") #, file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(e)
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
