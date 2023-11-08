#!/usr/bin/python2
# IBM(c) 2007 EPL license http://www.eclipse.org/legal/epl-v10.html
from __future__ import print_function
import os
import shutil
import re
import pickle
import hashlib

from six.moves import configparser
from .exceptions import *
from . import manager
from . import utils

try:
    import sh
except:
    raise InternalException("cannot find module \"sh\", please install it with \"pip install sh\" or \"yum install python2-sh\" from rhels epel repository")


class Invbackend(object):

    globalcfgpath="/etc/xcat/inventory.cfg"
    bkendcfg={}

    def __init__(self,skip=0): 
        if not skip:
            try:
                self.loadcfg()
                self._change_dir(self.bkendcfg['InfraRepo']['local_repo'])
                if self.__querycfgsig()!=self.__calcfgsig():
                    raise BackendNotInitException('Backend not initialized, please initialize the backend with \'xcat-inventory init\'')
            except:
                raise BackendNotInitException('Backend not initialized, please initialize the backend with \'xcat-inventory init\'') 

    def loadcfg(self,cfgpath=None):
        if cfgpath is None:
            myhome=utils.gethome()
            cfgpath=os.path.join(myhome, '.xcatinv/inventory.cfg') 
        if not myhome or not os.path.isfile(cfgpath):
            cfgpath=self.globalcfgpath 

        if not os.path.exists(cfgpath):
            raise InvalidFileException("The configuration file %s does not exist!\n"%(cfgpath))    

        configP = configparser.ConfigParser()
        configP.read(cfgpath)
        #if not config:
        #    raise ParseException("Unable to parse configuration file %s"%(cfgpath))
        if 'backend' not in configP.sections():
            raise ParseException("%s: expected section \"[%s]\" not found! "%(cfgpath,'backend')) 
        if 'InfraRepo' not in configP.sections():
            raise ParseException("%s: expected section \"[%s]\" not found! "%(cfgpath,'InfraRepo')) 

        config = dict(configP.items('backend'))

        if 'type' in config.keys():
            self.bkendcfg['type']=utils.stripquotes(config['type'])
        else:
            self.bkendcfg['type']='git'

        if 'workspace' in config.keys():
            self.bkendcfg['workspace']=utils.stripquotes(config['workspace'])
        else:
            self.bkendcfg['workspace']=''

        if 'user' in config.keys():
            self.bkendcfg['user']=utils.stripquotes(config['user'])
        else:
            self.bkendcfg['user']="xcat"

        if 'email' in config.keys():
            self.bkendcfg['email']=utils.stripquotes(config['email'])
        else: 
            self.bkendcfg['email']="xcat@xcat.org"

        self.bkendcfg['InfraRepo']={}

        config = dict(configP.items('InfraRepo'))
        if 'remote_repo' in config.keys(): 
            self.bkendcfg['InfraRepo']['remote_repo']=utils.stripquotes(config['remote_repo'])
        else:
            self.bkendcfg['InfraRepo']['remote_repo']=""

        if 'local_repo' in config.keys(): 
            self.bkendcfg['InfraRepo']['local_repo']=utils.stripquotes(config['local_repo'])
        else:
            self.bkendcfg['InfraRepo']['local_repo']=utils.gethome()

        if 'working_dir' in config.keys(): 
            self.bkendcfg['InfraRepo']['working_dir']=utils.stripquotes(config['working_dir'])
        else:
            self.bkendcfg['InfraRepo']['working_dir']='.'
             


    def __initcfgfile(self):
        myhome=utils.gethome()
        cfgpath=myhome+'/.xcatinv/inventory.cfg'
        if not os.path.exists(cfgpath):
            if not os.path.exists(self.globalcfgpath):
                raise FileNotExistException('File "%s" does not exist, please check ...' % self.globalcfgpath) 
            os.makedirs(myhome+'/.xcatinv')
            shutil.copyfile(self.globalcfgpath, cfgpath)   
            print("local configuration file \"%s\" created, you can customize it"%(cfgpath))

    def init(self,cfgpath=None): 
        self.__initcfgfile()        
        self.loadcfg(cfgpath)
        isgitrepo=0
        if os.path.isdir(self.bkendcfg['InfraRepo']['local_repo']):
            self._change_dir(self.bkendcfg['InfraRepo']['local_repo'])
            try:
                sh.git('rev-parse','--git-dir')    
            except  sh.ErrorReturnCode as e:
                print("%s is not a git repo dir, removing..."%(self.bkendcfg['InfraRepo']['local_repo']))
                shutil.rmtree(self.bkendcfg['InfraRepo']['local_repo'])
            else:
                isgitrepo=1
        else:
            os.makedirs(self.bkendcfg['InfraRepo']['local_repo'])
            self._change_dir(self.bkendcfg['InfraRepo']['local_repo'])

        if not isgitrepo:
            if self.bkendcfg['InfraRepo']['remote_repo']:
                print("cloning remote repo %s to %s ..."%(self.bkendcfg['InfraRepo']['remote_repo'],self.bkendcfg['InfraRepo']['local_repo']))
                try:
                    sh.git.clone(self.bkendcfg['InfraRepo']['remote_repo'],self.bkendcfg['InfraRepo']['local_repo'])
                except sh.ErrorReturnCode as e:
                    raise ShErrorReturnException(self._deal_with_shErr(e.stderr))
            else:
                try:
                    sh.git.init()
                except sh.ErrorReturnCode as e:
                    raise ShErrorReturnException(self._deal_with_shErr(e.stderr))            

        sig=self.__calcfgsig()
        mysig=self.__querycfgsig()
        if sig==mysig:
            print("Backend has already been initialized, do nothing....")
            return

        print("configuring backend dir \"%s\"...."%(self.bkendcfg['InfraRepo']['local_repo']))
        sh.git.config('--local','user.name',self.bkendcfg['user'])
        sh.git.config('--local','user.email',self.bkendcfg['email'])
        sh.git.config('--local','diff.tool','invdiff')
        sh.git.config('--local','difftool.invdiff.cmd','xcat-inventory diff --filename $MERGED --files $LOCAL $REMOTE')
        if self.bkendcfg['InfraRepo']['remote_repo']:
            output=sh.git.remote('-v',_tty_out=False)
            gitremotes={}
            for line in output.split("\n"):
                matches=re.findall(r'^(\S+)\s+(\S+)*\s+\((\S+)\)$',line)
                if matches:
                    if matches[0][0] not in gitremotes.keys():
                        gitremotes[matches[0][0]]={}
                    gitremotes[matches[0][0]].update({matches[0][2]:matches[0][1]})
            if gitremotes and 'origin' in gitremotes.keys():
                if gitremotes['origin']['fetch']!=self.bkendcfg['InfraRepo']['remote_repo'] or gitremotes['origin']['push']!=self.bkendcfg['InfraRepo']['remote_repo']:
                    sh.git.remote('remove','origin')
                    del gitremotes['origin']
              
            if 'origin' not in gitremotes.keys():
                sh.git.remote('add','origin',self.bkendcfg['InfraRepo']['remote_repo'])
        else:
            try:
                sh.git.remote("remove",'origin')
            except:
                pass            

        if self.bkendcfg['InfraRepo']['working_dir'] and self.bkendcfg['InfraRepo']['working_dir']!='.' and not os.path.isdir(self.bkendcfg['InfraRepo']['working_dir']):
            os.makedirs(self.bkendcfg['InfraRepo']['working_dir'])

        if self.bkendcfg['workspace'] and self.bkendcfg['workspace'] not in self.__getbranchlist():
            print("creating workspace %s ..."%(self.bkendcfg['workspace']))
            try:
                sh.git.checkout('-b',self.bkendcfg['workspace'])
                sh.git.commit('--allow-empty','-m "initial commit"')
                if self.bkendcfg['InfraRepo']['working_dir']:            
                    self._change_dir(self.bkendcfg['InfraRepo']['working_dir'])
            #    sh.git.pull('origin',self.bkendcfg['workspace'],'--tags')
            except sh.ErrorReturnCode as e:
                raise ShErrorReturnException(self._deal_with_shErr(e.stderr))
        self.__setcfgsig(sig) 
        print("xcat-inventory backend initialized. Please run \"xcat-inventory checkout\" to refresh xCAT DB")

    def __calcfgsig(self):
        cfgbin=pickle.dumps(self.bkendcfg)
        cfgsig=hashlib.md5(cfgbin).hexdigest()
        return cfgsig
        
    def __querycfgsig(self):
        try:
            out=sh.git.config('--local','--get','xcatinv.signature',_tty_out=False).strip()
        except sh.ErrorReturnCode as e:
            out=""
        return out 

    def __setcfgsig(self,sig):
        try:
            sh.git.config('--local','--add','xcatinv.signature',sig)
        except sh.ErrorReturnCode as e:
            pass

        

    def __getstash(self):
        brstash={}
        out=sh.git.stash('list',_tty_out=False).strip()
        lines=out.split("\n")
        for line in lines:
            ment=re.findall(r'(\S+):[^:]+\s+(\S+):.+',line)
            if ment:
                if ment[0][1] not in brstash.keys():
                    brstash[ment[0][1]]=[ment[0][0]] 
                else:
                    brstash[ment[0][1]].append(ment[0][0])
        return brstash
                    
    def __getbranch(self):
        try:
            line=sh.git('symbolic-ref','-q','--short', 'HEAD')
        except sh.ErrorReturnCode as e:
            raise ShErrorReturnException(self._deal_with_shErr(e.stderr))
        
        curworkspace=line.strip()
        return curworkspace

    def __isuncached(self):
        pass

    def __istempbranch(self,branch):
        return re.match(r'\S+@\S+',branch)

    def __iswkspacenamevalid(self,branch):
        return self._validatebrname(branch)

    #return a list of (branch,commit) from branch name "commit@branch"
    def __parsetempbranch(self,rawbranch):
        commit=None
        branch=None
        ment=re.findall(r'(\S+)@(\S+)',rawbranch)
        if ment:
            commit=ment[0][0]
            branch=ment[0][1]
        return (branch,commit)

    def _deal_with_shErr(self, err):
        if 'fatal' in err:
            return 'Error: %s' % re.findall(r"fatal: (.+?)\n", err)[0] 
        if 'error' in err:
            errors = re.findall(r"error: (.+?)\n", err)
            err_string = ['Error: ' + error for error in errors]
            return '\n' . join(err_string)

    def _change_dir(self, target_dir):
        if not target_dir:
            return
        if not os.path.isdir(target_dir):
            raise DirNotExistException('Directory "%s" does not exist, please check...' % target_dir)
        os.chdir(target_dir)

    def _validatebrname(self,brname):
        if brname and re.match(r'[^@^#]*(@|#)[^@^#]*',brname):
            return False
        else:
           return True

    #get all branches
    def __getbranchlist(self):
        branches=[]
        try:
            lines=sh.git.branch(_tty_out=False).strip()
        except sh.ErrorReturnCode as e:
            raise ShErrorReturnException(self._deal_with_shErr(e.stderr))
        if lines:
            rawbranches=lines.split('\n')        
            branches=[branch.lstrip('*').strip() for branch in rawbranches if not self.__istempbranch(branch.lstrip('*').strip())]

        return branches
            

    def workspace_list(self):
        self.loadcfg()
        self._change_dir(self.bkendcfg['InfraRepo']['local_repo'])
        branches=self.__getbranchlist()
        curbranch=self.__getbranch()
        outlines=[]
        for branch in branches:
            if branch == curbranch:
                outlines.append("* %s"%(branch))
            else:
                outlines.append(branch)
        if outlines:
            print('\n' . join(outlines))
        else:
            print('No workspace found')

    def workspace_new(self,newbranch):
        self.loadcfg()
        self._change_dir(self.bkendcfg['InfraRepo']['local_repo'])
        if not self.__iswkspacenamevalid(newbranch):
            raise InvalidValueException("invalid character \"@\" or \"#\" found in workspace name %s"%(newbranch))

        curbranch=self.__getbranch()
        if self.__istempbranch(curbranch):
            (branch,commit)=self.__parsetempbranch(curbranch)           
            sh.git.checkout(branch)
            sh.git.branch("-D",curbranch)
        if newbranch != curbranch:
            try:
                sh.git.checkout('-b',newbranch)
            except sh.ErrorReturnCode as e:
                raise ShErrorReturnException(self._deal_with_shErr(e.stderr))
        print("workspace %s created!"%(newbranch))

    def workspace_delete(self,branch):
        self.loadcfg()
        self._change_dir(self.bkendcfg['InfraRepo']['local_repo'])
        if not self.__iswkspacenamevalid(branch):
            raise InvalidValueException("invalid character \"@\" or \"#\" found in workspace name %s"%(branch))

        try:
            revlist=self.__getallrev(branch)
            if revlist:
                revlist=["%s#%s"%(rev,branch) for rev in revlist]
                sh.git.tag('-d',' '.join(revlist))
            sh.git.checkout('master')
            sh.git.branch('-D',branch)
            print("deleted workspace %s"%(branch))
        except sh.ErrorReturnCode as e:
            raise ShErrorReturnException(self._deal_with_shErr(e.stderr))

    def workspace_checkout(self,newbranch):
        self.loadcfg()
        self._change_dir(self.bkendcfg['InfraRepo']['local_repo'])
        if not self.__iswkspacenamevalid(newbranch):
            raise InvalidValueException("invalid character \"@\" or \"#\" found in workspace name %s"%(newbranch))

        curworkspace=self.__getbranch()
        if curworkspace!=newbranch:
            sh.git.stash('save')
        if self.__istempbranch(curworkspace):
            (branch,commit)=self.__parsetempbranch(curworkspace)
            sh.git.checkout(branch)
            sh.git.branch("-D",curworkspace)
             
        try:
            sh.git.checkout(newbranch)
        except sh.ErrorReturnCode as e:
            raise ShErrorReturnException(self._deal_with_shErr(e.stderr))

        #restore the uncommited and unstashed stuff in workspace on switching
        while True:
            stashdict=self.__getstash()
            if curworkspace!=newbranch and newbranch in stashdict.keys() :
                stashlist=stashdict[newbranch]
                sh.git.stash('pop',stashlist[0])
            else:
                break

        self.checkout(revision=None,doimport=True)
        print("switched to workspace %s"%(newbranch))

    # return (revision,branch) from "tag#branch"
    def __parsetag(self,tagname):
        itemmatched=re.findall(r'^([^#]+)#([^#]+)$',tagname)
        if itemmatched:
            return itemmatched[0]
        else:
            return (None,None)

    def __tag2rev(self,branch,tagname):
        itemmatched=re.findall(r'^([^#]+)#%s$'%(branch),tagname)
        if itemmatched:
            return itemmatched[0]       
        else:
            return None  

    def __getallrev(self,branch):
        tags=sh.git.tag('-l',_tty_out=False).strip()
        if tags:
            rawtaglist=tags.split('\n') 
            revlist=[]
            for rev in rawtaglist:
                myrev=self.__tag2rev(branch,rev)
                if myrev is not None:
                    revlist.append(myrev)
            return revlist
        return None

    def __getcurrev(self,branch):
        try:
            rawtag=sh.git.describe('--candidates','0').strip()
        except:
            return None
        rev=self.__tag2rev(branch,rawtag)
        return rev

    def __getcurcommit(self):
        try:
            rawcommit=sh.git("rev-parse",'--short=7','HEAD').strip()
        except:
            return '.'
        return rawcommit  
      

    def rev_list(self,revision):
        self.loadcfg()
        self._change_dir(self.bkendcfg['InfraRepo']['local_repo'])
        curworkspace=self.__getbranch()
        if self.__istempbranch(curworkspace):
            (branch,commit)=self.__parsetempbranch(curworkspace)
            curworkspace=branch
        try:
            if revision is None:
                    revlist=self.__getallrev(curworkspace)
                    if revlist:
                        print('\n' . join(revlist))
                    else:
                        print('No revision found in current workspace')
            else:
                if not self._validatebrname(revision):
                    raise InvalidValueException("invalid character \"@\" or \"#\" found in revision name %s"%(revision))

                revision=sh.git.show("%s#%s"%(revision,curworkspace),_tty_out=False)
                print(revision)
        except sh.ErrorReturnCode as e:
            raise ShErrorReturnException(self._deal_with_shErr(e.stderr))
       
    def diff(self):
        self.loadcfg()
        self._change_dir(self.bkendcfg['InfraRepo']['local_repo'] + '/' + self.bkendcfg['InfraRepo']['working_dir'])
        curworkspace=self.__getbranch()
        try:
            sh.git.stash('save','--all')
        except:
            pass
        if self.__istempbranch(curworkspace):
            (branch,tag)=self.__parsetempbranch(curworkspace)
        else:
            branch=curworkspace
        curcommit=self.__getcurcommit()
        newbrname="%s@%s"%(curcommit,branch) 
        
        try:
            sh.git.checkout('-b',newbrname)
        except sh.ErrorReturnCode as e:
            raise ShErrorReturnException(self._deal_with_shErr(e.stderr))
 
        print("exporting inventory data from xCAT DB...")
        devNull = open(os.devnull, 'w')
        with utils.stdout_redirector(devNull),utils.stderr_redirector(devNull):
            manager.export_by_type(None,None,None,'.',fmt='yaml',version=None,exclude=['credential'])
        print("generating diff report...") 
        try:
            sh.git.add("./*")
            sh.git.commit("-a","-m","temp commit for diff").strip()
        except:
            pass
        try:
            diffout=sh.git.difftool('-y',curcommit,"HEAD",_tty_out=False,_tty_in=True) 
            sh.git.reset('--hard',curcommit)
            sh.git.checkout(curworkspace)
        except sh.ErrorReturnCode as e:
            sh.git.branch("-D",newbrname)
            raise ShErrorReturnException(self._deal_with_shErr(e.stderr))
        print(diffout)

        #restore the uncommited and unstashed stuff in workspace on switching
        while True:
            stashdict=self.__getstash()
            if curworkspace in stashdict.keys() :
                stashlist=stashdict[curworkspace]
                sh.git.stash('pop',stashlist[0])
            else:
                break

        sh.git.branch("-D",newbrname)


        

    def pull(self):
        self.loadcfg()
        self._change_dir(self.bkendcfg['InfraRepo']['local_repo'])
        remoterepourl=self.__getremoteurl()
        if not remoterepourl:
            raise BackendNotInitException("[remote_repo] is not configured in backend, please make sure it is specified in config file and backend is initialized")
        curworkspace=self.__getbranch()
        if self.__istempbranch(curworkspace):
            (branch,commit)=self.__parsetempbranch(curworkspace)
            raise InvalidValueException("you are on the %s revision of %s workspace, cannot sync with remote repo"%(commit,branch))
        print("syncing workspace %s from remote repo"%(curworkspace))
        try:
            sh.git.stash('save')
            sh.git.stash('pop')
        except:
            pass

        try:
            sh.git.pull('origin',curworkspace,'--tags')
        except sh.ErrorReturnCode as e:
            raise ShErrorReturnException(self._deal_with_shErr(e.stderr))

    def __getremoteurl(self):
        remote_repo_url=""
        try:
            remote_repo_url=sh.git("ls-remote","--get-url").strip()
        except sh.ErrorReturnCode as e:
            pass
        return remote_repo_url

   
    def radar(self):
        self.loadcfg()
        self._change_dir(self.bkendcfg['InfraRepo']['local_repo'])
        remote_repo_url=""
        remote_repo_url=self.__getremoteurl()
        if not remote_repo_url:
            raise BackendNotInitException("[remote_repo] is not configured in backend, please make sure it is specified in config file and backend is initialized")
        curworkspace=self.__getbranch()

        branches=[]
        tags=[]
        brrevdict={}

        if not remote_repo_url:
            if not self.bkendcfg['InfraRepo']['remote_repo']:
                print("remote_repo not configured in inventory configuration file \"~/.xcatinv/inventory.cfg\", please configure it and run \"xcat-inventory init\" to reinitialize xcat-inventory backend")
                return
            else:
                print("please run \"xcat-inventory init\" to reinitialize xcat-inventory backend")
                return
        print("remote_repo_url: %s"%(remote_repo_url))
       
        try: 
            rawoutput=sh.git("ls-remote", "--refs", "--heads").strip()
        except sh.ErrorReturnCode as e:
            raise ShErrorReturnException(self._deal_with_shErr(e.stderr))
        matched=re.findall(r'refs/heads/(\S+)',rawoutput)
        if matched:
            branches=matched
        print("remote workspaces:\n-"+'\n-'.join(branches))
        try:
            rawoutput=sh.git("ls-remote", "--refs", "--tags").strip()
        except sh.ErrorReturnCode as e:
            raise ShErrorReturnException(self._deal_with_shErr(e.stderr))
        matched=re.findall(r'refs/tags/(\S+)',rawoutput)
        if matched:
            tags=matched
        for tag in tags:
            (rev,branch)=self.__parsetag(tag)
            if branch is None or rev is None:
                continue
            if branch not in brrevdict.keys():
                brrevdict[branch]=[]
            brrevdict[branch].append(rev)
        for branch in brrevdict.keys(): 
            if brrevdict[branch]:
                print("remote revisions on remote workspace "+branch+': \n-'+'\n-'.join(brrevdict[branch]))
        print("Hints:")
        print("1.if you want to checkout to a remote workspace <w>, please first create a local workspace with same name with \"xcat-inventory workspace-new <w>\" and then sync the remote repo to local with \"xcat-inventory pull\", then checkout to it with \"xcat-inventory checkout\"")
        print("2.if you want to checkout to a remote revision <r> on workspace <w>, please first checkout to local workspace <w> with \"xatt-inventory workspace-checkout <w>\", then sync the remote repo with \"xcat-inventory pull\", then checkout to it with \"xcat-inventory checkout <r>\"")
         

    def refresh(self):
        self.loadcfg()
        self._change_dir(self.bkendcfg['InfraRepo']['local_repo'])
        curworkspace=self.__getbranch()
        try:
            sh.git.stash('save','--include-untracked')
            stashdict=self.__getstash()
            while curworkspace in stashdict.keys() and stashdict[curworkspace]:
                sh.git.stash('drop',stashdict[curworkspace][0])        
                stashdict=self.__getstash()
        except sh.ErrorReturnCode as e:
            raise ShErrorReturnException(self._deal_with_shErr(e.stderr))                
    
    def push(self):
        self.loadcfg()
        self._change_dir(self.bkendcfg['InfraRepo']['local_repo'])
        remoterepourl=self.__getremoteurl()
        if not remoterepourl:
            raise BackendNotInitException("[remote_repo] is not configured in backend, please make sure it is specified in config file and backend is initialized")
        curworkspace=self.__getbranch()
        if self.__istempbranch(curworkspace):
            (branch,commit)=self.__parsetempbranch(curworkspace)
            raise InvalidValueException("you are on the %s revision of %s workspace, cannot sync with remote repo"%(commit,branch))
        print("pushing workspace %s to remote repo ..."%(curworkspace))
        try:
            sh.git.push('origin',curworkspace,'--tags')        
        except sh.ErrorReturnCode as e:
            raise ShErrorReturnException(self._deal_with_shErr(e.stderr))

    def drop(self):
        pass
        self.loadcfg()
        self._change_dir(self.bkendcfg['InfraRepo']['local_repo'])
        curworkspace=self.__getbranch()
        sh.git.reset()
        sh.git.checkout('.')
        sh.git.clean('-fdx')
        print("dropped the uncommited changes in workspace %s"%(curworkspace))
        stashdict=self.__getstash()
        while curworkspace in stashdict.keys() and stashdict[curworkspace]:
            sh.git.stash('drop',stashdict[curworkspace][0])        
            stashdict=self.__getstash()
       

    def commit(self,revision,description):
        self.loadcfg()
        self._change_dir(self.bkendcfg['InfraRepo']['local_repo'] + '/' + self.bkendcfg['InfraRepo']['working_dir'])
        curworkspace=self.__getbranch()
        if self.__istempbranch(curworkspace):
            (branch,commit)=self.__parsetempbranch(curworkspace)
            raise InvalidValueException("you are on the %s revision of %s workspace, please run \"xcat-inventory checkout --no-import\" to switch to the head of workspace"%(commit,branch))

        if not self._validatebrname(revision):
            raise InvalidValueException("invalid character \"@\" or \"#\" found in revision name %s"%(revision))
        print("exporting inventory data from xCAT DB....")
        devNull = open(os.devnull, 'w')
        with utils.stdout_redirector(devNull),utils.stderr_redirector(devNull):
            manager.export_by_type(None,None,None,'.',fmt='yaml',version=None,exclude=['credential'])
        
        if revision:
            print("creating revision %s in workspace %s ..."%(revision,curworkspace))
        else:
            print("commit inventory in workspace %s ..."%(curworkspace))

        sh.git.add('./*')
        try:
            sh.git.commit('-a','-m',description)
        except sh.ErrorReturnCode as e:
            if e.stderr:
                raise ShErrorReturnException(self._deal_with_shErr(e.stderr))
            if e.stdout:
                raise ShErrorReturnException(' ' . join(e.stdout.split('\n')))

        if revision:
            try:
                revname="%s#%s"%(revision,curworkspace)
                sh.git.tag('-a',revname,'-m',description)
            except sh.ErrorReturnCode as e:
                if e.stderr:
                    raise ShErrorReturnException(self._deal_with_shErr(e.stderr))
    
    def whereami(self):
        self.loadcfg()
        self._change_dir(self.bkendcfg['InfraRepo']['local_repo'])    
        curbranch=self.__getbranch()
        if self.__istempbranch(curbranch) :
            (branch,commit)=self.__parsetempbranch(curbranch)
            print("you are in revision \"%s\" of workspace \"%s\""%(commit,branch)) 
        else:
            branch=curbranch
            commit=self.__getcurrev(branch)
            print("you are in workspace \"%s\""%(branch))


    def checkout(self,revision=None,doimport=True):  
        self.loadcfg()
        self._change_dir(self.bkendcfg['InfraRepo']['local_repo'])
        self._change_dir(self.bkendcfg['InfraRepo']['working_dir'])
        curbranch=self.__getbranch()
        
        if not self._validatebrname(revision):
            raise InvalidValueException("invalid character \"@\" or \"#\" found in revision name %s"%(revision))

        if self.__istempbranch(curbranch) :
            (branch,commit)=self.__parsetempbranch(curbranch)
            if commit == revision:
                print("already on revision %s"%(revision)) 
                return 0
            else:
                sh.git.checkout(branch)
                sh.git.branch('-D',curbranch)
                curbranch=branch


        revlist=self.__getallrev(curbranch)
        if revision:
            if not revlist or revision not in revlist:
                raise InvalidValueException("revision %s not found in workspace %s"%(revision,curbranch))
 
        if revision is None:
            pass
        else:
            brname=revision+'@'+curbranch 
            try:
                sh.git.checkout('-b',brname,"%s#%s"%(revision,curbranch))
            except sh.ErrorReturnCode as e:
                raise ShErrorReturnException(self._deal_with_shErr(e.stderr))
            

        if doimport:
            print("importing inventory data to xCAT DB...")
            devNull = open(os.devnull, 'w')
            with utils.stdout_redirector(devNull),utils.stderr_redirector(devNull):
                manager.importobj(None,".",None,None,None,None,False,None,None,exclude=['credential'])

        if revision is None:
            print("checked out to latest revision")
        else:
            print("checked out to revision %s"%(revision)) 
      
