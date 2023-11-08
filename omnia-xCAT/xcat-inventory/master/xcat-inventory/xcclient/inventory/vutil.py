#!/usr/bin/python2
###############################################################################
# IBM(c) 2007 EPL license http://www.eclipse.org/legal/epl-v10.html
###############################################################################
# -*- coding: utf-8 -*-
# helper functions for schema validation
#

from __future__ import print_function
import os
import re
from distutils.version import LooseVersion, StrictVersion

from . import globalvars

def isIPaddr(varin):
    ValidIpAddressRegex = "^([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.(([0-9]|[0-9]{2}|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){2}([0-9]|[0-9]{2}|0[0-9]{2}|1[0-9]{2}|2[0-4][0-9]|25[0-5])$";
    return (re.match(ValidIpAddressRegex,str(varin)) is not None)

def isMac(varin):
    MacRegex=r'[0-9a-f]{2}([:])[0-9a-f]{2}(\1[0-9a-f]{2}){4}$'
    return (re.match(MacRegex,str(varin),re.IGNORECASE) is not None)

def isPort(varin):
    PortRegex=r'^(swp)*[0-9]+$'
    return (re.match(PortRegex,str(varin),re.IGNORECASE) is not None)

def isRegex(varin):
    RegexPattern=r'.*\|(,|$)'
    return (re.match(RegexPattern,str(varin)) is not None)

def isIPrange(varin):
    ip=[]
    ip=str(varin).split('-')
    return len(ip)==2 and isIPaddr(ip[0]) and isIPaddr(ip[1])

def isMacHosts(varin):
    machosts=[]
    machosts=str(varin).split('|') 
    for machost in machosts:
        entry=[]
        entry=machost.split('!') 
        if not isMac(entry[0]):
           return False
    return True 

def isNicips(varin):
    nicips=[] 
    nicips=str(varin).split(',')
    for nicip in nicips:
        entry=[]
        entry=nicip.split('!')
        if len(entry)>2:
            return False
        ips=[]
        if len(entry) == 2:
            if isRegex(entry[1]):
                continue
            ips=entry[1].split('|')
        for ip in ips:
            if not isIPaddr(ip) or isRegex(ip):
                return False
    return True   

def underpath(filename,path):
    if re.match(r'^'+os.path.realpath(path)+r'\/',os.path.realpath(filename)):
        return True
    else:
        return False


# return a list of the files in list "infilelist" and the files included in them
def getfileanddeplist(infilelist,rootdir=None):
    #helper function to return a dict whose keys are file "filename" specified and files included by it 
    def getincfiledict(filename,filedict={},rootdir=None):
        regex_include=r'^#INCLUDE:\s*([^#]+)#$'
        if filename in filedict.keys():
            return
        if rootdir and underpath(filename,rootdir):
            filedict[os.path.join(os.sep,os.path.relpath(filename,rootdir))]=1
        else:
            filedict[filename]=1
        filepath=filename
        if rootdir and os.path.isabs(filename) and not underpath(filename,rootdir):
            filepath=os.path.join(rootdir,os.path.relpath(filename,os.sep))
        if os.path.isfile(filepath):
            with open(filepath) as fileobj:
                filelines = fileobj.readlines()
            olddir=os.getcwd()
            curdir=os.path.dirname(filepath)
            os.chdir(curdir)
            for line in filelines:
                matchobj_include=re.search(regex_include,line.strip()) 
                if matchobj_include:
                    incfile=matchobj_include.group(1).strip()
                    incfile=os.path.realpath(incfile)
                    if incfile not in filedict.keys():
                        getincfiledict(incfile,filedict,rootdir)
            os.chdir(olddir)
        return 

    filedict={}

    #in case the input is some ancient inventory format, such as a list of files delimited with COMMA(,) 
    if type(infilelist) is not list:
        infilelist=infilelist.split(',')    

    for filename in infilelist:
        getincfiledict(filename,filedict,rootdir)
    return filedict.keys()

def strsubst(string,subdict={}):
    for k in subdict.keys():
        if k:
            string=string.replace(k,subdict[k])
    return string

def xcatversion():
    return LooseVersion(globalvars.xcat_verno)    


if __name__ == "__main__":
    pass
    


