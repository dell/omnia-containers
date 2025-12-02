#!/bin/bash
/opt/ovis-ldms/sbin/ldms_ls -x sock -h localhost -p 6002  -l -a ovis -A conf=$(pwd)/ldmsauth.conf
