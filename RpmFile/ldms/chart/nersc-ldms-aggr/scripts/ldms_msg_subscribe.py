#!/usr/bin/env python3
import time
import sys
sys.path.append('/opt/ovis-ldms/lib/python3.6/site-packages')
from ovis_ldms import ldms

mc = ldms.MsgClient(".*", True)

x = ldms.Xprt("sock", "munge")
x.connect("localhost", 6002)
x.msg_subscribe("nersc", True)

while True:
    d = mc.get_data()
    while d is None:
        time.sleep(0.25)
        d = mc.get_data()
    ts = time.strftime("%F %T") + f".{int( (time.time()%1)*1e6 ):06}"
    print(ts, d.name, ":", d.data)
