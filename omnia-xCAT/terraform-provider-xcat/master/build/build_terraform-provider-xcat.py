#!/usr/bin/env python

import jenkins
import re
import time
import getpass
from optparse import OptionParser

support_archs = ('x86_64', 'ppc64le')
build_prefix = '/xcatbuild/'
package_tar = "terraform-provider-xcat"

class BuildMyXCAT(object):

    def __init__(self, host, username, password, arch):

        self.host = host
        self.userid = username
        self.server = jenkins.Jenkins('http://%s:8080' % host, username=username, password=password)
        self.origin_job_prefix = 'terraform-provider-xcat'
	self.arch = arch

    def build_with_new_repo(self, branch, repo):

        origin_job_name = '%s_%s' % (self.origin_job_prefix, self.arch)
        job_name = '%s_%s_%s_%s_dev' % (repo.replace('/','-'), self.arch, branch.replace('/','-'), time.strftime("%Y%m%d%H%M%S", time.localtime()))
        build_dir = '%s%s/%s' % (build_prefix, self.userid, job_name)

        try:
            if (self.server.job_exists(job_name)):
                print('Error: project %s exists' % job_name)
                return 1

            job_config = re.sub(re.compile(r"<url.*?</url>", re.S), '<url>https://github.com/%s.git</url>' % repo, self._get_origin_config(origin_job_name)) 
            job_config = re.sub(re.compile(r"rest_build_dir=&quot;&quot;", re.S), 'rest_build_dir=%s' % build_dir, job_config)
            self.server.create_job(job_name, job_config)
            print('Created new Jenkins job %s' % job_name)
            next_build_number = self.server.get_job_info(job_name)['nextBuildNumber']
            print('Jenkins build number is %s' % next_build_number)
            self.server.build_job(job_name, {'BRANCH': branch})
            print('Start to build branch %s ...' % branch)

            if self._process_build_result(job_name, next_build_number, build_dir):
                return 1

        except (jenkins.JenkinsException, jenkins.NotFoundException, jenkins.EmptyResponseException, jenkins.BadHTTPException, jenkins.TimeoutException) as e:
            print e.message.split('\n')[0]
            return 1

    def build_with_create(self, branch):

        origin_job_name = '%s_%s' % (self.origin_job_prefix, self.arch)
	print (origin_job_name)
        new_job_name = '%s_%s_%s_dev' % (origin_job_name, branch.replace('/','-'), time.strftime("%Y%m%d%H%M%S", time.localtime()))
        build_dir = '%s%s/%s' % (build_prefix, self.userid, new_job_name)

        try:
            if (self.server.job_exists(new_job_name)):
                print('Error: project %s exists' % new_job_name)
                return 1

            job_config = re.sub(re.compile(r"rest_build_dir=&quot;&quot;", re.S), 'rest_build_dir=%s' % build_dir, self._get_origin_config(origin_job_name))
            self.server.create_job(new_job_name, job_config)
            print('Created new Jenkins job %s' % new_job_name)
            next_build_number = self.server.get_job_info(new_job_name)['nextBuildNumber']
            print('Jenkins build number is %s' % next_build_number)
            self.server.build_job(new_job_name, {'BRANCH': branch}) 
            print('Start to build branch %s ...' % branch)

            if self._process_build_result(new_job_name, next_build_number, build_dir):
                return 1

        except (jenkins.JenkinsException, jenkins.NotFoundException, jenkins.EmptyResponseException, jenkins.BadHTTPException, jenkins.TimeoutException) as e:
            print e.message.split('\n')[0]
            return 1

    def _process_build_result(self, job, number, build_dir=None):

        result = 'Unknown'

        start_time = time.time()
        while (time.time() - start_time < 1200):
            time.sleep(30)
            build_info = self.server.get_build_info(job, number)
            if 'result' in build_info and build_info['result']:
                result = build_info['result']
                break

        if result == 'Unknown':
            print ('Build have not ended, please check result on Jenkins')
            return 1

        print('Build result is %s' % result)
        if not build_dir:
            print('You could get more information on Jenkins')
            return

        if result == 'SUCCESS':
            print('The build xcat-core is available at "http://%s%s/%s"' % (self.host, build_dir, package_tar))
        else:
            print('The build log is available at "http://%s%s/build.log"' % (self.host, build_dir))

        #self.server.wipeout_job_workspace(job)
        self.server.delete_job(job)
        print('Cleaned Jenkins build environment')

    def _get_origin_config(self, job_name):

        origin_config = self.server.get_job_config(job_name) 
        return origin_config

if __name__ == '__main__':
    usage = "usage: %prog -H <host> -u <user> -p <pass> [-b <branch>] [--arch <arch>] [-r <repo>]"
    parser = OptionParser(usage=usage)
    parser.add_option("-H", "--host", dest="host", help="Jenkins server IP address")
    parser.add_option("-u", "--user", dest="user", help="Jenkins username")
    parser.add_option("-p", "--pass", dest="passwd", help="Jenkins password")
    parser.add_option("-b", "--branch", dest="branch", default="master", help="The branch want to build, default is 'master'")
    parser.add_option("-r", "--repo", dest="repo", help="Personal github repo want to be built, support format: xcat2/terraform-provider-xcat, default to build terraform-provider-xcat")
    parser.add_option("--arch", dest="arch", help="The ARCH want to build for, supported arch: x86_64, ppc64le")
    (options, args) = parser.parse_args()

    if not options.host or not options.user or not options.passwd:
        parser.error("options -H/-u/-p must be defined") 

    if options.arch not in support_archs:
        parser.error("Only '%s' supported" % ','.join(support_archs))

    build_job = BuildMyXCAT(options.host, options.user, options.passwd, options.arch)
    if options.repo:
        exit ( build_job.build_with_new_repo(options.branch, options.repo) )
    else:
        exit ( build_job.build_with_create(options.branch) )


    
