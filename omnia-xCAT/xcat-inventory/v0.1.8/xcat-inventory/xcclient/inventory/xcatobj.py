#!/usr/bin/python2
###############################################################################
# IBM(c) 2007 EPL license http://www.eclipse.org/legal/epl-v10.html
###############################################################################
# -*- coding: utf-8 -*-
#
import yaml

import sys
import re
from copy import *

from .dbobject import *
from .dbfactory import *
from .exceptions import *
from .utils import *
from .vutil import *
from . import vutil
#import pdb




class XcatBase(object):
    _schema=None
    _schema_loc__ = None

    _depdict_tab=None
    _depdict_val=None
    _files={}

    def __init__(self, objname, dbhash=None, objdict=None, schema=None):
        self.name=objname
        self._dbhash = {}
        self._mydict = {}

        if schema:
            self.__class__.loadschema(schema)
        if objdict is not None:
            self.setobjdict(objdict)
        elif dbhash is not None:
            self.setdbdata(dbhash)

    @classmethod
    def __gendepdict(cls,schmpath):
        valregex=re.compile("^\$\{\{((.*):(.*))\}\}\s*$")
        revregex=re.compile("^W:T\{(\S+)\}=(.+)$")
        validateregex=re.compile("^C:(.+)$")
        tabentregex=re.compile("T\{(.*?)\}")
        dictvalregex=re.compile("V\{(.*?)\}")
        filevalregex=re.compile("^F:(.+)$")
        refregex=re.compile("^REF\{(.+)\}$")
 
        def __parselambda(expression):
            mtchdval=re.findall(valregex,expression)
            if not mtchdval:
                mtchdval=[(':'+expression,'',expression)]
            ret={}
            ret['tabsinparam']=[]
            ret['tabsinbody']=[]
            ret['valsinparam']=[]
            ret['valsinbody']=[]
            ret['expression']=[]

            (expression,paramstr,bodystr)=mtchdval[0]
            if expression:
                ret['expression']=expression
            if paramstr:
                mtchdtabval=re.findall(tabentregex,paramstr)
                if mtchdtabval:
                    ret['tabsinparam'].extend(mtchdtabval)
                mtchdval=re.findall(dictvalregex,paramstr)
                if mtchdval:
                    ret['valsinparam'].extend(mtchdval)
            if bodystr:
                mtchdtabval=re.findall(tabentregex,bodystr)
                if mtchdtabval:
                    ret['tabsinbody'].extend(mtchdtabval)
                mtchdval=re.findall(dictvalregex,bodystr)
                if mtchdval:
                    ret['valsinbody'].extend(mtchdval)                
            return ret

       
        rawvalue=Util_getdictval(cls._schema,schmpath)
        if not rawvalue:
            return False
        if isinstance(rawvalue,list):
            rawvaluelist=rawvalue
        else:
            rawvaluelist=[rawvalue]  
        cls._depdict_val[schmpath]={}
       
        fwdrules=[] 
        revrules=[]
        validaterules=[]
        filerules=[]
        refrules=[]
        #print(rawvaluelist)
        for item in rawvaluelist:
            if not re.match(valregex,item) and not re.match(revregex,item) and not re.match(validateregex,item) and not re.match(filevalregex,item) and not re.match(refregex,item):
                item='${{:'+item+'}}'
                fwdrules.append(item)
            elif re.match(valregex,item): 
                fwdrules.append(item)
            elif re.match(revregex,item):
                revrules.append(item)
            elif re.match(validateregex,item):
                validaterules.append(item)
            elif re.match(filevalregex,item):
                filerules.append(item)
            elif re.match(refregex,item):
                refrules.append(item)
  
        if filerules:
            if schmpath not in cls._files.keys(): 
                cls._files[schmpath]={}
            cls._files[schmpath]['file2savefilter']={}
            cls._files[schmpath]['file2savefilter']['depvallist']=[]
            cls._files[schmpath]['file2savefilter']['expression']=[]
            for item in filerules:
                myexpression=re.findall(filevalregex,item)[0]
                ret=__parselambda(myexpression)
                if ret['expression']:
                    cls._files[schmpath]['file2savefilter']['expression'].append(ret['expression'])
                if ret['valsinparam']:
                    cls._files[schmpath]['file2savefilter']['depvallist'].extend(ret['valsinparam']) 
                if ret['valsinbody']:
                    cls._files[schmpath]['file2savefilter']['depvallist'].extend(ret['valsinbody'])

        cls._depdict_val[schmpath]['validate']={}
        cls._depdict_val[schmpath]['validate']['depvallist']=[]
        cls._depdict_val[schmpath]['validate']['expression']=[]
        for item in validaterules:
            myexpression=re.findall(validateregex,item)[0] 
            ret=__parselambda(myexpression)
            cls._depdict_val[schmpath]['validate']['expression'].append(ret['expression'])
            cls._depdict_val[schmpath]['validate']['depvallist'].extend(ret['valsinparam'])
            cls._depdict_val[schmpath]['validate']['depvallist'].extend(ret['valsinbody'])

        for item in fwdrules:
            ret=__parselambda(item)
            cls._depdict_val[schmpath]['depvallist']=[]
            cls._depdict_val[schmpath]['depvallist'].extend(ret['valsinparam'])
            cls._depdict_val[schmpath]['deptablist']=[]
            cls._depdict_val[schmpath]['deptablist'].extend(ret['tabsinparam'])
            cls._depdict_val[schmpath]['deptablist'].extend(ret['tabsinbody'])
            cls._depdict_val[schmpath]['expression']=ret['expression']    
           
            for tabcol in ret['tabsinbody']:
                cls._depdict_tab[tabcol]={} 
                cls._depdict_tab[tabcol]['schmpath']=schmpath
                cls._depdict_tab[tabcol]['deptablist']=[]
                cls._depdict_tab[tabcol]['deptablist'].extend(ret['tabsinparam'])
                cls._depdict_tab[tabcol]['depvallist']=[]
                cls._depdict_tab[tabcol]['depvallist'].extend(ret['valsinparam'])
                cls._depdict_tab[tabcol]['expression']=ret['expression']

        for item in revrules:
             (tabcol,myexpression)=re.findall(revregex,item)[0]
             ret=__parselambda(myexpression)
             cls._depdict_tab[tabcol]={} 
             cls._depdict_tab[tabcol]['expression']=ret['expression']
             cls._depdict_tab[tabcol]['deptablist']=[]
             cls._depdict_tab[tabcol]['deptablist'].extend(ret['tabsinparam'])
             cls._depdict_tab[tabcol]['deptablist'].extend(ret['tabsinbody'])
             cls._depdict_tab[tabcol]['depvallist']=[]
             cls._depdict_tab[tabcol]['depvallist'].extend(ret['valsinparam'])
             cls._depdict_tab[tabcol]['depvallist'].extend(ret['valsinbody'])
             cls._depdict_tab[tabcol]['schmpath']=''
     
        refdict={}
        for item in refrules:
             refentry=re.findall(refregex,item)[0]
             refdict[refentry]=1
        if refdict:
            if schmpath not in cls._depdict_ref.keys():
                cls._depdict_ref[schmpath]=[]
            cls._depdict_ref[schmpath].extend(refdict.keys())     
            if schmpath in cls._depdict_val.keys():
                del cls._depdict_val[schmpath]
                
        return True

    @classmethod
    def __scanschema(cls,schmdict,schmpath=None):
        for key in schmdict.keys():
            if schmpath:
                curpath=schmpath+'.'+key
            else:
                curpath=key
            if isinstance(schmdict[key],dict):
                cls.__scanschema(schmdict[key],curpath)
            else:
                cls.__gendepdict(curpath)
    @classmethod
    def scanschema(cls):
        cls._depdict_tab={}
        cls._depdict_val={}
        cls._depdict_ref={}
        cls._files={}
        cls.__scanschema(cls._schema)

    @classmethod
    def getoutref(cls):
        return cls._depdict_ref

    def __evalschema_tab(self,tabcol):
        mydeptablist=self._depdict_tab[tabcol]['deptablist']
        mydepvallist=self._depdict_tab[tabcol]['depvallist']
        myexpression=self._depdict_tab[tabcol]['expression']
        myschmpath=self._depdict_tab[tabcol]['schmpath']
        ctxdict={}
        for item in mydepvallist:
            myval=Util_getdictval(self._mydict,item)
            if myval is None:
                myval=''
            newitem=item.replace('.','_').replace('{','_').replace('}','_')
            newitem="V_%s"%(newitem)
            ctxdict[newitem]=myval
            myexpression=myexpression.replace('V{'+item+'}',newitem)
        for item in mydeptablist:
            tabval=''
            if item in self._dbhash.keys():
                tabval=self._dbhash[item]
            else:
                tabval=self.__evalschema_tab(item) 
            myexpression=myexpression.replace('T{'+item+'}',"'"+str(tabval).replace("'","\\'")+"'")   
        tabmatched=re.findall(r'T\{(\S+)\}',myexpression)
        if tabmatched:
            for item in tabmatched:
                if myschmpath: 
                    myexpression=myexpression.replace('T{'+item+'}',"'"+str(item).replace("'","\\'")+"'")
                else:
                    tabval=self.__evalschema_tab(item)
                    myexpression=myexpression.replace('T{'+item+'}',"'"+str(tabval).replace("'","\\'")+"'")
        evalexp=eval("lambda "+myexpression,None,ctxdict)
        result=evalexp()
        if myschmpath:
            if sys.version_info < (3,0):
                equal = bool(0 == cmp(result,tabcol))
            else:
                result = result or ''
                equal = bool(0 == (result > tabcol) - (result < tabcol))
            if equal :
                value=Util_getdictval(self._mydict,myschmpath)
                self._dbhash[tabcol]=value
            else:
                self._dbhash[tabcol]=''
            return self._dbhash[tabcol]
        else:
            self._dbhash[tabcol]=result
        
    def __evalschema_val(self,valpath):
        mydeptablist=self._depdict_val[valpath]['deptablist']
        mydepvallist=self._depdict_val[valpath]['depvallist']
        myexpression=self._depdict_val[valpath]['expression']
        for item in mydeptablist:    
            tabval=''
            if item in self._dbhash.keys():
                tabval=self._dbhash[item]
            if tabval is None:
                tabval=''
            myexpression=myexpression.replace('T{'+item+'}',"'"+str(tabval).replace("'","\\'")+"'")
        ctxdict={} 
        for item in mydepvallist:
            myval=Util_getdictval(self._mydict,item)
            if myval is None:
                myval=self.__evalschema_val(item)
                if myval is None:
                    myval=''
            newitem=item.replace('.','_').replace('{','_').replace('}','_')
            newitem="V_%s"%(newitem)
            ctxdict[newitem]=myval
            myexpression=myexpression.replace('V{'+item+'}',newitem)
        try:
            evalexp=eval("lambda "+myexpression,None,ctxdict)
            value=evalexp()
        except Exception as e:
            raise  InvalidValueException("Error: failed to process schema entry ["+valpath+"]: \""+myexpression+"\": "+str(e))
        Util_setdictval(self._mydict,valpath,value)
        return value 
                   

    def __dict2db(self):
        for key in self._depdict_tab.keys():
            self.__evalschema_tab(key)
            
    def __db2dict(self):
        for key in self._depdict_val.keys():
            self.__evalschema_val(key)
        
    @classmethod
    def createfromdb(cls,objname, dbhash):
        if not cls._schema:
            cls.loadschema(cls._schema_loc__)
        return cls(objname, dbhash=dbhash)

    @classmethod
    def createfromfile(cls,objname, objdict):
        if not cls._schema:
            cls.loadschema(cls._schema_loc__)
        return cls(objname, objdict=objdict)
  
    @classmethod
    def validate_schema_version(cls,schemapath=None,action='export'):
        if schemapath is None:
            schemapath=cls._schema_loc__
            schema=cls._schema
        else:
            try:
                schemacontent = yaml.load(open(schemapath, 'r'), Loader=Loader)
            except Exception as e:
                raise BadSchemaException("Error: Invalid schema file \"%s\": %s" % (schemapath, e))
            schmkey=list(schemacontent.keys())[0]
            schema=schemacontent[schmkey]
   
        ctxdict={}
        if schema and 'criteria' in schema.keys():
            criteria=schema['criteria']
            criterialist=[]
            ctxdict['action']=action
            if type(criteria) == str:
                criterialist.append(criteria)
            elif type(criteria) == list:
                criterialist=criteria
            for expression in criterialist:
                validateregex=re.compile("^C:\$\{\{(.+)\}\}$")
                mtchdval=re.findall(validateregex,expression)
                rule=mtchdval[0]

                try:
                    evalexp=eval("lambda "+rule,None,ctxdict)
                    (value,errmsg)=evalexp()
                except Exception as e:
                    raise  InternalException("Error: encountered some error when validating version of schema \"%s\": %s"%(schemapath,str(e)))
                if not value:
                    raise BadSchemaException("Error: invalid schema %s: %s"%(schemapath,errmsg))
            del(schema['criteria'])
            if cls._depdict_val and 'criteria' in cls._depdict_val.keys():
                del(cls._depdict_val['criteria'])
         
        
    @classmethod
    def loadschema(cls,schema=None):
        if schema is None:
            schema=cls._schema_loc__
        #cls._schema=yaml.load(open(schema,'r'))['node']
        try: 
            schemacontent=yaml.load(open(schema, 'r'), Loader=Loader)
        except Exception as e:
            raise BadSchemaException("Error: Invalid schema file \"%s\": %s" % (schema, e))
        schmkey=list(schemacontent.keys())[0]
        cls._schema=schemacontent[schmkey] 
        cls._schema_loc__=schema
        cls.scanschema()


    @classmethod
    def gettablist(cls):
        tabdict={}
        for mykey in cls._depdict_val.keys():
            if 'deptablist' in cls._depdict_val[mykey].keys():
                for tabcol in cls._depdict_val[mykey]['deptablist']:
                    (mytab,mycol)=tabcol.split('.')
                    tabdict[mytab]=1
        return tabdict.keys() 

    def getobjdict(self):
        ret={}
        ret[self.name]=deepcopy(self._mydict)
        Util_rmnullindict(ret[self.name])
        del ret[self.name]['obj_name']
        return ret
  
    def validatelayout(self,objdict):
        def _dictcmp(schemadict,objdict,invalidkeylist,curpath=''):
           if isinstance(objdict,dict):
               if not isinstance(schemadict,dict):
                   invalidkeylist.append(curpath)
                   return
               for key in objdict.keys():
                   if key in schemadict:
                       _dictcmp(schemadict[key],objdict[key],invalidkeylist,curpath+'.'+key)
                   else:
                       invalidkeylist.append(curpath+'.'+key)
           else:
               pass

        if not isinstance(objdict,dict):
            raise InvalidFileException("Error: invalid object definition of "+self.name)
        
        invalidkeylist=[]
        _dictcmp(self.__class__._schema,objdict,invalidkeylist)
        if invalidkeylist:
            raise InvalidFileException("Error: invalid keys \""+','.join(invalidkeylist)+"\" found in object definition of "+self.name)

        return       
        
    def validatevalue(self,objdict):
        errmsglist=[]
        retcode=True
        for key in self._depdict_val.keys():
            depvallist=self._depdict_val[key]['validate']['depvallist']
            expression=self._depdict_val[key]['validate']['expression']
            for myexpression in expression:
                for val in depvallist:
                    myval=Util_getdictval(objdict,val)
                    if myval is None:
                        myval=''
                    myexpression=myexpression.replace('V{'+val+'}',"'"+str(myval).replace("'","\\'")+"'")                    
                try:
                    evalexp=eval("lambda "+myexpression)
                    value=evalexp()
                except Exception as e:
                    raise  InternalException("Error: encountered some error when validate attribute ["+key+"] of object \""+self.name+"\": "+str(e)) 
                if not value:
                    retcode=False
                    errmsglist.append("Error: failed to validate attribute ["+key+"] of object \""+self.name+"\", criteria: \""+myexpression+"\"") 
        return [retcode,errmsglist]

    @classmethod
    def getfilerules(cls):
        print(yaml.dump(cls._files))

    def getfilestosave(self,rootdir=None):
        filelist=[]
        for key in self._files.keys():
            depvallist=self._files[key]['file2savefilter']['depvallist']
            expression=self._files[key]['file2savefilter']['expression'] 
            for myexpression in expression:
                ctxdict={}
                ctxdict['exvar_objdir']=rootdir
                for val in depvallist:
                    myval=Util_getdictval(self._mydict,val)
                    if myval is None:
                        myval=''
                    newitem=val.replace('.','_').replace('{','_').replace('}','_')
                    newitem="V_%s"%(newitem)
                    ctxdict[newitem]=myval
                    myexpression=myexpression.replace('V{'+val+'}',newitem)
                try:
                    evalexp=eval("lambda "+myexpression,None,ctxdict)
                    value=evalexp()
                except Exception as e:
                    raise  InvalidValueException("Error: encountered some error when get the files to save in [%s] of object \"%s\": %s"%(key,self.name,str(e))) 
                if value:
                    filelist.extend(filter(None,value))
        return filelist
                

    def setobjdict(self,objdict):
        self.validatelayout(objdict)
        retcode,msglist=self.validatevalue(objdict)
        if not retcode:
            raise InvalidValueException('\n'.join(msglist)) 
        self._mydict=deepcopy(objdict)
        self._mydict['obj_name']=self.name
        self._dbhash.clear()
        self.__dict2db()

    def getdbdata(self):
        ret={}
        ret[self.name]=deepcopy(self._dbhash)
        return ret

    def setdbdata(self,dbhash):
        self._dbhash=deepcopy(dbhash)
        self._mydict.clear()
        self._mydict['obj_name']=self.name
        self.__db2dict()


class Node(XcatBase):
    _schema_loc__ = os.path.join(os.path.dirname(__file__), 'schema/latest/node.yaml')
    def getobjdict(self):
        ret={}
        ret=super(Node,self).getobjdict()
        macpath=""
        nicspath=""
        for item in Node._depdict_val.keys():
            if re.match(r'^\S+\.mac$',item):
                macpath=item
            matchedpath=re.findall(r'^(\S+\.nics)\.\S+$',item)
            if matchedpath:
                nicspath=matchedpath[0]
            if macpath and nicspath:
                break
        if macpath:
            mac=Util_getdictval(self._mydict,macpath)
            if mac and not isinstance(mac,list):
                if re.match(r'[^\|]\S+[^\|]$',mac):
                    Util_setdictval(ret[self.name],macpath,mac.split('|'))
                else:
                    Util_setdictval(ret[self.name],macpath,[mac])
        if nicspath:
            rawnicsdict=Util_getdictval(ret[self.name],nicspath)
            if rawnicsdict:
                nicsdict={}
                try:
                    for key in rawnicsdict.keys():
                        string=rawnicsdict[key]
                        regexattr2=re.findall(r'((,|^)\|([^\|]*)\|([^\|]*)\|)',string)
                        for i in regexattr2:
                            # remove the matched part from string
                            string=string.replace(i[0],'')
                            regcond=i[2]
                            regbody=i[3]
                            while True:
                                bodyattr2=re.findall(r'((,)?([^,^!]*)!([^!]*))(?:,[^,]+!|$)',regbody)
                                if not bodyattr2:
                                    break
                                for j in bodyattr2:
                                    regbody=regbody.replace(j[0],'')  
                                    nic=j[2]
                                    regexpr=j[3]
                                    if nic not in nicsdict.keys():
                                        nicsdict[nic]={}
                                    nicsdict[nic][key]='|'+regcond+'|'+nic+'!'+regexpr+'|'   
                        regexattr=re.findall(r'((,|^)([^\|^,]*)!(\|[^\|]*\|[^\|]*\|))',string)
                        for i in regexattr:
                            # remove the matched part from string
                            string=string.replace(i[0],'')
                            nic=i[2]
                            nicattr=i[3]
                            if nic not in nicsdict.keys():
                                nicsdict[nic]={}   
                            nicsdict[nic][key]=nicattr
                        plainattr=re.findall(r'(,|^)([^\|^,]*)!([^\|^,][^,]*)',string)
                        for i in plainattr:
                            nic=i[1]
                            nicattr=i[2]
                            if nic not in nicsdict.keys():
                                nicsdict[nic]={}
                            nicsdict[nic][key]=nicattr.split('|')
                except Exception:
                    raise InvalidValueException("Error: invalid value \""+key+"\" for object "+self.name+" found "+"in nics table")
                Util_setdictval(ret[self.name],nicspath,nicsdict)
        return ret

    def setobjdict(self,objdict):
        tmpdict=deepcopy(objdict)
        macpath=""
        nicspath=""
        for item in Node._depdict_val.keys():
            if re.match(r'^\S+\.mac$',item):
                macpath=item
            matchedpath=re.findall(r'^(\S+\.nics)\.\S+$',item)
            if matchedpath:
                nicspath=matchedpath[0]
            if macpath and nicspath:
                break
        if macpath:
            mac=Util_getdictval(tmpdict,macpath)
        if mac and isinstance(mac,list):
            Util_setdictval(tmpdict,macpath,'|'.join(mac))         
        if nicspath:
            nicattrstr=''
            nicsattrdict={}
            rawnicsdict=Util_getdictval(tmpdict,nicspath)
            if rawnicsdict:
                for nic in rawnicsdict.keys():
                    nicattr=rawnicsdict[nic]
                    for attr in nicattr.keys():
                         if attr not in nicsattrdict.keys():
                             nicsattrdict[attr]=[]
                         attrvalue=''
                         if type(nicattr[attr]) == list:
                             attrvalue='|'.join(nicattr[attr])
                         else:
                             attrvalue=nicattr[attr]
                         if '!' not in attrvalue:
                             attrvalue=nic+'!'+attrvalue
                         nicsattrdict[attr].append(attrvalue)
                for item in nicsattrdict.keys():
                    nicsattrdict[item]=','.join(nicsattrdict[item])
                Util_setdictval(tmpdict,nicspath,nicsattrdict)
        super(Node,self).setobjdict(tmpdict)
    
class Osimage(XcatBase):
    _schema_loc__ = os.path.join(os.path.dirname(__file__), 'schema/latest/osimage.yaml')
    
class Network(XcatBase):
    _schema_loc__ = os.path.join(os.path.dirname(__file__), 'schema/latest/network.yaml')

class Route(XcatBase):
    _schema_loc__ = os.path.join(os.path.dirname(__file__), 'schema/latest/route.yaml')

class Policy(XcatBase):
    _schema_loc__ = os.path.join(os.path.dirname(__file__), 'schema/latest/policy.yaml')

class Passwd(XcatBase):
    _schema_loc__ = os.path.join(os.path.dirname(__file__), 'schema/latest/passwd.yaml')
    def validatelayout(self,objdict):
        if type(objdict)==list:
            for item in objdict:
                super(Passwd,self).validatelayout(item)
        else:
            super(Passwd,self).validatelayout(objdict)

class Site(XcatBase):
    _schema_loc__ = os.path.join(os.path.dirname(__file__), 'schema/latest/site.yaml')

class Zone(XcatBase):
    _schema_loc__ = os.path.join(os.path.dirname(__file__), 'schema/latest/zone.yaml')

class Credential(XcatBase):
    _schema_loc__ = os.path.join(os.path.dirname(__file__), 'schema/latest/credential.yaml')

class NetworkConn(XcatBase):
    _schema_loc__ = os.path.join(os.path.dirname(__file__), 'schema/latest/networkconn.yaml')

class ProductKey(XcatBase):
    _schema_loc__ = os.path.join(os.path.dirname(__file__), 'schema/latest/prodkey.yaml')

class Osdistro(XcatBase):
    _schema_loc__ = os.path.join(os.path.dirname(__file__), 'schema/latest/osdistro.yaml')


