nsenter -a -t $(cat /tmp/topotests/isis_srv6_topo1.test_isis_srv6_topo1/r1.pid) ip link set eth1 down
nsenter -a -t $(cat /tmp/topotests/isis_srv6_topo1.test_isis_srv6_topo1/r1.pid) ip link set eth1 up
