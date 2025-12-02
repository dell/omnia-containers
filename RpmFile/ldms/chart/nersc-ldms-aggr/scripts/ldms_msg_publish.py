#!/usr/bin/env python3
import sys
sys.path.append('/opt/ovis-ldms/lib/python3.6/site-packages')
from ovis_ldms import ldms
ldms.init(16*1024*1024)
x = ldms.Xprt("sock", "munge")
x.connect("localhost", "6002")
x.msg_publish("nersc", "This is a test")
