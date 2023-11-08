#!/usr/bin/env python
###############################################################################
# IBM(c) 2018 EPL license http://www.eclipse.org/legal/epl-v10.html
###############################################################################
#   
#  NAME:  xcatha.py
#
#  SYNTAX: xcatha.py -s|--setup -p <shared-data directory path> -i <nic> -v <virtual ip> -n <virtual ip hostname> [-m <netmask>] [-t <database type>] [--dryrun] 
#
#  SYNTAX: xcatha.py -a|--activate -p <shared-data directory path> -i <nic> -v <virtual ip> [-m <netmask>] [-t <database type>] [--dryrun]
#
#  SYNTAX: xcatha.py -d|--deactivate -i <nic> -v <virtual ip> [--dryrun]
#
#  DESCRIPTION:  Setup/Activate/Deactivate this node be the shared data based xCAT MN
#
#  FLAGS:
#               -p       the shared data directory path
#               -i       the nic that the virtual ip address attaches to,
#                        for Linux, it could be eth0:1 or eth1:2 or ...
#               -v       virtual ip address
#               -n       virtual ip hostname
#               -m       netmask for the virtual ip address,
#                        default is 255.255.255.0
#               -t       target database type, it can be postgresql, mariadb or sqlite, default is sqlite
#               --dryrun display steps without execution
import argparse
import os
import time
import platform
import shutil
import logging
from subprocess import Popen, PIPE
import pwd
import grp
import socket
import pdb
import re

etc_hosts="/etc/hosts"
dryrun=0
xcat_url="https://raw.githubusercontent.com/xcat2/xcat-core/master/xCAT-server/share/xcat/tools/go-xcat"
# Directories below will be linked to shared location specified by "-p" flag during setup and activation.
#     they will also be unlinked during deactivation. If any of these directories are already on shared
#     disk, remove then from shared_fs list
shared_fs=['/install','/etc/xcat','/root/.xcat','/var/lib/pgsql','/var/lib/mysql','/tftpboot']
xcat_cfgloc="/etc/xcat/cfgloc"
xcat_install="/tmp/go-xcat --yes install"
xcatdb_password={'XCATPGPW':'cluster','XCATMYSQLADMIN_PW':'cluster','XCATMYSQLROOT_PW':'cluster'}
setup_process_msg=""
service_list=['postgresql','mariadb','xcatd','named','dhcpd','ntpd','conserver','goconserver']
xcat_profile="/etc/profile.d/xcat.sh"
pg_hba_conf="/var/lib/pgsql/data/pg_hba.conf"
postgresql_conf="/var/lib/pgsql/data/postgresql.conf"
hostfile="/etc/hosts"
xcat_env="/opt/xcat/bin:/opt/xcat/sbin:/opt/xcat/share/xcat/tools:"

#configure logger
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%m/%d/%Y %H:%M:%S %p"
logging.basicConfig(filename = os.path.join(os.getcwd(), 'xcatha.log'), level = logging.DEBUG, filemode = 'a', format = LOG_FORMAT, datefmt=DATE_FORMAT)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
logger = logging.getLogger('xCAT-HA')
logger.addHandler(console_handler)

# User input strings
user_input_yn  = "Continue? [[Y]es/[N]o]:"
user_input_ynd = "Continue? [[Y]es/[N]o/[D]ryrun]:"

def run_command(cmd, retry, ignore_fail=None):
    """execute and retry execute command"""
    global dryrun
    if dryrun:
        loginfo=cmd+" [Dryrun]"
        logger.debug(loginfo)
        return 0
    a=0
    while True:
        res=os.system(cmd)
        if res is 0:
            loginfo=cmd+" [Passed]"
            logger.debug(loginfo)
            return 0
        else:
            # Command failed, but do we care ?
            if ignore_fail:
                loginfo=cmd+" [Failed, OK to ignore]"
                logger.debug(loginfo)
                return 0
            if retry is 0:
                loginfo=cmd+" [Failed]"
                logger.error(loginfo)
                return 1
            a += 1
            if a < retry:
                time.sleep(3)
                loginfo="Retry "+bytes(a)+" ... ..."+cmd
                logger.debug(loginfo)
            if a==3:
                loginfo=cmd+" [Failed]"
                logger.error(loginfo)
                return 1

class HaException(Exception):
    """customize exception"""
    def __init__(self,message):
        Exception.__init__(self)
        self.message=message

class xcat_ha_utils:
    """"""
    def log_info(self, message):
        """print format"""
        print "============================================================================================"
        logger.info(message)

    def vip_check(self, vip):
        """check if virtual ip can ping"""
        global setup_process_msg
        global dryrun
        setup_process_msg="===> Check virtual ip stage <==="
        logger.info(setup_process_msg)
        cmd="ping -c 1 -w 10 "+vip
        if dryrun:
            logger.debug(cmd + " [Dryrun]")
            return
        logger.debug(cmd)
        res=os.system(cmd)
        if res is 0:
            message="Aborted startup as virtual ip appears to be already active."
            logger.error(message)
            raise HaException(setup_process_msg)    
        else:
            message="virtual ip can be used."
            logger.info(message)

    def stop_service(self, serviceName):
        """Stop specified service"""
        cmd="systemctl stop "+serviceName
        return_code=run_command(cmd, 3)
        return return_code

    def start_service(self, serviceName):
        """Start specified service"""
        cmd="systemctl start "+serviceName
        return_code=run_command(cmd,3)
        return return_code

    def restart_service(self, serviceName):
        """restart specified service"""
        cmd="systemctl restart "+serviceName
        return_code=run_command(cmd,3)
        return return_code

    def disable_service(self, serviceName):
        """Disable specified service from starting on reboot"""
        cmd="systemctl disable "+serviceName
        return_code=run_command(cmd, 3)
        return return_code

    def start_all_services(self, servicelist, dbtype, host_name):
        """start all services"""
        global setup_process_msg
        global etc_hosts
        setup_process_msg="===> Start all services stage <==="
        logger.info(setup_process_msg)
        if dbtype == 'mariadb' and 'postgresql' in servicelist:
            servicelist.remove('postgresql')
        elif dbtype == 'postgresql' and 'mariadb' in servicelist:
            servicelist.remove('mariadb')
        elif dbtype == 'sqlite':
            if 'postgresql' in servicelist:
                servicelist.remove('postgresql')
            if 'mariadb' in servicelist:
                servicelist.remove('mariadb')
        process_file="/etc/xcat/console.lock"
        if os.path.exists(process_file):
            with open(process_file,'rt') as handle:
                for ln in handle:
                    if 'goconserver' in ln:
                        servicelist.remove('conserver')
                        break
                    else:
                        servicelist.remove('goconserver')
                        break
        else:
            servicelist.remove('conserver')
            servicelist.remove('goconserver')
        return_code=0
        xcat_status=1
        domain_in_site=0
        for value in servicelist:
            if xcat_status is 0:
                if value == 'conserver':
                    if run_command("makeconservercf", 0):
                        return_code=1
                if value == 'goconserver':
                    if run_command("makegocons", 0):
                        return_code=1
                if value == 'named':
                    # The decision to start "named" service is based on "domain" entry in "site" table
                    # "domain" entry     in "site" table AND
                    #      long hostname in "/etc/hosts" => run "makedns -n" which will in turn start "named"
                    # "domain" entry not in "site" table => do not run "makedns -n" and do not start "named"
                    cmd="lsdef -t site -i domain|grep domain"
                    if run_command(cmd,0) is 1:
                        # No domain in the site table, 
                        logger.warning('"domain" entry is not in "site" table. "named" service will not be started')
                    else:
                        # Domain in the site table, 
                        domain_in_site=1
                        host_name=host_name.strip()
                        long_name = self.find_line(etc_hosts, host_name+'.')
                        if long_name is 1:
                            # long hostname in /etc/hosts
                            if run_command("makedns -n", 0):
                                return_code=1
                        else:
                            # long hostname not in /etc/hosts
                            logger.warning('Long hostname is not in "/etc/hosts". "named" service will not be started')
                if value == "dhcpd":
                    if domain_in_site is 0:
                        logger.warning('"domain" entry is not in "site" table. "dhcpd" service will not be started')
                        continue
                    if run_command("makedhcp -n", 0):
                        return_code=1
                    if run_command("makedhcp -a", 0):
                        return_code=1
            if value == "xcatd" or value == "mariadb" or value == "postgresql":
                if self.start_service(value):
                    logger.error("start "+value+" failed") 
                    raise HaException(setup_process_msg)
                else:
                    if value == "xcatd":
                        self.source_xcat_profile()
                        xcat_status=0
               
            else:
                if value == "named" or value == "dhcpd":
                    # Do not start "named" service,
                    # Either it was started by "makedns -n" command above, or
                    # "domain" entry is not in "site" table and we should not run "named"
                    #
                    # Do not start "dhcpd" service,
                    # Either it was started by "makedhcp -a" command above, or
                    # "domain" entry is not in "site" table and we should not run "makedhcp"
                    #
                    continue
                if self.start_service(value):
                    return_code=1
        return return_code

    def stop_all_services(self, servicelist, dbtype):
        """stop all services"""
        if dbtype == 'mariadb' and 'postgresql' in servicelist:
            servicelist.remove('postgresql')
        elif dbtype == 'postgresql' and 'mariadb' in servicelist:
            servicelist.remove('mariadb')
        elif dbtype == 'sqlite':
            if 'postgresql' in servicelist:
                servicelist.remove('postgresql')
            if 'mariadb' in servicelist:
                servicelist.remove('mariadb')
        cmd="ps -ef|grep 'conserver\|goconserver'|grep -v grep"
        output=os.popen(cmd).read()
        if output:
            process="/etc/xcat/console.lock"
            if dryrun:
                logger.debug('Added "%s" to %s [Dryrun]' %(output, process))
            else:
                f=open(process, 'w') 
                f.write(output)
                logger.debug('Added "%s" to %s' %(output, process))
                f.close
        return_code=0
        for value in reversed(servicelist):
            if self.stop_service(value):
                return_code=1
        return return_code

    def disable_all_services(self, servicelist, dbtype):
        """disable all services from starting on reboot"""
        if dbtype == 'mariadb' and 'postgresql' in servicelist:
            servicelist.remove('postgresql')
        elif dbtype == 'postgresql' and 'mariadb' in servicelist:
            servicelist.remove('mariadb')
        elif dbtype == 'sqlite':
            if 'mariadb' in servicelist:
                servicelist.remove('mariadb')
            if 'postgresql' in servicelist:
                servicelist.remove('mariadb')
        return_code=0
        for value in reversed(servicelist):
            if self.disable_service(value):
                return_code=1
        return return_code

    def configure_xcat_attribute(self, host, ip):
        "configure xcat MN attribute"
        logger.info("Configure xCAT management node attribute")
        pass

    def current_database_type(self, path):
        """current data base type"""
        cfgloc=path+xcat_cfgloc
        if os.path.exists(cfgloc):
            with open(cfgloc, 'r') as file:
                cdbtype=file.read(2)
            file.close()
            if cdbtype == 'my':
                current_data_db="mariadb"
            else:
                current_data_db="postgresql"
        else:
            current_data_db="sqlite"
        return current_data_db

    def get_physical_ip(self, nic):
        """get physical IP"""
        main_nic=nic.split(":")[0]
        f=Popen(('ifconfig',main_nic), stdout=PIPE).stdout
        data=[eachLine.strip() for eachLine in f]
        physical_ip=filter(lambda x : 'inet ' in x, data)[0].split(" ")[1]
        return physical_ip 

    def check_database_type(self, dbtype, vip, nic, path):
        """if current xCAT DB type is different from target type, switch DB to target type"""
        global setup_process_msg
        setup_process_msg="===> Check database type stage <==="
        logger.info(setup_process_msg)
        current_dbtype=self.current_database_type("")
        logger.debug("Current xCAT database type: "+current_dbtype)
        logger.debug("Target xCAT database type: "+dbtype)
        target_dbtype=dbtype
        if current_dbtype != target_dbtype:
            physical_ip=self.get_original_ip()
            if physical_ip is "":
                physical_ip=self.get_physical_ip(nic)
            if physical_ip:
                if self.check_xcat_exist_in_shared_data(path):
                    self.install_db_package(dbtype)
                    self.modify_db_configure_file(dbtype, path, physical_ip, vip) 
                else:
                    self.switch_database(dbtype,vip,physical_ip)
                    self.modify_db_configure_file(dbtype, path, physical_ip, vip)
        else:
            logger.debug("No need to switch database")

    def check_xcat_exist_in_shared_data(self, path):
        """check if xCAT data is in shared data directory"""
        global setup_process_msg
        setup_process_msg="Check if xCAT data is in shared data directory"
        logger.info(setup_process_msg)
        xcat_path=path+"/install"
        if os.path.exists(xcat_path):
            logger.debug("There is xCAT data "+xcat_path+" in shared data "+path)
            return 1
        else:
            logger.debug("There is no xCAT data "+xcat_path+" in shared data "+path)
            return 0

    def check_shared_data_db_type(self, tdbtype, path):
        """check if target dbtype is the same with shared data dbtype"""
        global setup_process_msg
        setup_process_msg="===> Check if target dbtype is the same with shared data dbtype stage <==="
        logger.info(setup_process_msg)
        cfgfile=path+xcat_cfgloc
        share_data_db=""
        if os.path.exists(cfgfile):
            with open(cfgfile,'r') as file:
                sdbtype=file.read(2)
            file.close()
            if sdbtype == 'my':
                share_data_db="mariadb"
            elif sdbtype == 'Pg':
                share_data_db="postgresql"
        else:
            share_data_db="sqlite"
        logger.debug("Database type is '"+share_data_db+"' in shared data directory")
        if share_data_db == tdbtype:
            if dryrun:
                logger.debug("Target database type is matched [Dryrun]")
            else:
                logger.debug("Target database type is matched [Passed]")
        else:
            if dryrun:
                logger.error("target database is not matched [Dryrun]")
            else:
                logger.error("target database is not matched [Failed]")
            raise HaException(setup_process_msg)
        
    def switch_database(self, dbtype, vip, physical_ip):
        """switch database to target type"""
        global setup_process_msg
        res=self.install_db_package(dbtype)
        if res is 0:
            setup_process_msg="===> Switch to target database stage <==="
            logger.info(setup_process_msg)
            cmd_msg=""
            for key in xcatdb_password:
                os.environ[key]=xcatdb_password[key]
            if self.check_service_status("xcatd") is not 0:
                if self.restart_service("xcatd"):  
                    raise HaException(setup_process_msg)   
            self.source_xcat_profile()
            if dbtype == "postgresql":
                cmd="pgsqlsetup -i -a "+vip+" -a "+physical_ip
                cmd_msg="export XCATPGPW=xxxxxx;pgsqlsetup -i -a "+vip+" -a "+physical_ip
            elif dbtype == "mariadb":
                if os.path.exists("/tmp/ha_mn"):
                    cmd="cat /tmp/ha_mn|awk '{print $1}'|head -1 >/tmp/physical_ip"
                    os.system(cmd)
                if os.path.exists("/tmp/physical_ip"):
                    cmd="mysqlsetup -i -f /tmp/physical_ip -V"
                    cmd_msg="mysqlsetup -i -f /tmp/physical_ip -V"
                else:
                    logger.error("there is no physical ip file in /tmp/physical_ip")
                    raise HaException(setup_process_msg)    
            else:
                logger.error("Do not support"+dbtype+" [Failed]") 
                raise HaException(setup_process_msg)
            logger.info(cmd_msg)
            res=os.system(cmd)
            if res is 0:
                logger.debug("Switch to "+dbtype+" [Passed]")
            else:
                logger.error("Switch to "+dbtype+" [Failed]")

    def install_db_package(self, dbtype):
        """install database package"""
        global setup_process_msg
        global dryrun
        setup_process_msg="===> Install database package stage <==="
        logger.info(setup_process_msg)
        os_name=platform.platform()
        res=1
        if os_name.__contains__("redhat"):
            if not self.check_software_installed(dbtype):
                logger.debug(dbtype+" already installed")
                return 0    
            if dbtype == "postgresql":  
                db_rpms="postgresql* perl-DBD-Pg"
            elif dbtype == "mariadb":
                db_rpms="perl-DBD-MySQL* mariadb-server-5.* mariadb-5.* mysql-connector-odbc-*"
            else:
                return res
            cmd="yum -y install %s" %db_rpms
            res=run_command(cmd,0)
            if res is not 0:
                logger.error("install %s [Failed]" %db_rpms)
            else:
                if dryrun:
                    logger.info("install %s [Dryrun]" %db_rpms)     
                else:
                    logger.info("install %s [Passed]" %db_rpms)     
        return res

    def install_xcat(self, url):
        """install stable xCAT"""
        global setup_process_msg
        setup_process_msg="===> Install xCAT stage <==="
        logger.info(setup_process_msg)
        if not self.check_software_installed("xCAT"):
            logger.debug("xCAT already installed")
            return 0
        cmd="wget "+url+" -O - >/tmp/go-xcat"
        res=run_command(cmd,0)
        if res is 0:
            cmd="chmod +x /tmp/go-xcat"
            res=run_command(cmd,0)
            if res is 0:
                cmd=xcat_install
                res=run_command(cmd,0)
                if res is 0:
                    if dryrun:
                        logger.debug("xCAT is installed [Dryrun]")
                    else:
                        logger.debug("xCAT is installed [Passed]")
                        os.environ["PATH"]=xcat_env+os.environ["PATH"]
                        cmd="lsxcatd -v"
                        run_command(cmd,0)
                    return 1
                else:
                    logger.error("xCAT is installed [Failed]")
            else:
                logger.error("chmod [Failed]")
        else:
            logger.error("wget [Failed]")
        
            
    def configure_vip(self, vip, nic, mask):
        """configure virtual ip"""
        global setup_process_msg
        global dryrun
        setup_process_msg="===> Configure virtual ip as alias ip stage <==="
        logger.info(setup_process_msg)
        cmd="ifconfig "+nic+" "+vip+" "+" netmask "+mask
        res=run_command(cmd,0)
        if res is 1:
            raise HaException(setup_process_msg)
        #add virtual ip into /etc/resolve.conf
        name_server="nameserver "+vip
        resolv_file="/etc/resolv.conf"
        res=self.find_line(resolv_file, vip)
        if res is 0:
            resolvefile=open(resolv_file,'a')
            print name_server
            if dryrun:
                logger.debug("Adding virtual ip "+vip+" into /etc/resolv.conf [Dryrun]")
                resolvefile.close()
                return
            logger.debug("Adding virtual ip "+vip+" into /etc/resolv.conf")
            resolvefile.write(name_server)

    def find_line(self, filename, keyword, exact_match=None):
        """find keyword from file"""
        key=keyword.strip()
        with open(filename,'r')as fp:
            list1 = fp.readlines()
            for line in list1:
                line=line.rstrip('\n')
                if exact_match:
                    # Need to match line exactly, not just substring
                    if key == line:
                        return 1
                else:
                    # Substring match
                    if re.search(r'\b%s\b' % key, line):
                        return 1
        return 0

    def save_original_host_and_ip(self):
        """"""
        global dryrun
        global etc_hosts
        logger.info("Save physical hostname and ip")
        physicalhost=self.get_hostname()
        physicalip=self.get_ip_from_hostname()
        physicalnet=physicalip+" "+physicalhost
        res=self.find_line(etc_hosts, physicalip)
        if res is 0:
            if dryrun:
                logger.info("Write "+physicalnet+" into "+etc_hosts+" [Dryrun]")
            else:
                hostfile=open(etc_hosts,'a')
                hostfile.write(physicalnet+"\n")
                hostfile.close()
        mnfile="/tmp/ha_mn"
        if not os.path.exists(mnfile):
            nfile = open(mnfile,'w')
            nfile.close()
        res=self.find_line(mnfile, physicalnet)
        if res is 0:
            if dryrun is 1:
                logger.info("Write "+physicalnet+" into "+mnfile+" [Dryrun]")
            else:
                mnfile=open(mnfile,'a')
                mnfile.write(physicalnet+"\n")
                mnfile.close() 
                                
    def change_hostname(self, host, ip):
        """change hostname"""
        global setup_process_msg
        global dryrun
        global etc_hosts
        setup_process_msg="===> Configure hostname stage <==="
        logger.info(setup_process_msg)
        ip_and_host=ip+" "+host
        res=self.find_line(etc_hosts, ip)
        if res is 0:
            # Check if host is a long hostname.
            if '.' in host:
                # Passed in hostname is a long format.
                # Add short name to etc/hosts also
                ip_and_host=ip_and_host+" "+host.split('.',1)[0]
            hostfile=open(etc_hosts,'a')
            if not dryrun:
                hostfile.write(ip_and_host+"\n")
            hostfile.close()
        cmd="hostname "+host.strip()
        res=run_command(cmd,0)

    def get_hostname(self):
        """get hostname"""
        mhost=socket.gethostname()
        return mhost

    def get_ip_from_hostname(self):
        """get ip"""
        hostname=self.get_hostname()
        ip=socket.gethostbyname(hostname)
        return ip

    def unconfigure_vip(self, vip, nic):
        """remove vip from nic and /etc/resolve.conf"""
        global setup_process_msg
        global dryrun
        setup_process_msg="===> Remove virtual IP stage <==="
        logger.info(setup_process_msg)
        cmd="ifconfig "+nic+" 0.0.0.0 0.0.0.0 &>/dev/null"
        res=run_command(cmd,0,1)
        cmd="ip addr show |grep "+vip+" &>/dev/null"
        res=run_command(cmd,0,1)
        if dryrun is 1:
            return # For dryrun just exit, there is no passed or failed
        if res is 0:
            logger.info("Remove virtual IP [Passed]")
        else:
            logger.errer("Remove virtual IP [Failed]")
            raise HaException(setup_process_msg)
           
    def check_service_status(self, service_name):
        """check service status"""
        global setup_process_msg
        global dryrun
        setup_process_msg="Check "+service_name+" service status"
        logger.info(setup_process_msg)
        if dryrun:
            # In dryrun mode always return success.
            #     Checking for service running is not destructive, but in dryrun mode
            #     some services would not be started, so the check
            #     will return failure which would prevent process from
            #     continuing
            return 0
        cmd="systemctl status "+service_name+" > /dev/null"
        status =os.system(cmd)
        return status

    def check_software_installed(self, package):
        """check if software is installed or not"""
        global setup_process_msg
        global dryrun
        setup_process_msg="Checking if "+package+" is installed ..."
        logger.info(setup_process_msg)
        res=0
        cmd="rpm -q "+package+" > /dev/null"
        res=os.system(cmd)
        if dryrun:
            # In dryrun mode always return success.
            #     Checking for software being installed is not destructive, 
            #     but in dryrun mode some services would not be installed,
            #     so the check will return failure which would prevent process from
            #     continuing
            return 0
        else:
            return res

    def finditem(self, n, server):
        """add item into policy table"""
        index=bytes(n)
        global dryrun
        return_code=0
        cmd="lsdef -t policy |grep 1."+index
        if dryrun:
            logger.debug(cmd+" [Dryrun]")
            return return_code
        else:
            logger.debug(cmd) 
        res=os.system(cmd)
        if res is not 0:
            cmd="chdef -t policy 1."+index+" name="+server+" rule=trusted"
            res=run_command(cmd,0)
            if res is 0:
                loginfo="'"+cmd+"' [Passed]"
                logger.debug(loginfo)
                return 0
            else:
                loginfo="'"+cmd+"' [Failed]"
                logger.error(loginfo)
                return 1
        else:
            n+=1
            finditem(bytes(n),server)

    def change_xcat_policy_attribute(self, nic, vip):
        """add hostname into policy table"""
        global setup_process_msg
        global dryrun
        setup_process_msg="===> Configure xCAT policy table stage <==="
        logger.info(setup_process_msg)
        filename="/etc/xcat/cert/server-cert.pem"
        word="Subject: CN="
        server=""
        return_code=0
        try:
            with open(filename, 'r') as f:
                for l in f.readlines():
                    if word in l:
                        linelist=l.split("=")
                        server=linelist[1].strip()
                        break
        except IOError:
            if dryrun:
                # In dryrun if xCAT is not installed, this .pem file would not exist.
                # Pretend it is there and return
                logger.debug("lsdef -t policy -i name [Dryrun]")
                return 0
            # Throw exception for not dryrun or in dryrun with xCAT installed
            raise HaExeption(setup_process_msg)

        if server:
            cmd="lsdef -t policy -i name|grep "+server
            if dryrun:
                logger.debug(cmd+" [Dryrun]")
                return return_code
            else:
                logger.debug(cmd)
            res=os.system(cmd)
            if res is not 0:
                res=self.finditem(3,server)
                if res is 0:
                    return 0
            else:
                loginfo=server+" exists in policy table."
                logger.debug(loginfo)
                return 0
        else:
            loginfo="Get server name "+server+" [Failed]" 
            logger.error(loginfo)
        return 1       

    def copy_files(self, sourceDir, targetDir):  
        """copy files"""
        global dryrun
        return_code=0
        if dryrun:
            logger.debug("Copy "+sourceDir+" to "+targetDir+" [Dryrun]")
            return return_code
        logger.debug("Copy "+sourceDir+" to "+targetDir) 
        if shutil.copytree(sourceDir,targetDir):
            return_code=1
        stat_info = os.stat(sourceDir)
        uid = stat_info.st_uid
        gid = stat_info.st_gid
        user = pwd.getpwuid(uid)[0]
        group = grp.getgrgid(gid)[0]
        cmd="chown -R "+user+":"+group+" "+targetDir
        if run_command(cmd, 0):
            return_code=1
        return return_code              

    def configure_shared_data(self, path, sharedfs, dbtype):
        """configure shared data directory"""
        global setup_process_msg
        global dryrun
        setup_process_msg="===> Configure shared data directory stage <==="
        logger.info(setup_process_msg)
        #check if there is xcat data in shared data directory
        if dbtype == 'postgresql' and sharedfs.__contains__("/var/lib/mysql"):
            sharedfs.remove("/var/lib/mysql")
        elif dbtype == 'mariadb' and sharedfs.__contains__("/var/lib/pgsql"):
            sharedfs.remove("/var/lib/pgsql")
            self.stop_service("mariadb")
        xcat_file_path=path+"/etc/xcat"
        self.stop_all_services(service_list, dbtype)
        if not os.path.exists(xcat_file_path):
            permision=oct(os.stat(path).st_mode)[-3:]           
            if permision == '755':
                i = 0
                while i < len(sharedfs):
                    xcat_file_path=path+sharedfs[i]
                    self.copy_files(sharedfs[i],xcat_file_path)
                    i += 1  
        #create symlink 
        for sharedfs_link in sharedfs:
            if dryrun:
                logger.info("Creating symlink ..."+sharedfs_link+ " [Dryrun]")
                continue
            logger.info("Creating symlink ..."+sharedfs_link)
            xcat_file_path=path+sharedfs_link
            if not os.path.islink(sharedfs_link):
                if os.path.exists(sharedfs_link):
                    if os.path.exists(sharedfs_link+".xcatbak"):
                        # Remove backup if already there
                        shutil.rmtree(sharedfs_link+".xcatbak")
                    shutil.move(sharedfs_link, sharedfs_link+".xcatbak")
                os.symlink(xcat_file_path, sharedfs_link)    
        #save original host and ip into /etc/xcat/ha_mn 
        etc_ha_mn="/etc/xcat/ha_mn"
        if not os.path.exists(etc_ha_mn):
            cmd="touch "+etc_ha_mn
            run_command(cmd,0)
        original_host=self.get_original_host()
        original_ip=self.get_original_ip()
        ip_and_host=original_ip+" "+original_host
        if dryrun:
            logger.debug("orignal ip and hostname:"+ip_and_host+" [Dryrun]")
        else:
            res=self.find_line(etc_ha_mn, ip_and_host)
            if res is 0:
                hamnfile=open(etc_ha_mn,'a')
                hamnfile.write(ip_and_host)
                hamnfile.close

    def modify_db_configure_file(self, dbtype, dbpath, physical_ip, vip):
        """"""
        global dryrun
        if dbtype == 'postgresql':
            dbfile=dbpath+pg_hba_conf
            if os.path.exists(dbfile):
                res=self.find_line(dbfile, physical_ip)
                if res is 0:
                    addline="host    all          all        "+physical_ip+"/32      md5\n"
                    if dryrun:
                        logger.debug('Added line "%s" to %s configuration file %s [Dryrun]' %(addline, dbtype, dbfile))
                    else:
                        dbfile1=open(dbfile,'a')
                        dbfile1.write(addline)
                        dbfile1.close()
                        logger.debug('Added line "%s" to %s configuration file %s' %(addline, dbtype, dbfile))
                res=self.find_line(dbfile, vip)
                if res is 0:
                    addline="host    all          all        "+vip+"/32      md5\n"
                    if dryrun:
                        logger.debug('Added line "%s" to %s configuration file %s [Dryrun]' %(addline, dbtype, dbfile))
                    else:
                        dbfile1=open(dbfile,'a')
                        dbfile1.write(addline)
                        dbfile1.close()
                        logger.debug('Added line "%s" to %s configuration file %s' %(addline, dbtype, dbfile))
            postgre_file=dbpath+postgresql_conf
            if os.path.exists(postgre_file):
                listen_addr_line=os.popen("cat "+postgre_file+"|grep ^listen_addresses").readline()
                listen_addr=listen_addr_line.split("'")[1]
                cmd="echo "+listen_addr+"|grep -w "+vip
                res=os.system(cmd)
                replace=0
                if res:
                    listen_addr=listen_addr+","+vip
                    replace=1
                cmd="echo "+listen_addr+"|grep -w "+physical_ip
                res=os.system(cmd)
                if res:
                    listen_addr=listen_addr+","+physical_ip
                    replace=1
                if replace:
                    cmd="sed -i '/^listen_addresses =/d' "+postgre_file
                    res=run_command(cmd,0)
                    cmd="echo \"listen_addresses = '%s'\" >> %s" % (listen_addr,postgre_file)
                    res=run_command(cmd,0)

    def unconfigure_shared_data(self, sharedfs, dbtype):
        """unconfigure shared data directory"""
        global setup_process_msg
        setup_process_msg="===> Unconfigure shared data directory stage <==="
        logger.info(setup_process_msg)

        if dbtype == 'postgresql' and sharedfs.__contains__("/var/lib/mysql"):
            sharedfs.remove("/var/lib/mysql")
        elif dbtype == 'mariadb' and sharedfs.__contains__("/var/lib/pgsql"):
            sharedfs.remove("/var/lib/pgsql")
        #1.check if there is xcat data in shared data directory
        #2.unlink data in shared data directory
        for sharedfs_link in sharedfs:
            if dryrun:
                logger.info("Removing symlink ..."+sharedfs_link+ " [Dryrun]")
                continue
            if os.path.islink(sharedfs_link):
                logger.info("Removing symlink ..."+sharedfs_link)
                os.unlink(sharedfs_link)
                logger.info("Restoring local directory ..."+sharedfs_link)
                if os.path.exists(sharedfs_link+".xcatbak") and not os.path.exists(sharedfs_link):
                    shutil.move(sharedfs_link+".xcatbak", sharedfs_link)

    def get_hostname_for_ip(self,ip):
        """get hostname for the passed in ip"""
        hostname=os.popen("getent hosts "+ip+" | awk -F ' ' '{print $2}' | awk -F'.' '{print $1}'| uniq").read()
        return hostname

    def get_hostname_original_ip(self):
        """original hostname"""
        host1=""
        ha_mn=""
        if os.path.exists("/tmp/ha_mn"):
            ha_mn="/tmp/ha_mn" 
        elif os.path.exists("/etc/xcat/ha_mn"):
            ha_mn="/etc/xcat/ha_mn"
        if ha_mn is not "":
            ips=os.popen("cat "+ha_mn+"|awk '{print $1}'").readlines()
            for ip in ips:
                nip=ip.strip()
                cmd='ifconfig|grep "inet '+nip+'  netmask" > /dev/null'
                res=os.system(cmd)
                if res is 0:
                    cmd="cat "+ha_mn+"|grep "+nip+"|head -1"
                    host1=os.popen(cmd).read().strip()
                    break
        return host1
    
    def get_original_ip(self):
        """"""
        ip=""
        ip_host=self.get_hostname_original_ip()
        if ip_host:
            ip=ip_host.split()[0]
        return ip

    def get_original_host(self):
        """"""
        host=""
        ip_host=self.get_hostname_original_ip()
        if ip_host:
            host=ip_host.split()[1]
        return host
        

    def clean_env(self, vip, nic, dbtype):

        """clean up env when exception happen"""
        restore_host_name=self.get_original_host()
        restore_host_ip=self.get_original_ip()
        if restore_host_name and restore_host_ip:
            self.change_hostname(restore_host_name,restore_host_ip)
        else:

            logger.warning("Unable to restore original hostname")
        self.unconfigure_vip(vip, nic)

    def clean_vip_hostname(self, vip, nic):
        """clean up VIP"""
        restore_host_name=self.get_original_host()
        restore_host_ip=self.get_original_ip()
        if restore_host_name and restore_host_ip:
            self.change_hostname(restore_host_name,restore_host_ip)
        else:
            logger.warning("Unable to restore original hostname")
        self.unconfigure_vip(vip, nic)

    def deactivate_management_node(self, nic, vip, dbtype):
        """deactivate management node"""
        global setup_process_msg
        setup_process_msg="########## Deactivate stage ##########"
        logger.info(setup_process_msg)
        self.disable_all_services(service_list, dbtype)
        self.stop_all_services(service_list, dbtype)
        self.clean_vip_hostname(vip, nic)
        logger.info("This machine is set to standby management node successfully...")

    def check_HA_directory(self, path):
        """check if there is HA directory exist or not"""
        if not os.path.exists(path):
            raise HaException(path+" does not exist")

    def source_xcat_profile(self):
        """source xcat profile"""
        xcat_env="/opt/xcat/bin:/opt/xcat/sbin:/opt/xcat/share/xcat/tools:"
        os.environ["PATH"]=xcat_env+os.environ["PATH"]

    def activate_management_node(self, nic, vip, dbtype, path, mask):
        """activate management node"""
        try:
            global setup_process_msg
            setup_process_msg="########## Activate stage ##########"
            logger.info(setup_process_msg)
            self.check_HA_directory(path)
            self.vip_check(vip)
            self.configure_vip(vip, nic, mask)
            restore_host_name=self.get_hostname_for_ip(vip)
            if restore_host_name:
                self.change_hostname(restore_host_name,vip)
            else:
                logger.error("Can not find the hostname to set")
            self.check_xcat_exist_in_shared_data(path)
            self.start_all_services(service_list, dbtype, restore_host_name)
            logger.info("This machine is set to primary management node successfully...")
        except:
            raise HaException(setup_process_msg)
 
    def xcatha_setup_mn(self, args):
        """setup_mn process"""
        global dryrun
        try:
            self.check_HA_directory(args.path) 
            self.vip_check(args.virtual_ip)
            if self.check_xcat_exist_in_shared_data(args.path):
                self.check_shared_data_db_type(args.dbtype,args.path)
            self.configure_vip(args.virtual_ip,args.nic,args.netmask)
            self.save_original_host_and_ip()
            self.change_hostname(args.host_name,args.virtual_ip)
            if self.check_service_status("xcatd") is not 0:
                self.install_xcat(xcat_url)
            self.check_database_type(args.dbtype,args.virtual_ip,args.nic,args.path)
            self.configure_shared_data(args.path, shared_fs, args.dbtype)
            dbservice="postgresql"
            if args.dbtype == 'mariadb':
                dbservice="mariadb"
            if args.dbtype == 'postgresql' or args.dbtype == 'mariadb':
                res=self.restart_service(dbservice)
                if res:
                    logger.error("%s service did not start [Failed]" %dbservice) 
            if self.check_service_status("xcatd") is not 0:
                res=self.restart_service("xcatd")
                if res:
                    logger.error("xCAT service did not start [Failed]")
                    raise HaException(setup_process_msg)
            if dryrun:
                logger.debug("xCAT service has started [Dryrun]")
            else:
                logger.debug("xCAT service has started [Passed]")
            self.source_xcat_profile()
            self.change_xcat_policy_attribute(args.nic, args.virtual_ip)
            self.deactivate_management_node(args.nic, args.virtual_ip, args.dbtype) 
        except:
            raise HaException(setup_process_msg)

def parse_arguments():
    """parse input arguments"""
    parser = argparse.ArgumentParser(description="Setup/Activate/Deactivate shared data based xCAT HA MN node")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-s', '--setup', help="setup node to be xCAT MN", action='store_true')
    group.add_argument('-a', '--activate', help="activate node to be xCAT MN", action='store_true')
    group.add_argument('-d', '--deactivate', help="deactivate node to be xCAT MN", action='store_true')
    parser.add_argument('-p', dest="path", help="shared data directory path")
    parser.add_argument('-v', dest="virtual_ip", help="virtual IP")
    parser.add_argument('-i', dest="nic", help="virtual IP network interface")
    parser.add_argument('-n', dest="host_name", help="virtual IP hostname")
    parser.add_argument('-m', dest="netmask", help="virtual IP network mask")
    parser.add_argument('-t', dest="dbtype", choices=['postgresql', 'sqlite', 'mariadb'], help="database type")
    parser.add_argument('--dryrun', action="store_true", help="display steps without execution")
    args = parser.parse_args()
    return args

def get_user_input(ignore_dryrun=None):
    retry=5
    return_code=0
    while True :
        confirm=raw_input()
        if confirm in ["Y", "Yes"]:
            break
        elif confirm in ["N", "No"]:
            logger.info("Do nothing, exiting...")
            return_code=2
            break
        elif confirm in ["D", "Dryrun"]:
            return_code=1
            break
        else:
            if ignore_dryrun:
                print "Continue? [[Y]es/[N]o]:"
            else:
                print "Continue? [[Y]es/[N]o/[D]ryrun]:"
            retry=retry-1
        if retry < 1:
            return_code=1
            break
    return return_code

def get_db_type_from_user():
    retry=5
    confirm=""
    while True :
        confirm=raw_input()
        if confirm not in ["postgresql", "mariadb", "sqlite"]:
            print "Enter DB type [postgresql/mariadb/sqlite]"
            retry=retry-1
        else:
            break
        if retry < 1:
            break
    return confirm

def interactive_deactivate(obj,dbtype):
    global dryrun
    logger.info("[xCAT] Shutting down services:")
    if dbtype == 'mariadb' and 'postgresql' in service_list:
        service_list.remove('postgresql')
    elif dbtype == 'postgresql' and 'mariadb' in service_list:
        service_list.remove('mariadb')
    elif dbtype == 'sqlite':
        if 'mariadb' in service_list:
            service_list.remove('mariadb')
        if 'postgresql' in service_list:
            service_list.remove('postgresql')
    for service in reversed(service_list):
        print "... "+service
    print user_input_ynd
    return_code=get_user_input() 
    if return_code is 2:
        return 1
    elif return_code is 1:
        dryrun=1
    elif return_code is 0:
        dryrun=0
    obj.stop_all_services(service_list, dbtype)    
    print "[xCAT] Disabling services from starting on reboot:"
    for service in reversed(service_list):
        print "... "+service
    print user_input_ynd
    return_code=get_user_input()
    if return_code is 2:
        return 1
    elif return_code is 1:
        dryrun=1
    elif return_code is 0:
        dryrun=0
    obj.disable_all_services(service_list, dbtype)

def interactive_activate(obj,virtual_ip,dbtype):
    global dryrun
    print "[Admin] Verify VIP "+virtual_ip+" is configured on this node"
    print user_input_yn
    return_code=get_user_input(1)
    if return_code is 2:
        return 1
    print "[Admin] Verify that the following is configured to be saved in shared storage and accessible from this node:"

    if dbtype == 'mariadb' and '/var/lib/pgsql' in shared_fs:
        shared_fs.remove('/var/lib/pgsql')
    if dbtype == 'sqlite' and '/var/lib/pgsql' in shared_fs:
        shared_fs.remove('/var/lib/pgsql')
    if dbtype == 'postgresql' and '/var/lib/mysql' in shared_fs:
        shared_fs.remove('/var/lib/mysql')
    for shfs in shared_fs:
        print "... "+shfs
    print user_input_yn
    return_code=get_user_input(1)
    if return_code is 2:
        return 1
    print "[xCAT] Starting up services:"
    if dbtype == 'mariadb' and 'postgresql' in service_list:
        service_list.remove('postgresql')
    elif dbtype == 'postgresql' and 'mariadb' in service_list:
        service_list.remove('mariadb')
    elif dbtype == 'sqlite':
        if 'mariadb' in service_list:
            service_list.remove('mariadb')
        if 'postgresql' in service_list:
            service_list.remove('postgresql')
    for service in service_list:
        print "... "+service
    print user_input_ynd
    return_code=get_user_input()
    if return_code is 2:
        return 1
    elif return_code is 1:
        dryrun=1
    elif return_code is 0:
        dryrun=0
    restore_host_name=obj.get_hostname_for_ip(virtual_ip)
    obj.start_all_services(service_list, dbtype, restore_host_name)
     
def main():
    global dryrun
    args=parse_arguments()
    obj=xcat_ha_utils()
    interactive=False
    if args.dryrun:
        dryrun = 1
    try:
        if args.activate:
            if args.nic and args.virtual_ip and args.path:
                logger.info("Activating this node as xCAT primary MN")
                if not args.netmask:
                    args.netmask="255.255.255.0"
                dbtype=obj.current_database_type("")
                obj.activate_management_node(args.nic, args.virtual_ip, dbtype, args.path, args.netmask)
            else:
                if not args.virtual_ip:
                     args.virtual_ip = obj.get_ip_from_hostname()
                if not args.dbtype:
                     # Default to postgresql
                     args.dbtype = "postgresql"
                interactive=True
                interactive_activate(obj,args.virtual_ip,args.dbtype) 
                
        if args.deactivate:
            dbtype=obj.current_database_type("")
            if args.nic and args.virtual_ip:
                logger.info("Deactivating this node as xCAT standby MN")
                obj.deactivate_management_node(args.nic, args.virtual_ip, dbtype)
            else:
                interactive=True
                interactive_deactivate(obj,dbtype) 
            logger.info("This machine is set to standby management node successfully...") 
        if args.setup:
            if not args.netmask:
                args.netmask="255.255.255.0"
            if not args.dbtype:
                args.dbtype="postgresql"
            if not args.host_name:
                logger.error("Option -n is required for xCAT HA setup")
                return 1
            if not args.path:
                logger.error("Option -p is required for xCAT MN setup")
                return 1
            logger.info("Setup this node as xCAT HA standby MN")
            res=obj.xcatha_setup_mn(args)
            if res:
                obj.clean_env(args.virtual_ip, args.nic, args.dbtype)
                return 1
    except HaException,e:
        logger.error(e.message)
        logger.error("Error encountered, starting to clean up the environment")
        if interactive is False:
            obj.clean_env(args.virtual_ip, args.nic, args.dbtype)
        return 1

if __name__ == "__main__":
    main()
