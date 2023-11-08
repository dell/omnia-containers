#!/usr/bin/python2
###############################################################################
# IBM(c) 2018 EPL license http://www.eclipse.org/legal/epl-v10.html
###############################################################################
# -*- coding: utf-8 -*-
#


"""
Command-line interface skeleton to xCAT
"""

from __future__ import print_function
import argparse
import logging

import re
from .inventory import exceptions as exp
from .inventory import globalvars

# Decorator to define CLI args
def arg(*args, **kwargs):
    def _decorator(func):
        func.__dict__.setdefault('arguments', []).insert(0, (args, kwargs))
        return func
    return _decorator

class ClusterShell(object):

    def __init__(self, prog, version='1.0'):
        self.prog = prog
        self.version = version
        self.logger = logging.getLogger('xcclient')

    def get_common_parser(self, desc=None ):
        parser = argparse.ArgumentParser(
            prog=self.prog,
            description=desc or "",
            epilog='See "%s help COMMAND" '
                   'for help on a specific command.' % self.prog,
            add_help=False,
            formatter_class=XCHelpFormatter,
        )

        # Global arguments
        parser.add_argument('-h',
                            '--help',
                            action='store_true',
                            help="Prints help message")

        parser.add_argument('--debug',
                            default=False,
                            action='store_true',
                            help="Prints debugging output into the log file (not implemented yet).")

        parser.add_argument('-v', '--verbose',
                            default=False,
                            action='store_true',
                            help="Prints verbose output.")

        parser.add_argument('-V', '--version',
                            action='version',
                            version=self.version,
                            help="Shows the program version and exits.")
        return parser

    def get_subcommand_parser(self, parser=None, revision='1.0'):
        parser = parser or self.get_common_parser()

        self.subcommands = {}
        subparsers = parser.add_subparsers(metavar='<subcommand>')

        # Add the parser for subcommand in order
        self.add_subcommands(subparsers, revision)
        self._find_actions(subparsers, self)
        #self._add_bash_completion_subparser(subparsers)

        return parser

    def add_subcommands(self, parser):
        # Add the subparsers for each CLI
        

        #self._find_actions(subparsers, actions_module)
        raise NotImplementedError()

    def __subcmdshortcut(self,string):
        sc=None
        matched=re.findall(r'shortcut:(\S+)\s*$',string) 
        if matched:
            sc=matched[0].strip('"').strip("'")
            return sc.split(',')
        return None

    def _find_actions(self, subparsers, actions_module):
        for attr in (a for a in dir(actions_module) if a.startswith('do_')):
            command = attr[3:].replace('_', '-')
            callback = getattr(actions_module, attr)
            desc = callback.__doc__ or ''
            help = desc.strip().split('\n')[0]
            sc=self.__subcmdshortcut(help)
            arguments = getattr(callback, 'arguments', [])

            subparser = subparsers.add_parser(
                command,
                #aliases=sc,
                help=help,
                description=desc,
                add_help=False,
                formatter_class=XCHelpFormatter)
            subparser.add_argument('-h', '--help', action='help',
                                   help=argparse.SUPPRESS)
            self.subcommands[command] = subparser
            group = subparser.add_argument_group(title='Arguments')
            for (args, kwargs) in arguments:
                group.add_argument(*args, **kwargs)
            subparser.set_defaults(func=callback)

    def _add_bash_completion_subparser(self, subparsers):
        subparser = subparsers.add_parser(
            'bash_completion',
            add_help=False,
            formatter_class=XCHelpFormatter
        )
        self.subcommands['bash_completion'] = subparser
        subparser.set_defaults(func=self.do_bash_completion)

    def setup_debugging(self, debug):
        if not debug:
            return

        streamformat = "%(levelname)s (%(module)s:%(lineno)d) %(message)s"
        # Set up the root logger to debug so that the submodules can
        # print debug messages
        logging.basicConfig(level=logging.DEBUG,
                            format=streamformat)
        #logging.getLogger('iso8601').setLevel(logging.WARNING)
        self.logger.setLevel(logging.WARNING)
        
    def _do_bash_completion(self, args):
        """Prints all of the commands and options to stdout.
        """
        commands = set()
        options = set()
        for sc_str, sc in self.subcommands.items():
            commands.add(sc_str)
            for option in list(sc._optionals._option_string_actions):
                options.add(option)

        commands.remove('bash-completion')
        commands.remove('bash_completion')
        print(' '.join(commands | options))

    @arg('command', metavar='<subcommand>', nargs='?',
               help='Display help for <subcommand>.')
    def do_help(self, args):
        """Display help about this program or one of its subcommands."""
        if getattr(args, 'command', None):
            if args.command in self.subcommands:
                self.subcommands[args.command].print_help()
            else:
                raise exp.CommandException("Error: '%s' is not a valid subcommand" %
                                       args.command)
        else:
            self.parser.print_help()

    def run(self, argv, api=None, description=None):
        # Parse args once to find version
        parser = self.get_common_parser(description)
        (options, args) = parser.parse_known_args(argv)
        globalvars.verbose=options.verbose
        self.setup_debugging(options.debug)

        # build available subcommands based on version
        subcommand_parser = self.get_subcommand_parser(parser, api)
        self.parser = subcommand_parser

        # Handle top-level --help/-h before attempting to parse
        # a command off the command line
        if not argv:
            self.do_help(options)
            return 0

        if not args:
            self.do_help(options)
            return 0

        if args[0] not in self.subcommands.keys():
            self.do_help(options)
            raise exp.CommandException("Error: not a valid subcommand to run")

        if '-h' in argv or '--help' in argv:
            args.append('-h')

        # Parse args again and call whatever callback was selected
        args = subcommand_parser.parse_args(args)

        # Short-circuit and deal with help command right away.
        if args.func == self.do_help:
            self.do_help(args)
            return 0
        #elif args.func == self.do_bash_completion:
        #    self.do_bash_completion(args)
        #    return 0

        #try:
        return args.func(args)
        #except Exception, e:
        #    raise e

class XCHelpFormatter(argparse.HelpFormatter):
    INDENT_BEFORE_ARGUMENTS = 6
    MAX_WIDTH_ARGUMENTS = 32

    def add_arguments(self, actions):
        for action in filter(lambda x: not x.option_strings, actions):
            if not action.choices:
                continue
            for choice in action.choices:
                length = len(choice) + self.INDENT_BEFORE_ARGUMENTS
                if(length > self._max_help_position and
                   length <= self.MAX_WIDTH_ARGUMENTS):
                    self._max_help_position = length
        super(XCHelpFormatter, self).add_arguments(actions)

    def start_section(self, heading):
        # Title-case the headings
        heading = '%s%s' % (heading[0].upper(), heading[1:])
        super(XCHelpFormatter, self).start_section(heading)


    def __str__(self):
        return self._error_msg

