#!/usr/bin/python2
###############################################################################
# IBM(c) 2007 EPL license http://www.eclipse.org/legal/epl-v10.html
###############################################################################
# -*- coding: utf-8 -*-
#

from __future__ import print_function
import os
import shutil
from jinja2 import Environment,meta,FileSystemLoader
import json
import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from .dbsession import DBsession
from .dbfactory import dbfactory
from .xcatobj import *
from .exceptions import *
from . import utils
from . import globalvars

"""
Command-line interface to xCAT inventory import/export
"""

VALID_OBJ_FORMAT = ['yaml', 'json']

class InventoryFactory(object):
    __InventoryHandlers__ = {}
    __InventoryClass__ = {'node': Node, 'network': Network, 'osimage': Osimage, 'route': Route, 'policy': Policy, 'passwd': Passwd,'site': Site,'zone':Zone,'credential':Credential,'networkconn':NetworkConn,'prodkey':ProductKey,'osdistro':Osdistro}
    __InventoryClass_WithFiles__=['osimage','credential']
    __InventoryClass_partial__=['networkconn','prodkey']
    __db__ = None
    
    def __init__(self, objtype,dbsession,schemapath,schemaversion):
        self.objtype = objtype
        self.dbsession=dbsession
        self.schemapath=schemapath
        self.schemaversion=schemaversion


    @classmethod
    def getObjTypesWithFiles(cls):
        return cls.__InventoryClass_WithFiles__

    @classmethod
    def getvalidobjtypes(cls,ignorepartial=0):
        if ignorepartial:
            return list(set(cls.__InventoryClass__.keys())-set(cls.__InventoryClass_partial__))
        return cls.__InventoryClass__.keys()

    @staticmethod
    def createHandler(objtype,dbsession,schemaversion=None):
        if objtype not in InventoryFactory.getvalidobjtypes():
            raise CommandException("Error: Invalid object type: \"%(t)s\". Valid types: \"%(ts)s\"", t=objtype,ts=','.join(InventoryFactory.getvalidobjtypes(ignorepartial=1)))
             
        if schemaversion is None:
            schemaversion=InventoryFactory.getValidSchemaVersion(objtype)
        if schemaversion is None:
            raise BadSchemaException("Error: no available schema of %s found!"%(objtype)) 
            
        validversions=InventoryFactory.getAvailableSchemaVersions()
        if schemaversion not in validversions:
            raise BadSchemaException("Error: invalid schema version \""+schemaversion+"\", the valid schema versions: "+','.join(validversions)) 
        schemapath=os.path.join(os.path.dirname(__file__), 'schema/'+schemaversion+'/'+objtype+'.yaml')
        if not os.path.exists(schemapath):
            raise BadSchemaException("Error: schema file \""+schemapath+"\" does not exist, please confirm the schema version!")
        # non-thread-safe now
        if objtype not in InventoryFactory.__InventoryHandlers__:
            InventoryFactory.__InventoryHandlers__[objtype] = InventoryFactory(objtype,dbsession,schemapath,schemaversion)

        return InventoryFactory.__InventoryHandlers__[objtype]

    @staticmethod
    def getAvailableSchemaVersions():
        schemaversions=[]
        schemapath=os.path.join(os.path.dirname(__file__), 'schema')
        for item in os.listdir(schemapath):  
            filepath = os.path.join(schemapath, item)  
            if os.path.isdir(filepath):  
                schemaversions.append(item)
        schemaversions.sort(reverse = True)
        return schemaversions

    @staticmethod
    def getValidSchemaVersion(objtype='node'):
        schemavers=InventoryFactory.getAvailableSchemaVersions()
        for ver in schemavers:
            schemapath=os.path.join(os.path.dirname(__file__), 'schema/'+str(ver)+'/'+objtype+'.yaml')
            try:
                myclass = InventoryFactory.__InventoryClass__[objtype]
                myclass.validate_schema_version(schemapath)
            except Exception:
                continue
            return ver   
        return None
 
    @staticmethod
    def getLatestSchemaVersion():
        latestver=InventoryFactory.getAvailableSchemaVersions()[0]
        schemapath=os.path.join(os.path.dirname(__file__), 'schema/'+latestver)
        realpath=os.path.realpath(schemapath)
        return os.path.basename(realpath)
   
    def getDBInst(self):
        if InventoryFactory.__db__ is None:
            InventoryFactory.__db__=dbfactory(self.dbsession)
        return InventoryFactory.__db__

    def exportObjs(self, objlist, location=None,fmt='yaml',comment=None):
        myclass = InventoryFactory.__InventoryClass__[self.objtype]
        myclass.loadschema(self.schemapath)
        myclass.validate_schema_version(None,'export')
               
        obj_attr_dict={}
        tabs=myclass.gettablist()
        if not tabs:
            if not objlist and self.objtype in ('credential'):
                objlist=['credential']
            for obj in objlist:
                obj_attr_dict[obj]={}
        else:
            obj_attr_dict = self.getDBInst().gettab(tabs, objlist)
        objdict={}
        myobjdict2dump={}
        objdict[self.objtype]={}
        for key, attrs in obj_attr_dict.items():
            if not key:
               continue
            filestobak=[]
            if type(attrs)==list:
                myobjdict={}
                for attr in attrs:
                    newsubobj=myclass.createfromdb(key, attr)
                    subobjdict=newsubobj.getobjdict()
                    objdictkey=list(subobjdict.keys())[0]
                    if objdictkey not in myobjdict.keys():
                        myobjdict[objdictkey]=[]
                    myobjdict[objdictkey].append(subobjdict[objdictkey])
                    filestobak.append(newsubobj.getfilestosave())
            else:
                newobj = myclass.createfromdb(key, attrs)
                myobjdict=newobj.getobjdict()
                filestobak=newobj.getfilestosave()
            myobjdict2dump[self.objtype]=myobjdict
            myobjdict2dump['schema_version']=self.getcurschemaversion()
            objdict[self.objtype].update(myobjdict)

            if location: 
                mydir=os.path.join(location,key)
                if os.path.exists(mydir):
                    shutil.rmtree(mydir)
                os.mkdir(mydir) 
                if fmt=='yaml':
                    myfile=os.path.join(mydir,'definition.yaml')
                elif fmt=='json':
                    myfile=os.path.join(mydir,'definition.json')
                dumpobj(myobjdict2dump,fmt,myfile) 
                with open(myfile, "a") as f:
                    f.write(comment)
                for filetobak in filestobak:
                    if os.path.exists(filetobak):
                        dstfile=mydir+filetobak
                        try:
                            os.makedirs(os.path.dirname(dstfile))
                        except OSError as e:
                            if e.errno != os.errno.EEXIST:
                                raise
                            pass
                        shutil.copyfile(filetobak,dstfile)
                    else:
                        print("Warning: The file \"%s\" of \"%s\" object \"%s\" does not exist"%(filetobak,self.objtype,key),file=sys.stderr) 

        refobjdict=myclass.getoutref()
        if refobjdict:
           for key in refobjdict.keys():
               for subtype in refobjdict[key]:
                    subhdl = InventoryFactory.createHandler(subtype,self.dbsession,self.schemaversion)
                    subdict=subhdl.exportObjs(objlist,None,fmt)
                    if subdict:
                        for node,attr in subdict[subtype].items():
                            utils.Util_setdictval(objdict,"%s.%s.%s"%(self.objtype,node,key),attr)
            
        return objdict
        
    @classmethod
    def validateObjLayout(cls,obj_attr_dict):
        filekeys=set(obj_attr_dict.keys())
        schemakeys=set(cls.getvalidobjtypes())
        schemakeys.add('schema_version')
        invalidkeys=list(filekeys-schemakeys)
        if invalidkeys:
            raise InvalidFileException("Error: invalid keys found \""+' '.join(invalidkeys)+"\"!")
    
    def getclass(self):
        myclass = InventoryFactory.__InventoryClass__[self.objtype]
        myclass.loadschema(self.schemapath)        
        return myclass
       
          
    def importObjs(self, objlist, obj_attr_dict,update=True,envar=None,rootdir=None):
        print("starting to import \"%s\" type objects"%(self.objtype),file=sys.stdout)
        print(" preprocessing \"%s\" type objects"%(self.objtype),file=sys.stdout)
        myclass = InventoryFactory.__InventoryClass__[self.objtype]
        myclass.loadschema(self.schemapath)
        myclass.validate_schema_version(None,'import')

        dbdict = {}
        objfiles={}
        exptmsglist=[]

        outrefs=myclass.getoutref()
        partialobjdict={}

        for key, attrs in obj_attr_dict.items():
                 
            utils.verbose("  converting object \"%s\" to table entries"%(key),file=sys.stdout)
            if not objlist or key in objlist:
                if 'OBJNAME' in envar.keys() and type(attrs)==dict:
                    envar['OBJNAME']=key
                    utils.Util_subvarsindict(attrs,envar)
                else:
                    envar['OBJNAME']=key
                if self.objtype == 'osimage' and envar is not None:
                    utils.Util_setdictval(attrs,'environvars',','.join([item+'='+envar[item] for item in envar.keys()]))

                objfiles[key]=[]
                attrlist=[]
                if type(attrs)!=list:
                    attrlist.append(attrs)
                else:
                    attrlist.extend(attrs)

                for attr in attrlist:
                    for (attrpath,reftype) in outrefs.items():
                        partialobj=utils.Util_getdictval(attr,attrpath)
                        if partialobj:
                            utils.Util_setdictval(partialobjdict,"%s.%s"%(reftype[0],key),partialobj)
                            utils.Util_deldictkey(attr,attrpath)
                    try:
                        newobj = myclass.createfromfile(key, attr)
                    except InvalidValueException as e:
                        exptmsglist.append(str(e)) 
                        continue
                    objfiles[key].extend(newobj.getfilestosave(rootdir))
                    partialdbdict=newobj.getdbdata()
                    if key not in dbdict.keys():
                        dbdict.update(partialdbdict)
                    elif type(dbdict[key])==dict:
                        dbdict[key]=[dbdict[key]]
                        dbdict[key].append(partialdbdict[key])
                    elif type(dbdict[key])==list:
                        dbdict[key].append(partialdbdict[key])
        if(exptmsglist):
            raise InvalidValueException('\n'.join(exptmsglist))
        tabs=myclass.gettablist()
        if not update:
            self.getDBInst().cleartab(tabs)
        if dbdict:
            print(" writting \"%s\" type objects"%(self.objtype),file=sys.stdout)
            self.getDBInst().settab(dbdict)
        if partialobjdict:
            for subtype in partialobjdict.keys():
                subhdl = InventoryFactory.createHandler(subtype,self.dbsession,self.schemaversion)
                subdict=subhdl.importObjs(None,partialobjdict[subtype],update,envar=envar)

        return objfiles

    
    def removeObjs(self):
        self.importObjs(None,{},False,None)

    def getcurschemaversion(self):
        if self.schemapath:
            return os.path.basename(os.path.dirname(self.schemapath))

def dumpobj(objdict, fmt='yaml',location=None):
    if not fmt or fmt.lower() == 'yaml':
        dump2yaml(objdict,location)
    else:
        dump2json(objdict,location)


def dump2yaml(xcatobj, location=None):
    if not location:
        print(yaml.dump(xcatobj, default_flow_style=False))
    else:
        f=open(location,'w')
        print(yaml.dump(xcatobj, default_flow_style=False),file=f)

    #TODO: store in file or directory

def dump2json(xcatobj, location=None):
    if not location:
        print(json.dumps(xcatobj, sort_keys=True, indent=4, separators=(',', ': ')))
    else:
        f=open(location,'w')
        print(json.dumps(xcatobj, sort_keys=True, indent=4, separators=(',', ': ')),file=f)

    #TODO: store in file or directory

def validate_args(args, action):
    if args.type is not None:
        objtypelist=[]
        objtypelist.extend([n.strip() for n in args.type.split(',')])
        invalidobjtypes=list(set(objtypelist).difference(set(InventoryFactory.getvalidobjtypes())))
        if invalidobjtypes:
            raise CommandException("Error: Invalid object type: \"%(t)s\". Valid types: \"%(ts)s\"", t=','.join(invalidobjtypes),ts=','.join(InventoryFactory.getvalidobjtypes(ignorepartial=1)))
        if len(objtypelist)!=1 and args.name:
            raise CommandException("Error: object names cannot be specified with multiple object types!")
    if args.name == '':
        raise CommandException("Error: Invalid object names: \"%(o)s\"", o=args.name)
    if args.name and not args.type:
        raise CommandException("Error: Missing object type for object: %(o)s", o=args.name)
    if args.path and args.directory:
        raise CommandException("Error: -f|--path and -d|--dir cannot be used together!")
    if args.directory:
        if not os.path.exists(args.directory):
            raise CommandException("Error: the specified directory %(d)s does not exist!", d=args.directory)
        if not os.path.isdir(args.directory):
            raise CommandException("Error: the specified directory %(d)s is not a directory!", d=args.directory)
    if args.path:
        if os.path.exists(args.path):
            if not os.path.isfile(args.path):
                raise CommandException("Error: the specified file %(f)s already exists, is not a file!", f=args.path)
        else:
            mydir=os.path.dirname(args.path)
            myfile=os.path.basename(args.path)
            if not myfile:
                raise CommandException("Error: %(f)s is not a file!", f=args.path)
            if not os.path.isdir(mydir):
                raise CommandException("Error: the directory %(f)s does not exist or is not a directory!", f=mydir)
       
    if args.exclude:
        if args.type or args.name:
            raise CommandException("Error: \"-x|--exclude\" cannot be used with \"-t|--type\" or \"-o|--objects\"") 

        for et in [n.strip() for n in args.exclude.split(',')]:
            if et.lower() not in InventoryFactory.getvalidobjtypes():
                raise CommandException("Error: Invalid object type to exclude: \"%(t)s\"", t=et)
    
    if action == 'import': #extra validation for export
        if not args.path and not args.directory:
           raise CommandException("Error: expect inventory file(-f|--path) or inventory directory(-d|--direcotry)!")
        if args.path and not os.path.exists(args.path):
            raise CommandException("Error: The specified inventory file does not exist: %(p)s", p=args.path)
        if args.directory and not os.path.exists(args.directory):
            raise CommandException("Error: The specified inventory directory does not exist: %(p)s", p=args.path)

    if action == 'export': #extra validation for export
        #if args.path and (not args.type or args.type !='osimage'):
        #    raise CommandException("Error: -f|--path is only valid for -t|--type=osimage")
        if args.format and args.format.lower() not in VALID_OBJ_FORMAT:
            raise CommandException("Error: Invalid exporting format: %(f)s", f=args.format)


def export_by_type(objtype, names, destfile=None, destdir=None, fmt='yaml',version=None,exclude=[]):
    if objtype and objtype not in InventoryFactory.getObjTypesWithFiles()  and destdir:
        raise CommandException("Error: directory %(f)s specified by -f|--path is only supported when [-t|--type osimage|credential] or export all without [-t|--type] specified",f=destdir)

    if not fmt:
        fmt='yaml'
    InventoryFactory.getLatestSchemaVersion()
    dbsession=DBsession()
    
    xcatversion='XCAT Version'
    xcatversion=globalvars.xcat_version

    objlist = []
    objtypelist=[]
    exportall=0
    if objtype:
        objtypelist.extend([n.strip() for n in objtype.split(',')])
    else:
        objtypelist.extend(InventoryFactory.getvalidobjtypes(ignorepartial=1))
        exportall=1

    if names:
        objlist.extend([n.strip() for n in names.split(',')])

    wholedict={} 
    for myobjtype in objtypelist:
        if exclude and myobjtype in exclude:
            continue
        hdl = InventoryFactory.createHandler(myobjtype,dbsession,version)
        schemaversion=hdl.getcurschemaversion()
        if myobjtype in InventoryFactory.getObjTypesWithFiles() and destdir:
            if exportall:
                mylocation=os.path.join(destdir,myobjtype)
                if os.path.exists(mylocation):
                    shutil.rmtree(mylocation)
                os.mkdir(mylocation)
            else:
                mylocation=destdir
        else:
            mylocation=None
        
        typedict=hdl.exportObjs(objlist,mylocation,fmt,"#%s"%(xcatversion))
        nonexistobjlist=list(set(objlist).difference(set(typedict[myobjtype].keys())))
        if nonexistobjlist:
            raise ObjNonExistException("Error: cannot find "+myobjtype+" objects: %(f)s!", f=','.join(nonexistobjlist))
        if destdir and myobjtype in InventoryFactory.getObjTypesWithFiles():
            print("The %s objects has been exported to directory %s"%(myobjtype,destdir),file=sys.stdout)

        #do not add osimage objects to %wholedict when export inventory data to a directory
        if not destdir or myobjtype not in InventoryFactory.getObjTypesWithFiles():
            wholedict.update(typedict)
      
    wholedict['schema_version']=schemaversion    
   
    for myobjtype in InventoryFactory.getObjTypesWithFiles():
        if myobjtype in objtypelist and destdir:
            objtypelist.remove(myobjtype)

    if objtypelist:
        if destdir and exportall==1:
            if not fmt or fmt.lower() == 'yaml':
                mylocation=os.path.join(destdir,'cluster.yaml')
            else:
                mylocation=os.path.join(destdir,'cluster.json')

            dumpobj(wholedict, fmt,mylocation)
            if fmt.lower() == 'yaml':
                with open(mylocation, "a") as myfile:
                    myfile.write("#%s"%(xcatversion))
            print("The cluster inventory data has been dumped to %s"%(mylocation),file=sys.stdout)
        elif destfile:
            dumpobj(wholedict, fmt,destfile)
            if fmt.lower() == 'yaml':
                with open(destfile, "a") as myfile:
                    myfile.write("#%s"%(xcatversion))
            print("The inventory data has been dumped to %s"%(destfile),file=sys.stdout)
        else: 
            if not fmt or fmt.lower() == 'yaml':
                dump2yaml(wholedict)
                print("#%s"%(xcatversion))
            elif fmt == 'dict':
                dbsession.close()
                return wholedict
            else:
                dump2json(wholedict)

    dbsession.close() 


#get git related variable dict
#return None if not in a git
def getgitinfo(location):
    #vardict['GITBRANCH']=''
    #vardict['GITTAG']='' 
    #vardict['GITCOMMIT']=''
    #vardict['GITROOT']=''
    vardict={}
    oldcwd=os.getcwd()
    os.chdir(os.path.dirname(os.path.realpath(location)))
    (retcode,out,err)=utils.runCommand("git rev-parse --show-toplevel")
    if retcode==0:
        out=out.strip()
        vardict['GITROOT']=out.strip()
    else:
        #not a git repo
        os.chdir(oldcwd)
        return None

    (retcode,out,err)=utils.runCommand("git branch|grep '*'|cut -d' ' -f2-")
    if retcode==0:
        out=out.strip()
        matched=re.search(r'\(detached from (.*)\)',out)
        if matched:
            out=matched.group(1).strip()
        vardict['GITBRANCH']=out

    (retcode,out,err)=utils.runCommand("git describe  --candidates 0")
    if retcode==0:
        out=out.strip()
        matched=re.search(r'\(detached from (.*)',out)
        vardict['GITTAG']=out.strip()
    
    (retcode,out,err)=utils.runCommand("git rev-parse --short=7 HEAD")
    if retcode==0:
        out=out.strip()
        vardict['GITCOMMIT']=out.strip()
    os.chdir(oldcwd)
    return vardict



def importfromfile(objtypelist,objlist,filepath,dryrun=None,version=None,update=True,dbsession=None,envs=None,rootdir=None,exclude=[]):
    location=filepath
    dirpath=os.path.dirname(os.path.realpath(location))
    filename=os.path.basename(os.path.realpath(location))
    
    jinjaenv=Environment(loader=FileSystemLoader(dirpath)); 
    jinjasrc=jinjaenv.loader.get_source(jinjaenv,filename)[0]
    jinjatmpl=jinjaenv.get_template(filename)
    jinjast = jinjaenv.parse(jinjasrc)
    jinjavarlist=meta.find_undeclared_variables(jinjast)
    vardict={}
    if envs:
        vardict=envs
      
    # the value '{{OBJNAME}}' indicates that a variable substitute should be taken during import
    if 'OBJNAME' in list(jinjavarlist):
        vardict['OBJNAME']='{{OBJNAME}}'

    gitvardict=getgitinfo(location) 
    if gitvardict:
        vardict.update(gitvardict)

    unresolvedvars=list(set(jinjavarlist).difference(set(vardict.keys())))
    if unresolvedvars:
        raise ParseException("unresolved variables in \"%s\": \"%s\", please export them in environment variables"%(location,','.join(unresolvedvars))) 
    
    contents=jinjatmpl.render(vardict) 
 
    envar=vardict
    if dbsession is None: 
        dbsession=DBsession()
    print("loading inventory data from \"%s\""%(location),file=sys.stdout)
    try:

        obj_attr_dict = json.loads(contents)
    except ValueError:
        try: 
            obj_attr_dict = yaml.load(contents,Loader=Loader)
        except Exception as e:
            raise InvalidFileException("Error: failed to load file \"%s\", please validate the file with 'yamllint %s'(for yaml format) or 'cat %s|python -mjson.tool'(for json format)!"%(location,location,location))
  
    versinfile=None
    if 'schema_version' in obj_attr_dict.keys():
        versinfile=obj_attr_dict['schema_version']
        del obj_attr_dict['schema_version']
    if not versinfile or versinfile == 'latest':
        versinfile=InventoryFactory.getLatestSchemaVersion()
    if version == 'latest':
        version=InventoryFactory.getLatestSchemaVersion()
    if version and version != versinfile:
        raise CommandException("Error: the specified schema version \""+version+"\" does not match the schema_version \""+versinfile+"\" in input file "+location ) 
    version=versinfile
   
    InventoryFactory.validateObjLayout(obj_attr_dict) 
    objfiledict={}
    exptmsglist=[]
    if objtypelist: 
        objtypelist=list(set(objtypelist)-set(exclude))
        nonexistobjtypelist=list(set(objtypelist).difference(set(obj_attr_dict.keys())))
        if nonexistobjtypelist:
            raise ObjTypeNonExistException("Error: cannot find object types: %(f)s in the file "+location+'!', f=','.join(nonexistobjtypelist))
        for myobjtype in objtypelist:
            if objlist:
                nonexistobjlist=list(set(objlist).difference(set(obj_attr_dict[myobjtype].keys())))
                if nonexistobjlist:
                    raise ObjNonExistException("Error: cannot find %(t)s objects: %(f)s!",t=myobjtype,f=','.join(nonexistobjlist))
            hdl = InventoryFactory.createHandler(myobjtype,dbsession,version)
            if myobjtype not in objfiledict.keys():
                objfiledict[myobjtype]={}
            try: 
                objfiledict[myobjtype].update(hdl.importObjs(objlist, obj_attr_dict[myobjtype],update,envar,rootdir))
            except InvalidValueException as e:
                exptmsglist.append(str(e))
                continue
    else:
        for objtype in obj_attr_dict.keys():#VALID_OBJ_TYPES:
            if objtype in exclude:
                continue
            hdl = InventoryFactory.createHandler(objtype,dbsession,version)
            if objtype not in objfiledict.keys():
                objfiledict[objtype]={}
            try: 
                objfiledict[objtype].update(hdl.importObjs([], obj_attr_dict[objtype],update,envar,rootdir))
            except InvalidValueException as e:
                exptmsglist.append(str(e))
                continue

    if exptmsglist:
        raise InvalidValueException('\n'.join(exptmsglist))
    if not dryrun:
        try:
            dbsession.commit()   
        except Exception as e:
            raise DBException("Error on commit DB transactions: "+str(e))
        else:
            print('Inventory imported successfully',file=sys.stdout)
    else:
        print("Dry run mode, nothing will be written to database!",file=sys.stdout)
    dbsession.close()
    return objfiledict


def importobjdir(location,dryrun=None,version=None,update=True,dbsession=None,envs=None,objtype=None):
    objfile=None
    if os.path.exists(os.path.join(location,'definition.yaml')):
        objfile=os.path.join(location,'definition.yaml')
    elif os.path.exists(os.path.join(location,'definition.json')):
        objfile=os.path.join(location,'definition.json')    
    else:
        raise InvalidFileException("Error: no definition.json or definition.yaml found under \""+location+"\""+"!")
    if objtype and type(objtype) != list:
       objtype=[objtype]
    objfilesdict=importfromfile(objtype,None,objfile,dryrun,version,update,dbsession,envs,location)
    if len(objfilesdict.keys()) !=1:
        raise InvalidFileException("Error: invalid definition file: \""+objfile+"\": should contain only 1 object type")  
    else:
        objtype=list(objfilesdict.keys())[0]
    if len(objfilesdict[objtype].keys()) !=1:
        raise InvalidFileException("Error: invalid definition file: \""+objfile+"\": should contain only 1 object")
    else:
        objname=list(objfilesdict[objtype].keys())[0]
    objfiles=objfilesdict[objtype][objname]
    for myfile in objfiles:
        srcfile=location+myfile
        if os.path.exists(srcfile):
            if dryrun:
                print("creating directory: %s. Dryrun mode, do nothing..."%(os.path.dirname(myfile)),file=sys.stdout)
            else:
                try:
                    os.makedirs(os.path.dirname(myfile))
                except OSError as e:
                    if e.errno != os.errno.EEXIST:
                        raise
                    pass
            if os.path.exists(myfile):
                print("Warning: the %s already exists, will be overwritten"%(myfile), file=sys.stderr)
            if os.path.exists(myfile) and os.path.samefile(srcfile,myfile):
                print("Warning: \"%s\" and \"%s\" are the same file, skip copy"%(srcfile,myfile),file=sys.stderr)
            else:
                if dryrun:
                    print("copying file: %s ----> %s. Dryrun mode, do nothing..."%(srcfile,myfile),file=sys.stdout)
                else:
                    try:
                        shutil.copyfile(srcfile,myfile)
                    except Exception as e:
                        raise InvalidFileException("Error encountered while copying \"%s\" to \"%s\":\n%s"%(srcfile,myfile,str(e)))
        else:
            print("Warning: the file \""+srcfile+"\" of "+objtype+" \""+objname+"\" does not exist!",file=sys.stderr)
    print("The object "+objname+" has been imported",file=sys.stdout)

#import objects from object type inventory directory
def importfromdir(location,objtype=None,objnamelist=None,dryrun=None,version=None,update=True,dbsession=None,envs=None):
    importall=0
    typeobjdict=utils.traverseobjdir(location)
    if typeobjdict:
        objtypeindir=list(typeobjdict.keys())[0]
        objnamesindir=typeobjdict[objtypeindir]
        if objtype is None:
            objtype=objtypeindir
        if not objnamelist:
            objnamelist=objnamesindir
            importall=1
    if objtype is None:
        raise ObjTypeNonExistException("Error: cannot find any xCAT inventory object in directory \"%s\""%(location))

    if update==False:
        if dbsession is None:
            dbsession=DBsession()
        hdl = InventoryFactory.createHandler(objtype,dbsession,version)
        hdl.removeObjs()
        update=True
    objnotfound=[]
    for objname in objnamelist:
        if os.path.exists(os.path.join(location,objname)):
            objdir=os.path.join(location,objname)
            if importall:
                try:
                    importobjdir(objdir,dryrun,version,update,dbsession,envs,objtype)
                except ObjTypeNonExistException:
                       raise ObjTypeNonExistException("cannot find \"%s\" type objects in directory \"%s\""%(objtype,objtype))
            else:
                importobjdir(objdir,dryrun,version,update,dbsession,envs,objtype)
        else:
            objnotfound.append(objname)

    if objnotfound:
        raise ObjTypeNonExistException("the specified object \"%s\" does not exist under \"%s\"!"%(','.join(objnotfound),location),file=sys.stderr)

    if dbsession:
        dbsession.commit()
        dbsession.close()

     
def importobj(srcfile,srcdir,objtype,objnames=None,dryrun=None,version=None,update=True,envs=None,env_files=None,exclude=[]):
     objtypelist=[]
     importallobjtypes=0
     if objtype:
         objtypelist=[n.strip() for n in objtype.split(',')]
     else:
         importallobjtypes=1

     objnamelist=[]
     if objnames:
         objnamelist=[n.strip() for n in objnames.split(',')]

     vardict = {}

     if env_files:
        for env_file in env_files:
            try:
                f = open(env_file)
                vardict.update( yaml.load(f) )
                f.close()
            except Exception:
                raise InvalidFileException("Error: Failed to load variable file '%s', please check ..." % env_file)

     if envs:
        for env in envs:
            key, value = env.split('=')
            vardict[key] = value 

     envs = vardict

     dbsession=None

     if srcfile and os.path.isfile(srcfile):
         importfromfile(objtypelist, objnamelist,srcfile,dryrun,version,update,dbsession,envs=envs,rootdir=None,exclude=exclude)
     elif srcdir and os.path.isdir(srcdir):
         clusterfile=None
         if os.path.isfile(os.path.join(srcdir,'cluster.yaml')):
             clusterfile=os.path.join(srcdir,'cluster.yaml')
         elif os.path.isfile(os.path.join(srcdir,'cluster.json')):
             clusterfile=os.path.join(srcdir,'cluster.json')

         #this is a cluster inventory directory
         if clusterfile:
             myobjtypelist=[]
             if objtypelist:
                  myobjtypelist.extend(objtypelist)
             if importallobjtypes:
                  myobjtypelist.extend(InventoryFactory.getvalidobjtypes(ignorepartial=1)) 
             if exclude:
                  myobjtypelist=list(set(myobjtypelist)-set(exclude))
             objdirs=[d for d in os.listdir(srcdir) if os.path.isdir(os.path.join(srcdir,d)) and (d in myobjtypelist or (importallobjtypes and d in list(set(InventoryFactory.getvalidobjtypes())-set(exclude))))]
             for dirtoimport in objdirs:
                 myobjtypelist.remove(dirtoimport)
                 importfromdir(os.path.join(srcdir,dirtoimport),dirtoimport,objnamelist,dryrun,version,update,dbsession,envs=envs)
             if myobjtypelist or importallobjtypes:
                 importfromfile(myobjtypelist,objnamelist,clusterfile,dryrun,version,update,dbsession,envs=envs)
         else:
             objfile=None
             if os.path.isfile(os.path.join(srcdir,'definition.yaml')):
                 objfile=os.path.join(srcdir,'definition.yaml')
             elif os.path.isfile(os.path.join(srcdir,'definition.json')):
                 objfile=os.path.join(srcdir,'definition.json')

             myobjtypelist=[]
             if objtypelist:
                  myobjtypelist.extend(objtypelist)
             #if importallobjtypes:
             #     myobjtypelist.extend(InventoryFactory.getvalidobjtypes()) 
             for myobjtype in list(set(InventoryFactory.getObjTypesWithFiles())-set(exclude)): 
                 if myobjtype in myobjtypelist or importallobjtypes:
                     if importallobjtypes:
                         myobjtype=None
                     if objfile:
                         curobjname=os.path.basename(os.path.realpath(srcdir))
                         #this is an osimage derectory
                         if objnames:
                             if curobjname in objnamelist: 
                                 importfromdir(srcdir+'/../',myobjtype,[curobjname],dryrun,version,update,dbsession,envs=envs)
                                 objnamelist.remove(curobjname)
                             if objnamelist:
                                 raise InvalidFileException("Error: non-exist objects: \""+','.join(objnamelist)+"\" in inventory directory "+srcdir+"!")        
                         else:
                             #import current object
                             try:
                                 importobjdir(srcdir,dryrun,version,update,dbsession,envs,myobjtype)
                             except ObjTypeNonExistException as e:
                                 if importallobjtypes:
                                     print(str(e),file=sys.stderr)
                                     continue
                                 else:
                                     raise ObjTypeNonExistException(str(e))

                     else:
                         try:
                             #this is an obj inventory directory for a objtype
                             importfromdir(srcdir,myobjtype,objnamelist,dryrun,version,update,dbsession,envs=envs)
                         except ObjTypeNonExistException as e:
                             if importallobjtypes:
                                 print(str(e),file=sys.stderr)
                                 continue
                             else:
                                 raise ObjTypeNonExistException(str(e))
                          
                     if myobjtype in objtypelist:
                         objtypelist.remove(myobjtype)
 
                 if importallobjtypes:
                     break
   
             if objtypelist:
                 raise InvalidFileException("Error: non-exist object types: \""+','.join(objtypelist)+"\" in inventory directory "+srcdir+"!")
          

              
def envlist():
    print("%s : %s\n"%('Notice','refer the variables in the inventory file with format "{{variable name}}"'))
    print('%-15s : %s'%('variable name','description')) 
    for key in globalvars.implicitEnvVars.keys():
        print('%-15s : %s'%(key,globalvars.implicitEnvVars[key]['description'])) 

