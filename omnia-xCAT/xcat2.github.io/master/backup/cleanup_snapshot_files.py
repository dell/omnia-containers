#!/usr/bin/python 
#
# This script could be executed directly on xcat.org
# But it is intended to be executed from c910 login node
# by backup/runcleanup (in xcat2/xcat2.github.io repo)
#
# Usage: cleanup_snapshot_files.py [--dryrun] [--debug]

import sys, os
import fnmatch
import time

DAYS_OLD=180
REMOVED=0
DEBUG=0
DRYRUN=0

if (len(sys.argv)) > 1:
    # Some args were passed
    if "--dryrun" in sys.argv:
        print "--dryrun passed"
        DRYRUN=1
    if "--debug" in sys.argv:
        print "--debug passed"
        DEBUG=1

top = "/var/www/xcat.org"
fileDirectoryList = [top + "/files/xcat/xcat-dep",top + "/files/xcat/xcat-core"]

now = time.time()
cutoff = now - (int(DAYS_OLD) * 86400)

#For each file in the list
for fileDirectory in fileDirectoryList:
    # Get all the bz files 
    for root,dirnames,filenames in os.walk(fileDirectory): 
        print "Processing directory %s with %s files" %(root, len(filenames)) 
        if not filenames:
            continue

        if len(filenames) > 2: 
            # We want to leave around some files, so only clean up if 
            # there are more than 2 files in the directory

            symlinks = [] 
            fresh_time = 0
            fresh_file = "mg"
            for filename in fnmatch.filter(filenames, "*snap.tar.bz*"):
                fullpath = os.path.join(root,filename)
                # look for the symlinks
                if os.path.islink(fullpath):
                    real_path = os.readlink(fullpath)
                    real_full_path = os.path.join(root, os.readlink(fullpath))
                    # find the real file name and set them aside 
                    symlinks.append(real_full_path)
  
            # Repeat the loop and look for files with freshest date
            # We want to not remove such file as it might be the last one in dir
            # even if older than the DAYS_OLD
            for filename in fnmatch.filter(filenames, "*snap.tar.bz*"):
                fullpath = os.path.join(root,filename)
                t = os.stat(fullpath)
                c = t.st_mtime
                if fresh_time < c:
                    #This file has later timestamp
                    fresh_time = c
                    fresh_file = fullpath
                    # print "    FRESHEST - File %-50s, f=%d" %(filename, fresh_time)


            # Repeat the loop and actually remove the files older than DAYS_OLD 
            for filename in fnmatch.filter(filenames, "*snap.tar.bz*"):
                fullpath = os.path.join(root,filename)
                if os.path.islink(fullpath):
                    # do not remove symlinks
                    if DEBUG:
                        print "    ---> KEEP, SYMLINK %s" %(fullpath)
                    continue
                if fullpath in symlinks:
                    # do not remove the files pointed to by symlinks
                    if DEBUG:
                        print "    ---> KEEP, SYMLINK SOURCE %s" %(fullpath)
                    continue 
         
                # check the time of the file 
                t = os.stat(fullpath)
                c = t.st_mtime

                # print "DEBUG - File %s, c=%d,cutoff=%d" %(os.path.basename(fullpath), c, cutoff)
                if c < cutoff: 
                    # Timestamp on the file is older than the cutoff
                    if fullpath == fresh_file:
                        # Do not remove the last file in directory. It might be older than cutoff
                        # but it is the last snapshot of its kind
                        if DEBUG:
                            print "    ---> KEEP, LAST OF ITS KIND %s" %(filename)
                    else:
                        REMOVED += 1
                        if DRYRUN:
                            print "    ---> DRYRUN REMOVE %s" %(filename)
                        else:
                            os.remove(fullpath)
                            print "    ---> REMOVED %s" %(filename)
                else:
                    if DEBUG:
                        print "    ---> KEEP, NOT OLD ENOUGH %s" %(filename)

print "Removed %d files" %(REMOVED)
