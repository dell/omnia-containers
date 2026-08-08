import subprocess
import logging
import os
import glob
import pathmod
import tempfile
# Written Modules
from utils import cmd

class Installer:
    def __init__(self, pkg_man, cname, mname):
        self.pkg_man = pkg_man
        self.cname = cname
        self.mname = mname

        # Create temporary directory for logs, cache, etc. for package manager
        os.makedirs(os.path.join(mname, "tmp"), exist_ok=True)
        self.tdir = tempfile.mkdtemp(prefix="image-build-")
        logging.info(f'Installer: Temporary directory for {self.pkg_man} created at {self.tdir}')

        if pkg_man == "dnf":
            # DNF complains if the log directory is not present
            os.makedirs(os.path.join(self.tdir, "dnf/log"))

    def install_repos(self, repos, repo_dest, proxy):
        # check if there are repos passed for install
        if len(repos) == 0:
            logging.info("REPOS: no repos passed to install\n")
            return

        logging.info(f"REPOS: Installing these repos to {self.cname}")
        for r in repos:
            logging.info(r['alias'] + ': ' + r['url'])
            if self.pkg_man == "zypper":
                args = []
                args.append("-D")
                args.append(os.path.join(self.mname, pathmod.sep_strip(repo_dest)))
                args.append("addrepo")
                args.append("-f")
                args.append("-p")
                if 'priority' in r:
                    args.append(r['priority'])
                else:
                    args.append('99')
                args.append(r['url'])
                args.append(r['alias'])

                rc = cmd([self.pkg_man] + args)
                if rc != 0:
                    raise Exception("Failed to install repo", r['alias'], r['url'])

            elif self.pkg_man == "dnf":
                # Write .repo file directly with priority support
                # This is more reliable than dnf config-manager + glob on DNF5
                repo_dir = os.path.join(self.mname, pathmod.sep_strip(repo_dest))
                os.makedirs(repo_dir, exist_ok=True)

                repo_id = r['alias']
                repo_file_path = os.path.join(repo_dir, repo_id + '.repo')
                priority_val = r.get('priority', '99')

                repo_content = f"[{repo_id}]\n"
                repo_content += f"name=added from: {r['url']}\n"
                repo_content += f"baseurl={r['url']}\n"
                repo_content += f"enabled=1\n"
                repo_content += f"gpgcheck=0\n"
                repo_content += f"sslverify=0\n"
                repo_content += f"priority={priority_val}\n"
                if proxy != "":
                    repo_content += f"proxy={proxy}\n"

                with open(repo_file_path, 'w') as rf:
                    rf.write(repo_content)
                logging.info(f"Created repo file: {repo_file_path} (priority={priority_val})")

            if "gpg" in r:
                # Using rpm apparently works for both Yum- and Zypper-based distros.
                args = []
                if proxy != "":
                    arg_env = os.environ.copy()
                    arg_env['https_proxy'] = proxy
                args.append("--root="+self.mname)
                args.append("--import")
                args.append(r["gpg"])

                rc = cmd(["rpm"] + args)
                if rc != 0:
                    raise Exception("Failed to install gpg key for", r['alias'], "at URL", r['gpg'])

    def install_base_packages(self, packages, registry_loc, proxy):
        # check if there are packages to install
        if len(packages) == 0:
            logging.warn("PACKAGES: no packages passed to install\n")
            return

        logging.info(f"PACKAGES: Installing these packages to {self.cname}")
        logging.info("\n".join(packages))

        args = []
        if self.pkg_man == "zypper":
            args.append("-n")
            args.append("-D")
            args.append(os.path.join(self.mname, pathmod.sep_strip(registry_loc)))
            args.append("-C")
            args.append(self.tdir)
            args.append("--no-gpg-checks")
            args.append("--installroot")
            args.append(self.mname)
            args.append("install")
            args.append("-l")
            args.extend(packages)
        elif self.pkg_man == "dnf":
            args.append("--setopt=reposdir="+os.path.join(self.mname, pathmod.sep_strip(registry_loc)))
            args.append("--setopt=logdir="+os.path.join(self.tdir, self.pkg_man, "log"))
            args.append("--setopt=cachedir="+os.path.join(self.tdir, self.pkg_man, "cache"))
            if proxy != "":
                args.append("--setopt=proxy="+proxy)
            args.append("install")
            args.append("-y")
            args.append("--nogpgcheck")
            args.append("--installroot")
            args.append(self.mname)
            args.extend(packages)

        rc = cmd([self.pkg_man] + args)
        if rc == 104:
            raise Exception("Installing base packages failed")

        if rc == 107:
            logging.warn("one or more RPM postscripts failed to run")

    def remove_base_packages(self, remove_packages):
        # check if there are packages to remove
        if len(remove_packages) == 0:
            logging.warn("REMOVE PACKAGES: no package passed to remove\n")
            return

        logging.info(f"REMOVE PACKAGES: removing these packages from container {self.cname}")
        logging.info("\n".join(remove_packages))
        for p in remove_packages:
            args = [self.cname, '--', 'rpm', '-e', '--nodeps', p]
            cmd(["buildah","run"] + args)

    def install_base_package_groups(self, package_groups, registry_loc, proxy):
        # check if there are packages groups to install
        if len(package_groups) == 0:
            logging.warn("PACKAGE GROUPS: no package groups passed to install\n")
            return

        logging.info(f"PACKAGE GROUPS: Installing these package groups to {self.cname}")
        logging.info("\n".join(package_groups))
        args = []

        if self.pkg_man == "zypper":
            logging.warn("zypper does not support package groups")
        elif self.pkg_man == "dnf":
            args.append("--setopt=reposdir="+os.path.join(self.mname, pathmod.sep_strip(registry_loc)))
            args.append("--setopt=logdir="+os.path.join(self.tdir, self.pkg_man, "log"))
            args.append("--setopt=cachedir="+os.path.join(self.tdir, self.pkg_man, "cache"))
            if proxy != "":
                args.append("--setopt=proxy="+proxy)
            args.append("groupinstall")
            args.append("-y")
            args.append("--nogpgcheck")
            args.append("--installroot")
            args.append(self.mname)
            args.extend(package_groups)

        rc = cmd([self.pkg_man] + args)
        if rc == 104:
            raise Exception("Installing base packages failed")

    def install_base_modules(self, modules, registry_loc, proxy):
        # check if there are modules groups to install
        if len(modules) == 0:
            logging.warn("PACKAGE MODULES: no modules passed to install\n")
            return
        logging.info(f"MODULES: Running these module commands for {self.cname}")
        for mod_cmd, mod_list in modules.items():
            logging.info(mod_cmd + ": " + " ".join(mod_list))
        for mod_cmd, mod_list in modules.items():
            args = []
            if self.pkg_man == "zypper":
                logging.warn("zypper does not support package groups")
                return
            elif self.pkg_man == "dnf":
                args.append("--setopt=reposdir="+os.path.join(self.mname, pathmod.sep_strip(registry_loc)))
                args.append("--setopt=logdir="+os.path.join(self.tdir, self.pkg_man, "log"))
                args.append("--setopt=cachedir="+os.path.join(self.tdir, self.pkg_man, "cache"))
                if proxy != "":
                    args.append("--setopt=proxy="+proxy)
                args.append("module")
                args.append(mod_cmd)
                args.append("-y")
                args.append("--nogpgcheck")
                args.append("--installroot")
                args.append(self.mname)
                args.extend(mod_list)
            rc = cmd([self.pkg_man] + args)
            if rc != 0:
                raise Exception("Failed to run module cmd", mod_cmd, ' '.join(mod_list))
            

    def install_base_commands(self, commands):
        # check if there are commands to install
        if len(commands) == 0:
            logging.warn("COMMANDS: no commands passed to run\n")
            return

        logging.info(f"COMMANDS: running these commands in {self.cname}")
        for c in commands:
            logging.info(c['cmd'])
            build_cmd = ["buildah","run"]
            if 'buildah_extra_args' in c:
              build_cmd.extend(c['buildah_extra_args'])
            args = [self.cname, '--', 'bash', '-c', c['cmd']]
            if 'loglevel' in c:
                if c['loglevel'].upper() == "INFO":
                    loglevel = logging.info
                elif c['loglevel'].upper() == "WARN":
                    loglevel = logging.warn
                else:
                    loglevel = logging.error
            else:
                loglevel = logging.error
            out = cmd(build_cmd + args, stderr_handler=loglevel)

    def install_base_copyfiles(self, copyfiles):
        if len(copyfiles) == 0:
            logging.warn("COPYFILES: no files to copy\n")
            return
        logging.info(f"COPYFILES: copying these files to {self.cname}")
        for f in copyfiles:
            args = []
            if 'opts' in f:
                for o in f['opts']:
                    args.extend(o.split())
            logging.info(f['src'] + ' -> ' + f['dest'])
            args +=  [ self.cname, f['src'], f['dest'] ]
            out=cmd(["buildah","copy"] + args)
