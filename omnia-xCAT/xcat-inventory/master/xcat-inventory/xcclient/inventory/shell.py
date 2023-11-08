#!/usr/bin/python2
###############################################################################
# IBM(c) 2007 EPL license http://www.eclipse.org/legal/epl-v10.html
###############################################################################
# -*- coding: utf-8 -*-
#

"""
Command-line interface to xCAT inventory import/export
"""

from __future__ import print_function

import re
import sys
import traceback

from xcclient import shell
from .exceptions import *
from . import backend, utils


try: 
    import xcclient.inventory.manager as mgr
except ImportError as e:
     if re.match(r'No module named pymysql',str(e),re.I):
         print(r'Error: '+str(e), file=sys.stderr)
         print(r"Please install package 'python-PyMySQL-0.7.x' or 'PyMySQL 0.7.x' on PyPI",file=sys.stderr)
         sys.exit(1)
     else:
         print(str(e), file=sys.stderr)
         sys.exit(1)

class InventoryShell(shell.ClusterShell):
    def add_subcommands(self, subparsers, revision):
        pass

    @shell.arg('-t','--type', metavar='<type>', help='comma "," delimited types of the objects to import, valid values: '+','.join(mgr.InventoryFactory.getvalidobjtypes())+'. '+'If not specified, all objects in the inventory file will be imported')
    @shell.arg('-o','--objects', dest='name',metavar='<name>', help='names of the objects to import, delimited with Comma(,). If not specified, all objects of the specified type in the inventory file will be imported')
    @shell.arg('-f','--path', metavar='<path>', help='path of the inventory file to import ')
    @shell.arg('-d','--dir', dest='directory',metavar='<directory>', help='path of the inventory directory')
    @shell.arg('-s','--schema-version',dest='version', metavar='<version>', help='schema version of the inventory file. Valid schema versions: '+','.join(mgr.InventoryFactory.getAvailableSchemaVersions())+'. '+'If not specified, the "latest" schema version will be used')
    @shell.arg('--dry', dest='dryrun', action="store_true", default=False, help='Dry run mode, nothing will be commited to xcat database')
    @shell.arg('-c','--clean', dest='update', action="store_false", default=True, help='clean mode. IF specified, all objects other than the ones to import will be removed')
    @shell.arg('-e','--env', dest='env', metavar='<env_var>', action='append', help='the values of variables in object definitions(only available for osimage object), syntax: "<variable name>=<variable value>" , this option can be used multiple times to specify multiple variables')
    @shell.arg('--env-file', dest='env_file', metavar='<env_file>', action='append', help='the variable file to set values for variables in inventory file during import. When specified multiple times, the variables in the variable file will overwrite any existing variable. When used with -e option together, the variable value specified with -e will take precedence.')
    @shell.arg('-x', '--exclude', dest='exclude', default='', help='types to be excluded when importing all, delimited with Comma(,).')
    def do_import(self, args):
        """Import inventory file to xcat database"""
        mgr.validate_args(args, 'import')
        mgr.importobj(args.path,args.directory,args.type,args.name,dryrun=args.dryrun,version=args.version,update=args.update,envs=args.env, env_files=args.env_file,exclude=args.exclude.split(','))

    @shell.arg('-t','--type', metavar='<type>', help='comma "," delimited types of objects to export, valid values: '+','.join(mgr.InventoryFactory.getvalidobjtypes())+'. '+'If not specified, all objects in xcat databse will be exported')
    @shell.arg('-x', '--exclude', dest='exclude', default='', help='types to be excluded when exporting all, delimited with Comma(,).')
    @shell.arg('-o','--objects', dest='name',metavar='<name>', help='names of the objects to export, delimited with Comma(,). If not specified, all objects of the specified type will be exported')
    @shell.arg('-f','--path', metavar='<path>', help='path of the inventory file')
    @shell.arg('-d','--dir', dest='directory',metavar='<directory>', help='path of the inventory directory')
    @shell.arg('-s','--schema-version', dest='version',metavar='<version>', help='schema version of the inventory data. Valid values: '+','.join(mgr.InventoryFactory.getAvailableSchemaVersions())+'. '+'If not specified, the "latest" schema version will be used')
    @shell.arg('--format', metavar='<format>', help='format of the inventory data, valid values: json, yaml. yaml will be used by default if not specified ')
    def do_export(self, args):
        """Export the inventory data from xcat database"""
        mgr.validate_args(args, 'export')
        mgr.export_by_type(args.type, args.name, args.path, args.directory, args.format, version=args.version, exclude=args.exclude.split(','))

    @shell.arg('--files', dest='files', metavar='FILE', nargs=2, help='compare the given 2 inventory files')
    @shell.arg('--filename', dest='filename', metavar='FILENAME', nargs=1, help='the filename want to show, be used with "--files"')
    @shell.arg('--source', dest='source', metavar='FILE', nargs=1, help='compare the given inventory file with xCAT DB')
    @shell.arg('--all', dest='all', action="store_true", default=False, help='compare the given inventory file with the whole xCAT DB, be used with "--source". If not specified, will only compare the objects in given inventory file by default.')
    def do_diff(self, args):
        """show inventory diff between files or file vs xCAT DB"""
        if not args.files and not args.source:
            mybackend=backend.Invbackend()
            mybackend.diff()
        else:
            from .inventorydiff import InventoryDiff
            InventoryDiff(args).inventory_diff()

    def do_envlist(self,args):
        """Show implicit environment variables during 'xcat-inventory import', which can be used in inventory files with format '{{<environment variable name>}}'"""
        mgr.envlist()

    def do_init(self,args):
        """Initialize the inventory backend"""
        mybackend=backend.Invbackend(skip=1)
        mybackend.init()

    def do_workspace_list(self,args):
        """list all the workspaces"""
        mybackend=backend.Invbackend()
        mybackend.workspace_list()

    @shell.arg('workspacename',metavar='workspacename',type=str,help='the workspace name to create')
    def do_workspace_new(self,args):
        """create a new workspace"""
        mybackend=backend.Invbackend()
        mybackend.workspace_new(args.workspacename)

    @shell.arg('workspacename',metavar='workspacename',type=str,help='the workspace name to delete')
    def do_workspace_delete(self,args):
        """remove a workspace"""
        mybackend=backend.Invbackend()
        mybackend.workspace_delete(args.workspacename)

    @shell.arg('workspacename',metavar='workspacename',type=str,help='the workspace name to switch to')
    def do_workspace_checkout(self,args):
        """checkout a workspace"""
        mybackend=backend.Invbackend()
        mybackend.workspace_checkout(args.workspacename)


    @shell.arg('revision',metavar='revision',type=str,nargs='?',default=None,help='the revision to show or list')
    def do_revlist(self,args):
        """list the revisions of the current workspace if no revision is specified, otherwise, show the info of the specified revision"""
        mybackend=backend.Invbackend()
        mybackend.rev_list(args.revision)

    @shell.arg('--no-import', dest='doimport', action="store_false", default=True, help='whether import inventory data into DB after checkout. If not specified, import inventory data to DB')
    @shell.arg('revision',metavar='revision',type=str,nargs='?',default=None,help='the revision to checkout')
    def do_checkout(self,args):
        """checkout to a specified revision"""
        mybackend=backend.Invbackend()
        mybackend.checkout(args.revision,args.doimport)

    def do_refresh(self,args):
        """refresh the workspace, drop all the stashed and untracked changes"""
        mybackend=backend.Invbackend()
        mybackend.refresh()

    def do_radar(self,args):
        """detect the workspace and revision in remote repo"""
        mybackend=backend.Invbackend()
        mybackend.radar()

    def do_pull(self,args):
        """sync the current workspace with remote workspace"""
        mybackend=backend.Invbackend()
        mybackend.pull()

    #@shell.arg('revision',metavar='revision',type=str,nargs='?',default=None,help='the revision to push')
    def do_push(self,args):
        """push the current workspace to remoteworkspace"""
        mybackend=backend.Invbackend()
        mybackend.push()

    #def do_drop(self,args):
    #    """drop the uncommited modification in backend"""
    #    mybackend=backend.Invbackend()
    #    mybackend.drop()

    @shell.arg('revision',metavar='revision',type=str,nargs='?',default=None,help='the revision name to create')
    @shell.arg('-m','--message', dest='message',metavar='<message>',type=str,nargs='?', help='the description of the revision to create')
    def do_commit(self,args):
        """create a revision on current workspace"""
        mybackend=backend.Invbackend()
        mybackend.commit(args.revision,args.message)

    def do_whereami(self,args):
        """tell me where i am, which branch,which revision. shortcut:\"w\""""
        mybackend=backend.Invbackend()
        mybackend.whereami()


# main entry for CLI
def main():
    utils.initglobal()
    try:
        InventoryShell('xcat-inventory','#VERSION_SUBSTITUTE#').run(sys.argv[1:], '1.0', "xCAT inventory management tool")
    except KeyboardInterrupt:
        print("... terminating xCAT inventory management tool", file=sys.stderr)
        sys.exit(2)
    except (InvalidFileException,ObjNonExistException,CommandException,InvalidValueException,BadDBHdlException,BadSchemaException,DBException,ParseException,InternalException,ObjTypeNonExistException,FileNotExistException,BackendNotInitException,ShErrorReturnException,DirNotExistException) as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    #except (ParserError), e:
    #    print("Error: invalid file!", file=sys.stderr)
    #    sys.exit(2)
    except Exception as e:
        #print(e)
        traceback.print_exc(e)
        sys.exit(1)
