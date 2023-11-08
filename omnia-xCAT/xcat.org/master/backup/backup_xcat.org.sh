#!/bin/sh
# This script is copied over to xcat.org and 
# executed to tar up the directories in the list below

SAVE_DIRECTORIES="./css ./images ./*.html ./files ./*.py"

DATE=`date +%Y%m%d`
FILENAME="${DATE}-xcat.org-backup.tar.gz"

TARGET_TOPDIR=/var/www/xcat.org

# -------------- starting the backup process --------------

echo "Creating backup file ${FILENAME}"

cd ${TARGET_TOPDIR}
tar -czvf $FILENAME ${SAVE_DIRECTORIES}

# move the backup to the home directory of the user
mv ${TARGET_TOPDIR}/${FILENAME} ~/

# list out for debug 
ls -ltr ~/${FILENAME}

