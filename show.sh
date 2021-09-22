PID=$(cat /tmp/topotests/isis_srv6_topo1.test_isis_srv6_topo1/r1.pid)
nsenter -t $PID -a vtysh -c 'sh isis data deta'
