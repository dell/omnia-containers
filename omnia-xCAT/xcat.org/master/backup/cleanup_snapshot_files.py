#!/usr/bin/python 
# Run this by adding to the crontab
# - execute every day at 1:00 AM, deleting files older than 180 days
#
# 1 00 * * * xcat /var/www/xcat.org/backup/cleanup_snapshot_files.sh
#

import sys, os
import fnmatch
import time

DAYS_OLD=180

baseDirectory = os.path.dirname(os.path.realpath(__file__))
fileDirectory = baseDirectory.replace("backup", "files")

now = time.time()
cutoff = now - (int(DAYS_OLD) * 86400)

# Get all the bz2 files 
for root,dirnames,filenames in os.walk(fileDirectory): 
    if not filenames:
        continue

    if len(filenames) > 2: 
        # We want to leave around some files, so only clean up if 
        # there are more than 2 files in the directory

        symlinks = [] 
        for filename in fnmatch.filter(filenames, "*snap.tar.bz2"):
            fullpath = os.path.join(root,filename)
            # look for the symlinks
            if os.path.islink(fullpath):
                real_path = os.readlink(fullpath)
                real_full_path = os.path.join(root, os.readlink(fullpath))
                # find the real file name and set them aside 
                symlinks.append(real_full_path)
  
        # Repeat the loop and actually remove the files older than DAYS_OLD 
        for filename in fnmatch.filter(filenames, "*.bz2"):
            fullpath = os.path.join(root,filename)
            if os.path.islink(fullpath):
                # do not remove symlinks
                continue
            if fullpath in symlinks:
                # do not remove the files pointed to by symlinks
                continue 
         
            # check the time of the file 
            t = os.stat(fullpath)
            c = t.st_mtime

            # print "DEBUG - File %s, c=%d,cutoff=%d" %(os.path.basename(fullpath), c, cutoff)
            if c < cutoff: 
                os.remove(fullpath)
